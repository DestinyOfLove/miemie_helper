"""运行环境能力 API。"""

from fastapi import APIRouter

from src.runtime_capabilities import get_runtime_capabilities
from src.search.models import RuntimeCapabilities

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/capabilities", response_model=RuntimeCapabilities)
async def read_runtime_capabilities() -> RuntimeCapabilities:
    """返回当前运行环境能力。"""
    return get_runtime_capabilities()
