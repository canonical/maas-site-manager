from collections.abc import AsyncGenerator
from contextlib import aclosing, asynccontextmanager
from logging import Logger
from mimetypes import guess_type
import os
from pathlib import Path
import re
from typing import Any
import urllib.parse

import anyio
from baize.asgi.responses import FileResponse as BaizeFileResponse
from bs4 import BeautifulSoup as bs
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    Response as FastApiResponse,
)
from prometheus_client import REGISTRY, CollectorRegistry
from sqlalchemy.ext.asyncio import AsyncConnection
import uvicorn
from uvicorn.server import logger

import msm
from msm import __version__
from msm.api.exceptions.middleware import (
    ExceptionMiddleware,
    request_validation_error_handler,
)
from msm.api.prometheus import instrument_prometheus
from msm.api.site.handlers import ROUTERS as SITE_API_ROUTERS
from msm.api.user.handlers import ROUTERS as USER_API_ROUTERS
from msm.api.utils import create_subapp
from msm.db import Database, check_server_version
from msm.metrics import collect_stats
from msm.middleware import DatabaseMetricsMiddleware, TransactionMiddleware
from msm.service import ConfigService, ServiceCollection, SettingsService
from msm.settings import Settings


def run() -> None:
    """Run the API application."""
    settings = Settings()
    config: dict[str, Any]
    if settings.dev_mode:
        config = {
            "host": "0.0.0.0",
            "port": settings.api_port,
            "reload": True,
            "reload_dirs": [str(Path(msm.__file__).parent)],
        }
    else:
        config = {"uds": settings.api_socket}
    uvicorn.run(
        "msm.api:create_app",
        factory=True,
        loop="uvloop",
        **config,
    )


def create_app(
    db: Database | None = None,
    transaction_middleware_class: type = TransactionMiddleware,
    prometheus_registry: CollectorRegistry = REGISTRY,
) -> FastAPI:
    """Create the API (FastAPI) ASGI application."""
    settings = Settings()
    if not db:
        db = Database(settings.db_dsn())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        _log_settings(logger, settings)

        async with aclosing(db):
            await db.execute_in_transaction(check_server_version)
            await db.ensure_schema()
            await db.execute_in_transaction(ensure_db_entries)

            # start background tasks
            async with anyio.create_task_group() as tg:
                tg.start_soon(collect_stats, db, logger)
                yield
                # stop all tasks
                tg.cancel_scope.cancel()

    base_path = os.environ.get("MSM_BASE_PATH", "")
    root_path = urllib.parse.urlparse(base_path).path

    app = FastAPI(
        title="MAAS Site Manager",
        name="msm",
        version=__version__,
        lifespan=lifespan,
        root_path=root_path,
    )

    @app.get("/")
    @app.get("/ui", response_class=RedirectResponse, status_code=301)
    async def redirect(request: Request) -> RedirectResponse:
        return RedirectResponse(
            url="/".join([app.root_path.strip("/"), "ui/"]),
            headers=request.headers,
        )

    @app.get("/version")
    def get_version() -> dict[str, str]:
        return {"version": app.version}

    @app.get("/ui/{path_name:path}", response_model=None)
    def get_static(
        request: Request, path_name: str
    ) -> FastApiBaizeFileResponse | HTMLResponse:
        full_path = Path(settings.static_dir) / path_name
        if full_path.is_file() and path_name != "index.html":
            return FastApiBaizeFileResponse(full_path)
        else:
            return _serve_index_html(settings.static_dir, app.root_path)

    if settings.dev_mode:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    user_app = create_subapp("User API", "api", USER_API_ROUTERS)
    site_app = create_subapp("Site API", "site", SITE_API_ROUTERS)

    instrument_prometheus(prometheus_registry, app, user_app, site_app)

    for a in (user_app, site_app):
        # subapp exceptions do not reach the main app, so we must install the
        # handlers here also to allow middlewares to react to errors,
        # e.g. rollback a DB transaction
        a.add_middleware(DatabaseMetricsMiddleware, db=db)
        a.add_middleware(transaction_middleware_class, db=db)  # type: ignore
        a.add_middleware(ExceptionMiddleware)
        a.add_exception_handler(
            RequestValidationError, request_validation_error_handler
        )

    app.mount("/api", user_app)
    app.mount("/site", site_app)

    ServiceCollection.register_metrics(prometheus_registry)

    return app


async def ensure_db_entries(conn: AsyncConnection) -> None:
    """Ensure global database entries are populated."""
    await ConfigService(conn).ensure()
    await SettingsService(conn).ensure()


def _log_settings(logger: Logger, settings: Settings) -> None:
    logger.info("Application settings:")
    for key, value in sorted(settings.model_dump().items()):
        logger.info(f"  {key}: {value}")


def _serve_index_html(static_dir: str, root_path_url: str) -> HTMLResponse:
    root_path = urllib.parse.urlparse(root_path_url).path
    index_html_path = Path(static_dir) / "index.html"
    with index_html_path.open() as f:
        soup = bs(f, features="html.parser")
    _update_resource_paths(soup, root_path)
    return HTMLResponse(content=str(soup), status_code=200)


def _update_resource_paths(soup: bs, root_path: str) -> None:
    """Updates the paths of resources
    in the HTML to include the root path."""
    for link in soup.find_all("link", attrs={"href": True}):
        link["href"] = _replace_ui_path(link["href"], root_path)  # type: ignore
    for script in soup.find_all("script", attrs={"src": True}):
        script["src"] = _replace_ui_path(script["src"], root_path)  # type: ignore
    scripts = soup.find_all(
        "script",
        string=lambda text: "__ROOT_PATH__" in text
        if text is not None
        else False,
    )
    for script in scripts:
        script.string = _set_root_path(script.string, root_path)  # type: ignore


def _replace_ui_path(original_path: str, root_path: str) -> str:
    return original_path.replace("/ui", f"{root_path}/ui", 1)


def _set_root_path(script_content: str, root_path: str) -> str:
    """Sets the global __ROOT_PATH__ in inline scripts."""
    return re.sub(
        r'globalThis\.__ROOT_PATH__\s*=\s*"";',
        f'globalThis.__ROOT_PATH__="{root_path}";',
        script_content,
    )


class FastApiBaizeFileResponse(FastApiResponse):
    _baize_response: BaizeFileResponse

    def __init__(self, path: Path, **kwargs: Any) -> None:
        filepath = str(kwargs.get("filepath", kwargs.get("path", path)))
        kwargs.pop("filepath", None)
        kwargs.pop("path", None)
        stat_result = os.stat(filepath)
        self._baize_response = BaizeFileResponse(
            filepath,
            **kwargs,
            content_type=guess_type(filepath)[0],
            stat_result=stat_result,
        )
        super().__init__(
            media_type=guess_type(filepath)[0],
            headers={"content-length": str(stat_result.st_size)},
        )

    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self._baize_response(*args, **kwargs)

    def __getattr__(self, name):  # type: ignore[no-untyped-def]
        return getattr(self._baize_response, name)
