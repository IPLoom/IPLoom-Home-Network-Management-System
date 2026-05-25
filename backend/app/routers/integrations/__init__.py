from fastapi import APIRouter
from .deco import router as deco_router
from .openwrt import router as openwrt_router
from .adguard import router as adguard_router
from .tailscale import router as tailscale_router

router = APIRouter()

router.include_router(deco_router, prefix="/deco", tags=["Integrations - Deco"])
router.include_router(openwrt_router, prefix="/openwrt", tags=["Integrations - OpenWrt"])
router.include_router(adguard_router, prefix="/adguard", tags=["Integrations - AdGuard"])
router.include_router(tailscale_router, prefix="/tailscale", tags=["Integrations - Tailscale"])
