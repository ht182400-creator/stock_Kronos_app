"""
Kronos 金融预测 Web 应用 - 数据管理路由
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from config import settings
from models.schemas import DataFileInfo, UploadResponse

router = APIRouter(prefix="/api/data", tags=["数据管理"])

# 内存存储：file_id -> file_path
_data_files: dict = {}


def _ensure_upload_dir():
    """确保上传目录存在"""
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_csv(file_path: Path) -> tuple:
    """
    验证 CSV 文件
    
    Returns:
        (rows, columns, error_message)
    """
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path)
        
        # 检查必需列
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return None, None, f"缺少必需列: {missing_cols}"
        
        # 处理时间戳列
        timestamp_col = None
        for col in ["timestamps", "timestamp", "date", "time"]:
            if col in df.columns:
                timestamp_col = col
                break
        
        if timestamp_col:
            df["timestamps"] = pd.to_datetime(df[timestamp_col])
        else:
            return None, None, "未找到时间戳列 (timestamps/timestamp/date/time)"
        
        # 确保数值列为数值类型
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # 检查空值
        if df[required_cols].isnull().any().any():
            return None, None, "数据中存在空值"
        
        return len(df), list(df.columns), None
    
    except Exception as e:
        return None, None, f"读取文件失败: {str(e)}"


@router.get("/files", response_model=dict)
async def list_files():
    """
    获取已上传文件列表
    
    Returns:
        文件列表
    """
    files = []
    for file_id, file_path in _data_files.items():
        if not os.path.exists(file_path):
            continue
        
        stat = os.stat(file_path)
        files.append({
            "file_id": file_id,
            "file_name": os.path.basename(file_path),
            "size": stat.st_size,
            "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    
    return {
        "success": True,
        "files": files,
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    上传数据文件
    
    Args:
        file: CSV 文件
    
    Returns:
        上传结果
    """
    # 验证文件类型
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="只支持 CSV 文件")
    
    # 检查文件大小
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE // 1024 // 1024}MB)"
        )
    
    # 生成文件ID
    file_id = str(uuid.uuid4())
    _ensure_upload_dir()
    
    # 保存文件
    file_path = settings.UPLOAD_DIR / f"{file_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # 验证文件
    rows, columns, error = _validate_csv(file_path)
    if error:
        # 删除无效文件
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=error)
    
    # 存储映射
    _data_files[file_id] = str(file_path)
    
    return {
        "success": True,
        "message": "上传成功",
        "file_id": file_id,
        "file_name": file.filename,
        "rows": rows,
    }


@router.get("/{file_id}")
async def get_file_info(file_id: str):
    """
    获取文件详情
    
    Args:
        file_id: 文件ID
    
    Returns:
        文件信息
    """
    file_path = _data_files.get(file_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    import pandas as pd
    
    df = pd.read_csv(file_path)
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    
    return {
        "success": True,
        "file_id": file_id,
        "file_name": os.path.basename(file_path),
        "rows": len(df),
        "columns": list(df.columns),
        "time_range": {
            "start": df["timestamps"].min().isoformat(),
            "end": df["timestamps"].max().isoformat(),
        },
        "preview": {
            "head": df.head(5).to_dict(orient="records"),
            "tail": df.tail(5).to_dict(orient="records"),
        },
    }


@router.get("/{file_id}/data")
async def get_file_data(file_id: str, rows: int = 0):
    """
    获取文件数据
    
    Args:
        file_id: 文件ID
        rows: 返回行数 (0 表示全部)
    
    Returns:
        文件数据
    """
    file_path = _data_files.get(file_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    import pandas as pd
    
    df = pd.read_csv(file_path)
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    
    if rows > 0:
        df = df.tail(rows)
    
    return {
        "success": True,
        "data": df.to_dict(orient="records"),
    }


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    删除文件
    
    Args:
        file_id: 文件ID
    """
    file_path = _data_files.get(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    del _data_files[file_id]
    
    return {
        "success": True,
        "message": "删除成功",
    }


def get_file_path(file_id: str) -> str:
    """获取文件路径"""
    return _data_files.get(file_id, "")


def get_file_dataframe(file_id: str) -> "pd.DataFrame":
    """获取文件数据为 DataFrame"""
    import pandas as pd
    
    file_path = _data_files.get(file_id)
    if not file_path:
        raise ValueError(f"文件不存在: {file_id}")
    
    df = pd.read_csv(file_path)
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    return df
