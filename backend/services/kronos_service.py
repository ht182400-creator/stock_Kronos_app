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
                        "model_info": {**AVAILABLE_MODELS[model_key], "key": model_key},
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
                "model_info": {**model_config, "key": model_key},
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
        支持从 HuggingFace 或本地路径加载
        
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
            
            # 判断使用本地还是远程模型
            local_tokenizer_path = model_config.get("local_tokenizer_path")
            local_model_path = model_config.get("local_model_path")
            
            # 加载 Tokenizer
            if local_tokenizer_path:
                print(f"正在从本地加载 Tokenizer: {local_tokenizer_path}")
                tokenizer = KronosTokenizer.from_pretrained(local_tokenizer_path)
            else:
                print(f"正在从 HuggingFace 加载 Tokenizer: {model_config['tokenizer_id']}")
                tokenizer = KronosTokenizer.from_pretrained(model_config["tokenizer_id"])
            
            # 加载 Model
            if local_model_path:
                print(f"正在从本地加载 Model: {local_model_path}")
                model = Kronos.from_pretrained(local_model_path)
            else:
                print(f"正在从 HuggingFace 加载 Model: {model_config['model_id']}")
                model = Kronos.from_pretrained(model_config["model_id"])
            
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
            
            # 获取历史数据统计用于合理化
            hist_close = df["close"].values
            hist_mean = float(hist_close.mean())
            hist_std = float(hist_close.std())
            
            # 转换为预测点列表（并进行合理化处理）
            predictions = []
            for idx, row in pred_df.iterrows():
                pred_open = float(row.get("open", 0))
                pred_high = float(row.get("high", 0))
                pred_low = float(row.get("low", 0))
                pred_close = float(row.get("close", 0))
                pred_volume = float(row.get("volume", 0))
                
                # 合理化处理
                pred_open, pred_high, pred_low, pred_close = self._sanitize_prediction(
                    pred_open, pred_high, pred_low, pred_close, hist_mean, hist_std
                )
                
                predictions.append({
                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "open": pred_open,
                    "high": pred_high,
                    "low": pred_low,
                    "close": pred_close,
                    "volume": pred_volume,
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

    def _sanitize_prediction(
        self,
        open_p: float,
        high_p: float,
        low_p: float,
        close_p: float,
        hist_mean: float,
        hist_std: float
    ) -> tuple:
        """
        合理化预测结果
        
        Args:
            open_p: 开盘价
            high_p: 最高价
            low_p: 最低价
            close_p: 收盘价
            hist_mean: 历史均价
            hist_std: 历史标准差
        
        Returns:
            (open, high, low, close) 修正后的值
        """
        import numpy as np
        
        # 允许的价格范围：均值 ± 3倍标准差
        min_price = max(0.01, hist_mean - 3 * hist_std)
        max_price = hist_mean + 3 * hist_std
        
        # 1. 确保所有价格非负
        open_p = max(0.01, open_p)
        high_p = max(0.01, high_p)
        low_p = max(0.01, low_p)
        close_p = max(0.01, close_p)
        
        # 2. 确保 high >= low
        if high_p < low_p:
            high_p, low_p = low_p, high_p
        
        # 3. 确保 open 和 close 在 [low, high] 范围内
        open_p = np.clip(open_p, low_p, high_p)
        close_p = np.clip(close_p, low_p, high_p)
        
        # 4. 确保价格在合理范围内
        if open_p < min_price:
            open_p = min_price
        if open_p > max_price:
            open_p = max_price
            
        if close_p < min_price:
            close_p = min_price
        if close_p > max_price:
            close_p = max_price
            
        if high_p < min_price:
            high_p = min_price
        if high_p > max_price:
            high_p = max_price
            
        if low_p < min_price:
            low_p = min_price
        if low_p > max_price:
            low_p = max_price
        
        # 5. 再次确保 high >= low
        if high_p < low_p:
            high_p = low_p
        
        # 6. 如果 high 和 low 差距太小，给一点空间
        if high_p - low_p < hist_std * 0.1:
            center = (high_p + low_p) / 2
            spread = hist_std * 0.1
            low_p = center - spread
            high_p = center + spread
        
        return round(open_p, 2), round(high_p, 2), round(low_p, 2), round(close_p, 2)


# 全局服务实例
kronos_service = KronosService()
