from msm.apiserver.site.handlers import (
    config,
    enroll,
    images,
    report,
)

ROUTERS = (
    config.v1_router,
    enroll.v1_router,
    report.v1_router,
    images.v1_router,
)
