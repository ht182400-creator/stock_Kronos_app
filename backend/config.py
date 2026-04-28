"""
Kronos 金融预测 Web 应用 - 后端配置
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]
    
    # 模型配置
    MODEL_DEFAULT: str = "kronos-small"
    DEVICE: str = "cpu"  # cpu, cuda:0, mps
    KRONOS_REPO_DIR: Path = Path("D:/Work_Area/Kronos")  # 本地 Kronos 源码路径
    
    # HuggingFace Hub 配置（用于下载模型）
    HF_HOME: str = os.path.expanduser("~/.cache/huggingface")
    
    # 上传配置
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".csv"}
    
    # 预测配置
    DEFAULT_LOOKBACK: int = 400
    DEFAULT_PRED_LEN: int = 120
    MAX_LOOKBACK: int = 512
    MAX_PRED_LEN: int = 256
    
    # 任务队列配置
    MAX_QUEUE_SIZE: int = 10
    TASK_TIMEOUT: int = 600  # 10 分钟超时
    
    # 结果缓存配置
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 小时
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()


# 可用模型配置
AVAILABLE_MODELS = {
    "kronos-mini": {
        "name": "Kronos-mini",
        "model_id": "NeoQuasar/Kronos-mini",
        "tokenizer_id": "NeoQuasar/Kronos-Tokenizer-2k",
        "context_length": 2048,
        "params": "4.1M",
        "description": "轻量级模型，适合快速预测，CPU 推理首选",
    },
    "kronos-small": {
        "name": "Kronos-small",
        "model_id": "NeoQuasar/Kronos-small",
        "tokenizer_id": "NeoQuasar/Kronos-Tokenizer-base",
        "context_length": 512,
        "params": "24.7M",
        "description": "平衡型模型，性能与速度兼顾",
    },
    "kronos-base": {
        "name": "Kronos-base",
        "model_id": "NeoQuasar/Kronos-base",
        "tokenizer_id": "NeoQuasar/Kronos-Tokenizer-base",
        "context_length": 512,
        "params": "102.3M",
        "description": "高质量模型，需要较强算力",
    },
}
