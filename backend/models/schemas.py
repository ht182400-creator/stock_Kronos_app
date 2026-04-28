"""
Kronos 金融预测 Web 应用 - Pydantic 数据模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 通用响应模型 ============

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: ErrorDetail


# ============ 模型相关模型 ============

class ModelInfo(BaseModel):
    """模型信息"""
    key: str
    name: str
    model_id: str
    tokenizer_id: str
    context_length: int
    params: str
    description: str


class LoadModelRequest(BaseModel):
    """加载模型请求"""
    model_key: str = Field(default="kronos-small", description="模型标识")
    device: str = Field(default="cpu", description="设备: cpu, cuda:0, mps")


class LoadModelResponse(BaseResponse):
    """加载模型响应"""
    model_info: ModelInfo


class ModelStatusResponse(BaseResponse):
    """模型状态响应"""
    loaded: bool
    current_model: Optional[str] = None
    device: Optional[str] = None


# ============ 数据相关模型 ============

class DataFileInfo(BaseModel):
    """数据文件信息"""
    file_id: str
    file_name: str
    file_path: str
    size: int
    rows: int
    columns: List[str]
    time_range: Optional[Dict[str, str]] = None
    uploaded_at: datetime


class UploadResponse(BaseResponse):
    """上传响应"""
    file_id: str
    file_name: str
    rows: int


# ============ 预测相关模型 ============

class PredictionParams(BaseModel):
    """预测参数"""
    lookback: int = Field(default=400, ge=100, le=512, description="回看窗口")
    pred_len: int = Field(default=120, ge=1, le=256, description="预测长度")
    temperature: float = Field(default=0.8, ge=0.1, le=1.0, description="采样温度")
    top_p: float = Field(default=0.9, ge=0.5, le=1.0, description="Nucleus采样概率")
    sample_count: int = Field(default=1, ge=1, le=10, description="采样路径数")
    start_date: Optional[str] = Field(default=None, description="起始日期时间")


class PredictionRequest(BaseModel):
    """预测请求"""
    file_id: str = Field(description="文件ID")
    params: PredictionParams = Field(default_factory=PredictionParams)


class PredictionPoint(BaseModel):
    """预测数据点"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class PredictionStatistics(BaseModel):
    """预测统计"""
    avg_close: float
    max_close: float
    min_close: float
    volatility: float  # 波动率


class PredictionResultData(BaseModel):
    """预测结果数据"""
    predictions: List[PredictionPoint]
    chart_config: Dict[str, Any]  # ECharts 配置
    statistics: PredictionStatistics


class PredictionResponse(BaseResponse):
    """预测响应（同步）"""
    predictions: List[PredictionPoint]
    statistics: PredictionStatistics
    execution_time: float


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AsyncPredictResponse(BaseResponse):
    """异步预测响应"""
    task_id: str
    status: str


class TaskResultResponse(BaseResponse):
    """任务结果响应"""
    task_id: str
    status: str
    result: Optional[PredictionResultData] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class PredictionHistoryItem(BaseModel):
    """预测历史项"""
    task_id: str
    file_name: str
    params: PredictionParams
    status: str
    created_at: datetime
    execution_time: Optional[float] = None
