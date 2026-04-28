"""
Kronos 金融预测 Web 应用 - 路由初始化
"""

from .model import router as model_router
from .data import router as data_router
from .predict import router as predict_router

__all__ = ["model_router", "data_router", "predict_router"]
