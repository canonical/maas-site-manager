from datetime import datetime, timedelta
import json

import pytest

from msm.db.models import (
    BootAssetKind,
    BootAssetLabel,
)
from msm.time import now_utc
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.mark.asyncio
class TestBootAssetsGetHandler:
    async def test_get(self, user_client: Client, factory: Factory) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(
            boot_source_id=boot_source.id,
            kind=BootAssetKind.BOOTLOADER,
            label=BootAssetLabel.CANDIDATE,
            os="test_os",
            release="test_release",
            codename="test_codename",
            title="test title",
            arch="test_arch",
            subarch="test_subarch",
            compatibility=["test", "compatibility"],
            flavor="test_flavor",
            base_image="test_base_image",
            eol=now_utc() + timedelta(days=3650),
            esm_eol=now_utc() + timedelta(days=7000),
        )
        assets = await user_client.get("/bootassets")
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["page"] == 1
        assert resp_body["size"] == 20
        assert resp_body["total"] == 1
        resp_body["items"][0]["id"] = boot_asset.id

        # dumping to JSON then loading back to a dict converts types like datetime
        # to string representations, which are returned by the API
        assert resp_body["items"] == [json.loads(boot_asset.model_dump_json())]

    async def test_get_with_sorting(
        self, user_client: Client, factory: Factory
    ) -> None:
        boot_source = await factory.make_BootSource()
        boot_asset1 = await factory.make_BootAsset(
            boot_source_id=boot_source.id, os="a", release="b"
        )
        boot_asset2 = await factory.make_BootAsset(
            boot_source_id=boot_source.id, os="b", release="a"
        )
        assets = await user_client.get("/bootassets?sort_by=os")
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["items"] == [
            json.loads(boot_asset1.model_dump_json()),
            json.loads(boot_asset2.model_dump_json()),
        ]
        assets = await user_client.get("/bootassets?sort_by=release")
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["items"] == [
            json.loads(boot_asset2.model_dump_json()),
            json.loads(boot_asset1.model_dump_json()),
        ]

    async def test_get_with_page_and_size(
        self, user_client: Client, factory: Factory
    ) -> None:
        bs = await factory.make_BootSource()
        for i in range(4):
            await factory.make_BootAsset(bs.id, title=f"{i+1}")

        resp = await user_client.get("/bootassets?page=2&size=2&sort_by=title")
        assert resp.status_code == 200
        resp_body = resp.json()
        assert resp_body["page"] == 2
        assert resp_body["size"] == 2
        assert len(resp_body["items"]) == 2
        assert resp_body["items"][0]["title"] == "3"
        assert resp_body["items"][1]["title"] == "4"

    @pytest.mark.parametrize("sort_by", ["id", "kind,kind", "not_a_field"])
    async def test_invalid_sort_params(
        self, user_client: Client, factory: Factory, sort_by: str
    ) -> None:
        resp = await user_client.get(f"/bootassets?sort_by={sort_by}")
        assert resp.status_code == 422

    @pytest.mark.parametrize("page", [-1, 0])
    async def test_invalid_page_params(
        self, user_client: Client, factory: Factory, page: int
    ) -> None:
        resp = await user_client.get(f"/bootassets?page={page}")
        assert resp.status_code == 422

    @pytest.mark.parametrize("size", [0, -1, 101])
    async def test_invalid_size_params(
        self, user_client: Client, factory: Factory, size: int
    ) -> None:
        resp = await user_client.get(f"/bootassets?size={size}")
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestBootAssetsPostHandler:
    async def test_post(self, user_client: Client, factory: Factory) -> None:
        boot_source = await factory.make_BootSource()
        data = {
            "boot_source_id": boot_source.id,
            "kind": BootAssetKind.BOOTLOADER,
            "label": BootAssetLabel.CANDIDATE,
            "os": "ubuntu",
            "release": "noble",
            "codename": "Noble Numbat",
            "title": "My Custom Image",
            "arch": "amd64",
            "subarch": "generic",
            "compatibility": ["generic"],
            "flavor": "generic",
            "base_image": "ubuntu",
            "eol": (now_utc() + timedelta(days=365)).isoformat(),
            "esm_eol": (now_utc() + timedelta(days=3650)).isoformat(),
        }
        resp = await user_client.post("/bootassets", json=data)
        new_id = resp.json()["id"]
        assert resp.status_code == 200
        stored = await factory.get("boot_asset")
        assert len(stored) == 1
        data["eol"] = datetime.fromisoformat(data["eol"])  # type: ignore
        data["esm_eol"] = datetime.fromisoformat(data["esm_eol"])  # type: ignore
        assert stored[0] == data | {"id": new_id}

    async def test_post_missing_details(
        self, user_client: Client, factory: Factory
    ) -> None:
        boot_source = await factory.make_BootSource()
        data = {
            "boot_source_id": boot_source.id,
            "kind": BootAssetKind.BOOTLOADER,
            "label": BootAssetLabel.CANDIDATE,
        }
        resp = await user_client.post("/bootassets", json=data)
        assert resp.status_code == 422

    async def test_post_missing_boot_source(
        self, user_client: Client, factory: Factory
    ) -> None:
        data = {
            "boot_source_id": 999,
            "kind": BootAssetKind.BOOTLOADER,
            "label": BootAssetLabel.CANDIDATE,
            "os": "ubuntu",
            "release": "noble",
            "codename": "Noble Numbat",
            "title": "My Custom Image",
            "arch": "amd64",
            "subarch": "generic",
            "compatibility": ["generic"],
            "flavor": "generic",
            "base_image": "ubuntu",
            "eol": (now_utc() + timedelta(days=365)).isoformat(),
            "esm_eol": (now_utc() + timedelta(days=3650)).isoformat(),
        }
        resp = await user_client.post("/bootassets", json=data)
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestBootSourcesGetHandler:
    async def test_get(self, user_client: Client, factory: Factory) -> None:
        boot_source = await factory.make_BootSource(
            priority=2,
            url="http://test.url",
            keyring="test_keyring",
            sync_interval=4200,
        )
        sources = await user_client.get("/bootasset-sources")
        assert sources.status_code == 200
        resp_body = sources.json()
        assert resp_body["page"] == 1
        assert resp_body["size"] == 20
        assert resp_body["total"] == 1
        assert resp_body["items"] == [boot_source.model_dump()]

    async def test_get_with_sorting(
        self, user_client: Client, factory: Factory
    ) -> None:
        boot_source1 = await factory.make_BootSource(url="a", keyring="b")
        boot_source2 = await factory.make_BootSource(url="b", keyring="a")
        assets = await user_client.get("/bootasset-sources?sort_by=url")
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["items"] == [
            json.loads(boot_source1.model_dump_json()),
            json.loads(boot_source2.model_dump_json()),
        ]
        assets = await user_client.get("/bootasset-sources?sort_by=keyring")
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["items"] == [
            json.loads(boot_source2.model_dump_json()),
            json.loads(boot_source1.model_dump_json()),
        ]

    async def test_get_with_page_and_size(
        self, user_client: Client, factory: Factory
    ) -> None:
        for i in range(4):
            await factory.make_BootSource(priority=i + 1)

        resp = await user_client.get(
            "/bootasset-sources?page=2&size=2&sort_by=priority"
        )
        assert resp.status_code == 200
        resp_body = resp.json()
        assert resp_body["page"] == 2
        assert resp_body["size"] == 2
        assert len(resp_body["items"]) == 2
        assert resp_body["items"][0]["priority"] == 3
        assert resp_body["items"][1]["priority"] == 4

    @pytest.mark.parametrize("sort_by", ["id", "kind,kind", "not_a_field"])
    async def test_invalid_sort_params(
        self, user_client: Client, factory: Factory, sort_by: str
    ) -> None:
        resp = await user_client.get(f"/bootasset-sources?sort_by={sort_by}")
        assert resp.status_code == 422

    @pytest.mark.parametrize("page", [-1, 0])
    async def test_invalid_page_params(
        self, user_client: Client, factory: Factory, page: int
    ) -> None:
        resp = await user_client.get(f"/bootasset-sources?page={page}")
        assert resp.status_code == 422

    @pytest.mark.parametrize("size", [0, -1, 101])
    async def test_invalid_size_params(
        self, user_client: Client, factory: Factory, size: int
    ) -> None:
        resp = await user_client.get(f"/bootasset-sources?size={size}")
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestBootSourcesPostHandler:
    async def test_post(self, user_client: Client, factory: Factory) -> None:
        data = {
            "priority": 1,
            "url": "http://some.image.server",
            "keyring": "testkeyring",
            "sync_interval": 1000,
        }
        resp = await user_client.post("/bootasset-sources", json=data)
        new_id = resp.json()["id"]
        assert resp.status_code == 200
        stored = await factory.get("boot_source")
        assert len(stored) == 1
        assert stored[0] == data | {"id": new_id}

    async def test_post_missing_details(
        self, user_client: Client, factory: Factory
    ) -> None:
        data = {
            "priority": 1,
            "url": "http://some.image.server",
            "keyring": "testkeyring",
        }
        resp = await user_client.post("/bootasset-sources", json=data)
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestBootSourceSelectionsGetHandler:
    async def test_get(self, user_client: Client, factory: Factory) -> None:
        boot_source = await factory.make_BootSource()
        boot_source2 = await factory.make_BootSource()
        selection = await factory.make_BootSourceSelection(
            boot_source.id,
            label=BootAssetLabel.CANDIDATE,
            os="test_os",
            release="test_release",
            arches=["test", "arches"],
        )
        await factory.make_BootSourceSelection(boot_source2.id)
        selections = await user_client.get(
            f"/bootasset-sources/{boot_source.id}/selections"
        )
        assert selections.status_code == 200
        resp_body = selections.json()
        assert resp_body["page"] == 1
        assert resp_body["size"] == 20
        assert resp_body["total"] == 1
        assert resp_body["items"] == [selection.model_dump()]

    async def test_get_with_sorting(
        self, user_client: Client, factory: Factory
    ) -> None:
        boot_source = await factory.make_BootSource()
        selection1 = await factory.make_BootSourceSelection(
            boot_source.id, os="a", release="b"
        )
        selection2 = await factory.make_BootSourceSelection(
            boot_source.id, os="b", release="a"
        )
        assets = await user_client.get(
            f"/bootasset-sources/{boot_source.id}/selections?sort_by=os"
        )
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["items"] == [
            json.loads(selection1.model_dump_json()),
            json.loads(selection2.model_dump_json()),
        ]
        assets = await user_client.get(
            f"/bootasset-sources/{boot_source.id}/selections?sort_by=release"
        )
        assert assets.status_code == 200
        resp_body = assets.json()
        assert resp_body["items"] == [
            json.loads(selection2.model_dump_json()),
            json.loads(selection1.model_dump_json()),
        ]

    async def test_get_with_page_and_size(
        self, user_client: Client, factory: Factory
    ) -> None:
        bs = await factory.make_BootSource()
        for i in range(4):
            await factory.make_BootSourceSelection(bs.id, release=f"{i+1}")

        resp = await user_client.get(
            f"/bootasset-sources/{bs.id}/selections?page=2&size=2&sort_by=release"
        )
        assert resp.status_code == 200
        resp_body = resp.json()
        assert resp_body["page"] == 2
        assert resp_body["size"] == 2
        assert len(resp_body["items"]) == 2
        assert resp_body["items"][0]["release"] == "3"
        assert resp_body["items"][1]["release"] == "4"

    @pytest.mark.parametrize("sort_by", ["id", "kind,kind", "not_a_field"])
    async def test_invalid_sort_params(
        self, user_client: Client, factory: Factory, sort_by: str
    ) -> None:
        resp = await user_client.get(
            f"/bootasset-sources/1/selections?sort_by={sort_by}"
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("page", [-1, 0])
    async def test_invalid_page_params(
        self, user_client: Client, factory: Factory, page: int
    ) -> None:
        resp = await user_client.get(
            f"/bootasset-sources/1/selections?page={page}"
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("size", [0, -1, 101])
    async def test_invalid_size_params(
        self, user_client: Client, factory: Factory, size: int
    ) -> None:
        resp = await user_client.get(
            f"/bootasset-sources/1/selections?size={size}"
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestBootAssetVersionsPostHandler:
    async def test_post(self, user_client: Client, factory: Factory) -> None:
        bs = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(bs.id)
        data = {
            "version": "20250302.1",
        }
        resp = await user_client.post(
            f"/bootassets/{boot_asset.id}/versions", json=data
        )
        new_id = resp.json()["id"]
        assert resp.status_code == 200
        stored = await factory.get("boot_asset_version")
        assert len(stored) == 1
        assert stored[0] == data | {
            "id": new_id,
            "boot_asset_id": boot_asset.id,
        }

    async def test_post_missing_details(
        self, user_client: Client, factory: Factory
    ) -> None:
        bs = await factory.make_BootSource()
        boot_asset = await factory.make_BootAsset(bs.id)
        resp = await user_client.post(
            f"/bootassets/{boot_asset.id}/versions",
        )
        assert resp.status_code == 422

    async def test_post_missing_boot_source(
        self, user_client: Client, factory: Factory
    ) -> None:
        data = {
            "version": "20250302.1",
        }
        resp = await user_client.post(f"/bootassets/{999}/versions", json=data)
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestBootAssetItemsPostHandler:
    async def test_post(self, user_client: Client, factory: Factory) -> None:
        bs = await factory.make_BootSource()
        ba = await factory.make_BootAsset(bs.id)
        boot_asset_version = await factory.make_BootAssetVersion(ba.id)
        data = {
            "ftype": "kernel",
            "sha256": "testblaksjdflkj",
            "path": "/item",
            "size": 2321345623,
            "source_package": "ubukernel",
            "source_version": "23.4.1",
            "source_release": "noble",
        }
        resp = await user_client.post(
            f"/bootasset-versions/{boot_asset_version.id}/items", json=data
        )
        assert resp.status_code == 200
        new_id = resp.json()["id"]
        stored = await factory.get("boot_asset_item")
        assert len(stored) == 1
        assert stored[0] == data | {
            "id": new_id,
            "boot_asset_version_id": boot_asset_version.id,
            "bytes_synced": 0,
        }

    async def test_post_missing_details(
        self, user_client: Client, factory: Factory
    ) -> None:
        bs = await factory.make_BootSource()
        ba = await factory.make_BootAsset(bs.id)
        boot_asset_version = await factory.make_BootAssetVersion(ba.id)
        data = {
            "sha256": "testblaksjdflkj",
            "path": "/item",
            "size": 2321345623,
            "source_package": "ubukernel",
            "source_version": "23.4.1",
            "source_release": "noble",
        }
        resp = await user_client.post(
            f"/bootasset-versions/{boot_asset_version.id}/items", json=data
        )
        assert resp.status_code == 422

    async def test_post_missing_boot_asset_version(
        self, user_client: Client, factory: Factory
    ) -> None:
        data = {
            "ftype": "kernel",
            "sha256": "testblaksjdflkj",
            "path": "/item",
            "size": 2321345623,
            "source_package": "ubukernel",
            "source_version": "23.4.1",
            "source_release": "noble",
        }
        resp = await user_client.post(
            f"/bootasset-versions/{999}/items", json=data
        )
        assert resp.status_code == 404
