from msm.apiserver.user.handlers import (
    bootassets,
    images,
    login,
    profiles,
    selections,
    settings,
    sites,
    tokens,
    users,
)

ROUTERS = (
    bootassets.v1_router,
    images.v1_router,
    login.v1_router,
    profiles.v1_router,
    selections.v1_router,
    settings.v1_router,
    sites.v1_router,
    tokens.v1_router,
    users.v1_router,
)
