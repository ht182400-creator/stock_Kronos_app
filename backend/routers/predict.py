"""
Kronos 金融预测 Web 应用 - 预测路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks

from routers.data import get_file_dataframe, get_file_path
from services.prediction_service import prediction_service
from services.kronos_service import kronos_service
from models.schemas import (
    PredictionRequest,
    PredictionResponse,
    PredictionParams,
    AsyncPredictResponse,
    TaskResultResponse,
)
from config import settings

router = APIRouter(prefix="/api/predict", tags=["预测管理"])


@router.post("", response_model=PredictionResponse)
async def predict_sync(request: PredictionRequest):
    """
    同步预测接口（适合小数据量）
    
    注意：CPU 推理较慢，建议使用异步接口 /api/predict/async
    
    Args:
        request: 预测请求
    
    Returns:
        预测结果
    """
    # 检查模型
    if not kronos_service.is_loaded:
        raise HTTPException(
            status_code=400,
            detail="模型未加载，请先调用 POST /api/models/load"
        )
    
    # 获取数据
    try:
        df = get_file_dataframe(request.file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # 解析参数
    params = request.params.model_dump()
    lookback = params.get("lookback", settings.DEFAULT_LOOKBACK)
    pred_len = params.get("pred_len", settings.DEFAULT_PRED_LEN)
    start_date = params.get("start_date")
    
    # 数据切片
    if start_date:
        import pandas as pd
        start_dt = pd.to_datetime(start_date)
        mask = df["timestamps"] >= start_dt
        time_range_df = df[mask]
        
        if len(time_range_df) < lookback + pred_len:
            raise HTTPException(
                status_code=400,
                detail=f"数据不足：从 {start_date} 开始只有 "
                       f"{len(time_range_df)} 行，需要至少 {lookback + pred_len} 行"
            )
        
        x_df = time_range_df.iloc[:lookback][["open", "high", "low", "close", "volume", "amount"]]
        x_timestamp = time_range_df.iloc[:lookback]["timestamps"]
        y_timestamp = time_range_df.iloc[lookback:lookback + pred_len]["timestamps"]
    else:
        if len(df) < lookback + pred_len:
            raise HTTPException(
                status_code=400,
                detail=f"数据不足：只有 {len(df)} 行，需要至少 {lookback + pred_len} 行"
            )
        
        x_df = df.iloc[:lookback][["open", "high", "low", "close", "volume", "amount"]]
        x_timestamp = df.iloc[:lookback]["timestamps"]
        y_timestamp = df.iloc[lookback:lookback + pred_len]["timestamps"]
    
    # 执行预测
    result = await kronos_service.predict(
        df=x_df,
        x_timestamp=x_timestamp,
        y_timestamp=y_timestamp,
        params=params
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return {
        "success": True,
        "message": "预测完成",
        "predictions": result["predictions"],
        "statistics": result["statistics"],
        "execution_time": result["execution_time"],
    }


@router.post("/async", response_model=AsyncPredictResponse)
async def predict_async(request: PredictionRequest, background_tasks: BackgroundTasks):
    """
    异步预测接口（推荐使用）
    
    提交预测任务后返回 task_id，通过 GET /api/predict/{task_id} 查询状态
    
    Args:
        request: 预测请求
        background_tasks: FastAPI 后台任务
    
    Returns:
        任务ID
    """
    # 检查模型
    if not kronos_service.is_loaded:
        raise HTTPException(
            status_code=400,
            detail="模型未加载，请先调用 POST /api/models/load"
        )
    
    # 获取数据
    try:
        df = get_file_dataframe(request.file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # 解析参数
    params = request.params.model_dump()
    lookback = params.get("lookback", settings.DEFAULT_LOOKBACK)
    pred_len = params.get("pred_len", settings.DEFAULT_PRED_LEN)
    start_date = params.get("start_date")
    
    # 数据验证
    if start_date:
        import pandas as pd
        start_dt = pd.to_datetime(start_date)
        mask = df["timestamps"] >= start_dt
        time_range_df = df[mask]
        
        if len(time_range_df) < lookback + pred_len:
            raise HTTPException(
                status_code=400,
                detail=f"数据不足：从 {start_date} 开始只有 "
                       f"{len(time_range_df)} 行，需要至少 {lookback + pred_len} 行"
            )
    else:
        if len(df) < lookback + pred_len:
            raise HTTPException(
                status_code=400,
                detail=f"数据不足：只有 {len(df)} 行，需要至少 {lookback + pred_len} 行"
            )
    
    # 提交任务
    result = await prediction_service.submit_task(
        file_id=request.file_id,
        df=df,
        params=params
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error"))
    
    task_id = result["task_id"]
    
    # 使用 BackgroundTasks 执行预测
    async def run_prediction():
        print(f"[BACKGROUND] 开始执行任务 {task_id}")
        try:
            await prediction_service._execute_task(prediction_service._tasks[task_id])
            print(f"[BACKGROUND] 任务 {task_id} 执行完成")
        except Exception as e:
            print(f"[BACKGROUND] 任务 {task_id} 执行失败: {e}")
    
    background_tasks.add_task(run_prediction)
    
    return {
        "success": True,
        "message": "任务已提交",
        "task_id": task_id,
        "status": "pending",
    }


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态或结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态或结果
    """
    result = await prediction_service.get_task_result(task_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if result.get("status") == "completed":
        return {
            "success": True,
            "task_id": task_id,
            "status": result["status"],
            "result": result["result"],
            "execution_time": result.get("execution_time"),
        }
    elif result.get("status") == "failed":
        return {
            "success": False,
            "task_id": task_id,
            "status": result["status"],
            "error": result.get("error"),
        }
    else:
        return {
            "success": True,
            "task_id": task_id,
            "status": result["status"],
            "progress": result.get("progress", 0),
        }


@router.get("/history/list")
async def get_history(limit: int = 20):
    """
    获取预测历史
    
    Args:
        limit: 返回数量限制
    
    Returns:
        历史记录列表
    """
    history = await prediction_service.list_history(limit=limit)
    
    return {
        "success": True,
        "history": history,
    }
