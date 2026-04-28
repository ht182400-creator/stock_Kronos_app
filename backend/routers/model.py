"""
Kronos 金融预测 Web 应用 - 模型管理路由
"""

from fastapi import APIRouter

from services.kronos_service import kronos_service
from models.schemas import (
    ModelInfo,
    LoadModelRequest,
    LoadModelResponse,
    ModelStatusResponse,
    BaseResponse,
)

router = APIRouter(prefix="/api/models", tags=["模型管理"])


@router.get("", response_model=BaseResponse)
async def get_available_models():
    """
    获取可用模型列表
    
    Returns:
        可用的 Kronos 模型列表
    """
    models = kronos_service.get_available_models()
    model_list = [
        ModelInfo(
            key=key,
            name=cfg["name"],
            model_id=cfg["model_id"],
            tokenizer_id=cfg["tokenizer_id"],
            context_length=cfg["context_length"],
            params=cfg["params"],
            description=cfg["description"],
        )
        for key, cfg in models.items()
    ]
    
    return {
        "success": True,
        "message": "获取成功",
        "models": model_list,
    }


@router.post("/load", response_model=LoadModelResponse)
async def load_model(request: LoadModelRequest):
    """
    加载指定模型
    
    Args:
        request: 加载请求
    
    Returns:
        加载结果
    """
    result = await kronos_service.load_model(
        model_key=request.model_key,
        device=request.device,
    )
    
    if result.get("success"):
        return {
            "success": True,
            "message": result["message"],
            "model_info": result["model_info"],
        }
    else:
        return {
            "success": False,
            "message": result.get("error", "加载失败"),
        }


@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status():
    """
    获取模型状态
    
    Returns:
        当前模型加载状态
    """
    if kronos_service.is_loaded:
        return {
            "success": True,
            "message": "模型已加载",
            "loaded": True,
            "current_model": kronos_service.current_model,
            "device": kronos_service.device,
        }
    else:
        return {
            "success": True,
            "message": "模型未加载",
            "loaded": False,
        }
