"""
Kronos 金融预测 Web 应用 - Kronos 模型服务
"""

import sys
import asyncio
import time
from typing import Optional, Dict, Any
from pathlib import Path

import pandas as pd
import torch

# 添加 Kronos 源码路径
from config import settings, AVAILABLE_MODELS


class KronosService:
    """Kronos 模型服务"""
    
    _instance: Optional["KronosService"] = None
    
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
        self._predictor: Optional[Any] = None
        self._current_model_key: Optional[str] = None
        self._device: Optional[str] = None
        self._lock = asyncio.Lock()
        self._loading = False
    
    @property
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._predictor is not None
    
    @property
    def current_model(self) -> Optional[str]:
        """获取当前模型名称"""
        return self._current_model_key
    
    @property
    def device(self) -> Optional[str]:
        """获取当前设备"""
        return self._device
    
    def get_available_models(self) -> Dict[str, Any]:
        """获取可用模型列表"""
        return AVAILABLE_MODELS
    
    async def load_model(
        self,
        model_key: str = "kronos-small",
        device: str = "cpu"
    ) -> Dict[str, Any]:
        """
        异步加载 Kronos 模型
        
        Args:
            model_key: 模型标识
            device: 设备 (cpu, cuda:0, mps)
        
        Returns:
            模型信息字典
        """
        async with self._lock:
            # 检查是否已加载相同模型
            if self._predictor is not None:
                if self._current_model_key == model_key and self._device == device:
                    return {
                        "success": True,
                        "message": "模型已加载",
                        "model_info": AVAILABLE_MODELS[model_key],
                    }
            
            # 防止重复加载
            if self._loading:
                return {
                    "success": False,
                    "error": "模型正在加载中",
                }
            
            self._loading = True
        
        try:
            # 验证模型
            if model_key not in AVAILABLE_MODELS:
                raise ValueError(f"不支持的模型: {model_key}")
            
            model_config = AVAILABLE_MODELS[model_key]
            
            # 在线程池中执行模型加载（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            
            predictor = await loop.run_in_executor(
                None,
                self._load_model_sync,
                model_config,
                device
            )
            
            self._predictor = predictor
            self._current_model_key = model_key
            self._device = device
            
            return {
                "success": True,
                "message": f"模型 {model_config['name']} 加载成功",
                "model_info": model_config,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"模型加载失败: {str(e)}",
            }
        
        finally:
            self._loading = False
    
    def _load_model_sync(
        self,
        model_config: Dict[str, Any],
        device: str
    ) -> Any:
        """
        同步加载模型（在线程中执行）
        
        Args:
            model_config: 模型配置
            device: 设备
        
        Returns:
            KronosPredictor 实例
        """
        # 添加 Kronos 源码路径
        sys.path.insert(0, str(settings.KRONOS_REPO_DIR))
        
        try:
            from model import Kronos, KronosTokenizer, KronosPredictor
            
            print(f"正在加载 Tokenizer: {model_config['tokenizer_id']}")
            tokenizer = KronosTokenizer.from_pretrained(
                model_config["tokenizer_id"]
            )
            
            print(f"正在加载 Model: {model_config['model_id']}")
            model = Kronos.from_pretrained(
                model_config["model_id"]
            )
            
            print(f"正在创建 Predictor (device={device})")
            predictor = KronosPredictor(
                model,
                tokenizer,
                device=device,
                max_context=model_config["context_length"]
            )
            
            print("模型加载完成!")
            return predictor
        
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise
    
    async def predict(
        self,
        df: pd.DataFrame,
        x_timestamp: pd.Series,
        y_timestamp: pd.Series,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行预测
        
        Args:
            df: 历史数据 DataFrame
            x_timestamp: 历史数据时间戳
            y_timestamp: 预测时间戳
            params: 预测参数
        
        Returns:
            预测结果字典
        """
        if self._predictor is None:
            return {
                "success": False,
                "error": "模型未加载，请先调用 /api/models/load",
            }
        
        try:
            loop = asyncio.get_event_loop()
            start_time = time.time()
            
            # 在线程池中执行预测
            pred_df = await loop.run_in_executor(
                None,
                self._predict_sync,
                df,
                x_timestamp,
                y_timestamp,
                params
            )
            
            execution_time = time.time() - start_time
            
            # 转换为预测点列表
            predictions = []
            for idx, row in pred_df.iterrows():
                predictions.append({
                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                })
            
            # 计算统计信息
            close_values = pred_df["close"].values
            statistics = {
                "avg_close": float(close_values.mean()),
                "max_close": float(close_values.max()),
                "min_close": float(close_values.min()),
                "volatility": float(close_values.std() / close_values.mean()) if close_values.mean() != 0 else 0,
            }
            
            return {
                "success": True,
                "predictions": predictions,
                "statistics": statistics,
                "execution_time": execution_time,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"预测失败: {str(e)}",
            }
    
    def _predict_sync(
        self,
        df: pd.DataFrame,
        x_timestamp: pd.Series,
        y_timestamp: pd.Series,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        同步执行预测
        
        Returns:
            预测结果 DataFrame
        """
        # 确保 x_timestamp 和 y_timestamp 是 Series 类型
        if isinstance(x_timestamp, pd.DatetimeIndex):
            x_timestamp = pd.Series(x_timestamp.values, name="timestamps")
        if isinstance(y_timestamp, pd.DatetimeIndex):
            y_timestamp = pd.Series(y_timestamp.values, name="timestamps")
        
        # 执行预测
        pred_df = self._predictor.predict(
            df=df,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=params.get("pred_len", 120),
            T=params.get("temperature", 0.8),
            top_p=params.get("top_p", 0.9),
            sample_count=params.get("sample_count", 1),
            verbose=False
        )
        
        return pred_df


# 全局服务实例
kronos_service = KronosService()
