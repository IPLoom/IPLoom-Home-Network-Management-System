from fastapi import APIRouter
from app.routers.integrations.adguard import router as adguard_router
from app.routers.integrations.deco import router as deco_router
from app.routers.integrations.openwrt import router as openwrt_router

router = APIRouter()

router.include_router(adguard_router, prefix="/adguard", tags=["adguard"])
router.include_router(deco_router, prefix="/deco", tags=["deco"])
router.include_router(openwrt_router, prefix="/openwrt", tags=["openwrt"])
