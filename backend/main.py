"""
Kronos 金融预测 Web 应用 - FastAPI 主入口
"""

import sys
from pathlib import Path

# 添加 Kronos 源码路径
from config import settings

# 确保 Kronos 源码在 Python 路径中
if str(settings.KRONOS_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(settings.KRONOS_REPO_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from routers import model_router, data_router, predict_router

# 创建 FastAPI 应用
app = FastAPI(
    title="Kronos 金融预测 API",
    description="""
    基于 Kronos Foundation Model 的金融 K 线预测服务。
    
    ## 功能
    
    * **模型管理** - 加载和管理 Kronos 模型
    * **数据管理** - 上传和管理 K 线数据文件
    * **价格预测** - 使用 Kronos 进行 K 线价格预测
    
    ## 模型
    
    * Kronos-mini - 轻量级，CPU 推理首选
    * Kronos-small - 平衡型，性能与速度兼顾
    * Kronos-base - 高质量，需要较强算力
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
            }
        }
    )


# 注册路由
app.include_router(model_router)
app.include_router(data_router)
app.include_router(predict_router)


@app.get("/", tags=["首页"])
async def root():
    """首页"""
    return {
        "name": "Kronos 金融预测 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "kronos-webapp",
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 确保上传目录存在
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 50)
    print("Kronos 金融预测 Web 应用启动中...")
    print(f"Kronos 源码路径: {settings.KRONOS_REPO_DIR}")
    print(f"上传目录: {settings.UPLOAD_DIR}")
    print("=" * 50)


# 允许直接运行
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
