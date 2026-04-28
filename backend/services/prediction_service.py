"""
Kronos 金融预测 Web 应用 - 预测任务服务
"""

import uuid
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

import pandas as pd

from services.kronos_service import kronos_service
from config import settings


class PredictionTask:
    """预测任务"""
    
    def __init__(
        self,
        task_id: str,
        file_id: str,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ):
        self.task_id = task_id
        self.file_id = file_id
        self.df = df
        self.params = params
        self.status = "pending"
        self.progress = 0
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress": self.progress,
            "message": self._get_status_message(),
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def _get_status_message(self) -> str:
        """获取状态消息"""
        messages = {
            "pending": "任务等待中...",
            "running": f"正在预测... {self.progress}%",
            "completed": "预测完成",
            "failed": f"预测失败: {self.error}",
        }
        return messages.get(self.status, "")


class PredictionService:
    """预测任务服务"""
    
    _instance: Optional["PredictionService"] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._tasks: Dict[str, PredictionTask] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        self._processing = False
    
    async def submit_task(
        self,
        file_id: str,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提交预测任务
        
        Args:
            file_id: 文件ID
            df: 历史数据
            params: 预测参数
        
        Returns:
            任务信息
        """
        # 检查队列是否已满
        if self._task_queue.full():
            return {
                "success": False,
                "error": "预测队列已满，请稍后再试",
            }
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task = PredictionTask(
            task_id=task_id,
            file_id=file_id,
            df=df,
            params=params
        )
        
        # 存储任务
        self._tasks[task_id] = task
        
        # 加入队列
        await self._task_queue.put(task)
        
        # 启动处理（如果尚未运行）
        if not self._processing:
            self._processing = True
            task_coroutine = asyncio.ensure_future(self._process_queue())
            print(f"[DEBUG] 已启动任务处理协程, 队列长度: {self._task_queue.qsize()}")
            task_coroutine.add_done_callback(
                lambda t: print(f"[DEBUG] 任务处理协程结束, 结果: {t.result()}")
            )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "pending",
            "message": "任务已提交",
        }
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        
        return task.to_dict()
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        
        if task.status == "completed":
            return {
                "success": True,
                "task_id": task_id,
                "status": task.status,
                "result": task.result,
                "execution_time": task.execution_time,
            }
        elif task.status == "failed":
            return {
                "success": False,
                "task_id": task_id,
                "status": task.status,
                "error": task.error,
            }
        else:
            return {
                "success": True,
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
            }
    
    async def list_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取预测历史"""
        tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )[:limit]
        
        return [
            {
                "task_id": t.task_id,
                "file_id": t.file_id,
                "params": t.params,
                "status": t.status,
                "created_at": t.created_at,
                "execution_time": t.execution_time,
            }
            for t in tasks
        ]
    
    async def _process_queue(self):
        """处理任务队列"""
        print(f"[DEBUG] _process_queue 开始运行")
        
        while True:
            try:
                # 从队列获取任务
                task = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                # 执行任务
                await self._execute_task(task)
                
                # 标记任务完成
                self._task_queue.task_done()
            
            except asyncio.TimeoutError:
                # 队列为空，检查是否应该退出
                if self._task_queue.empty():
                    break
            except Exception as e:
                print(f"处理任务时出错: {e}")
    
    async def _execute_task(self, task: PredictionTask):
        """执行预测任务"""
        print(f"[DEBUG] 开始执行任务 {task.task_id}")
        task.status = "running"
        print(f"[DEBUG] task.df columns: {list(task.df.columns)}")
        task.progress = 0
        task.updated_at = datetime.now()
        
        try:
            # 准备数据
            params = task.params
            lookback = params.get("lookback", settings.DEFAULT_LOOKBACK)
            pred_len = params.get("pred_len", settings.DEFAULT_PRED_LEN)
            start_date = params.get("start_date")
            
            # 数据切片
            if start_date:
                start_dt = pd.to_datetime(start_date)
                mask = task.df["timestamps"] >= start_dt
                time_range_df = task.df[mask]
                
                if len(time_range_df) < lookback + pred_len:
                    raise ValueError(
                        f"数据不足：从 {start_date} 开始只有 "
                        f"{len(time_range_df)} 行，需要至少 {lookback + pred_len} 行"
                    )
                
                x_df = time_range_df.iloc[:lookback][["open", "high", "low", "close", "volume", "amount"]]
                x_timestamp = time_range_df.iloc[:lookback]["timestamps"]
                y_timestamp = time_range_df.iloc[lookback:lookback + pred_len]["timestamps"]
                x_df_full = time_range_df.iloc[:lookback]  # 完整数据（含 timestamps）
            else:
                if len(task.df) < lookback + pred_len:
                    raise ValueError(
                        f"数据不足：只有 {len(task.df)} 行，需要至少 {lookback + pred_len} 行"
                    )
                
                x_df = task.df.iloc[:lookback][["open", "high", "low", "close", "volume", "amount"]]
                x_timestamp = task.df.iloc[:lookback]["timestamps"]
                y_timestamp = task.df.iloc[lookback:lookback + pred_len]["timestamps"]
                x_df_full = task.df.iloc[:lookback]  # 完整数据（含 timestamps）
            
            # 转换时间戳格式
            if isinstance(x_timestamp, pd.DatetimeIndex):
                x_timestamp = pd.Series(x_timestamp.values, name="timestamps")
            if isinstance(y_timestamp, pd.DatetimeIndex):
                y_timestamp = pd.Series(y_timestamp.values, name="timestamps")
            
            print(f"[DEBUG] x_df columns: {list(x_df.columns)}, x_timestamp: {x_timestamp.name}")
            print(f"[DEBUG] 准备调用 kronos_service.predict, x_df shape: {x_df.shape}")
            
            task.progress = 30
            
            # 执行预测
            result = await kronos_service.predict(
                df=x_df,
                x_timestamp=x_timestamp,
                y_timestamp=y_timestamp,
                params=params
            )
            
            task.progress = 90
            
            if result.get("success"):
                # 生成图表配置 - 传入完整数据框（含 timestamps）
                chart_config = self._generate_chart_config(
                    x_df_full, result["predictions"], pred_len
                )
                
                task.result = {
                    "predictions": result["predictions"],
                    "chart_config": chart_config,
                    "statistics": result["statistics"],
                }
                task.execution_time = result.get("execution_time", 0)
                task.status = "completed"
                print(f"[DEBUG] 任务 {task.task_id} 执行成功!")
            else:
                raise Exception(result.get("error", "未知错误"))
            
            task.progress = 100
        
        except Exception as e:
            import traceback
            print(f"[DEBUG] 任务执行异常: {e}")
            print(f"[DEBUG] traceback: {traceback.format_exc()}")
            task.status = "failed"
            task.error = str(e)
        
        finally:
            task.updated_at = datetime.now()
    
    def _generate_chart_config(
        self,
        history_df: pd.DataFrame,
        predictions: List[Dict],
        pred_len: int
    ) -> Dict[str, Any]:
        """
        生成 ECharts 配置
        
        Args:
            history_df: 历史数据
            predictions: 预测结果
            pred_len: 预测长度
        
        Returns:
            ECharts 配置字典
        """
        # 历史数据日期
        history_dates = history_df["timestamps"].dt.strftime("%Y-%m-%d %H:%M").tolist()
        
        # 预测日期
        if predictions:
            pred_dates = [p["timestamp"] for p in predictions]
        else:
            last_ts = history_df["timestamps"].iloc[-1]
            freq = history_df["timestamps"].diff().iloc[-1]
            if pd.isna(freq):
                freq = pd.Timedelta(hours=1)
            pred_dates = pd.date_range(
                start=last_ts + freq,
                periods=pred_len,
                freq=freq
            ).strftime("%Y-%m-%d %H:%M").tolist()
        
        # K线数据
        history_klines = [
            [float(row["open"]), float(row["close"]), float(row["low"]), float(row["high"])]
            for _, row in history_df.iterrows()
        ]
        
        pred_klines = [
            [p["open"], p["close"], p["low"], p["high"]]
            for p in predictions
        ]
        
        # 配置
        return {
            "title": {
                "text": "Kronos 金融预测",
                "left": "center"
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross"
                }
            },
            "legend": {
                "data": ["历史数据", "预测数据"],
                "top": 30
            },
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "top": "20%"
            },
            "xAxis": {
                "type": "category",
                "data": history_dates + pred_dates,
                "axisLabel": {
                    "rotate": 45,
                    "interval": 50
                }
            },
            "yAxis": {
                "type": "value",
                "scale": True
            },
            "dataZoom": [
                {
                    "type": "inside",
                    "start": 0,
                    "end": 100
                },
                {
                    "type": "slider",
                    "start": 0,
                    "end": 100
                }
            ],
            "series": [
                {
                    "name": "历史数据",
                    "type": "candlestick",
                    "data": history_klines
                },
                {
                    "name": "预测数据",
                    "type": "candlestick",
                    "data": pred_klines,
                    "itemStyle": {
                        "color": "#6PF8699",     # 预测上涨颜色
                        "color0": "#FF4646",     # 预测下跌颜色
                        "borderColor": "#6PF8699",
                        "borderColor0": "#FF4646"
                    }
                }
            ]
        }


# 全局服务实例
prediction_service = PredictionService()
