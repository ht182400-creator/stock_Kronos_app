# Kronos 金融预测 Web 应用 - 开发过程 FAQ

## 目录

- [界面问题](#界面问题)
- [接口问题](#接口问题)
- [其他问题](#其他问题)
- [历史问题记录](#历史问题记录)

---

## 界面问题

### Q1: 前端页面显示"无法连接到后端服务"

**问题描述**：

刷新页面后仍显示"无法连接到后端服务"。

**原因**：

后端服务未启动。

**解决方案**：

1. 启动后端服务：

```powershell
cd d:/Work_Area/AI/stock_Kronos_app/backend
python -m uvicorn main:app --reload --port 8000
```

2. 确认后端启动成功，看到以下日志：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

3. 刷新前端页面 http://localhost:5173

---

### Q2: 模型下拉框为空，显示"模型未加载"

**问题描述**：

界面右上角显示"模型未加载"，下拉框为空或无选项。

**原因**：

前端 API 请求失败或类型定义不完整。

**解决方案**：

1. 确保后端已启动并正常运行
2. 检查浏览器控制台（F12）是否有报错
3. 已修复 `TaskResult` 类型定义，添加了 `progress` 和 `message` 字段

**界面示例**：

```
┌─────────────────────────────────────────────────────────────┐
│  Kronos 金融预测平台              [选择模型 ▼] ●模型未加载  │
└─────────────────────────────────────────────────────────────┘
                                    ↓
刷新后显示：
┌─────────────────────────────────────────────────────────────┐
│  Kronos 金融预测平台    [Kronos-mini (4.1M) ▼] ●模型已加载  │
└─────────────────────────────────────────────────────────────┘
```

---

### Q3: 预测按钮不可点击

**问题描述**：

"开始预测"按钮显示为灰色，不可点击。

**原因**：

未满足以下条件之一：
- 模型未加载
- 未选择数据文件

**解决方案**：

1. 先在右上角选择并加载模型
2. 上传或选择数据文件
3. 两个条件都满足后按钮变蓝可用

---

## 接口问题

### Q4: `/api/models` 接口返回成功但前端不显示模型列表

**问题描述**：

后端接口正常返回，但前端下拉框为空。

**原因**：

前端 `TaskResult` 类型缺少 `progress` 字段。

**解决方案**：

更新 `frontend/src/types/api.ts` 中的 `TaskResult` 接口：

```typescript
// 修复前
export interface TaskResult {
  task_id: string;
  status: string;
  result?: { ... };
  error?: string;
  execution_time?: number;
}

// 修复后
export interface TaskResult {
  task_id: string;
  status: string;
  progress?: number;      // 新增
  result?: { ... };
  error?: string;
  execution_time?: number;
  message?: string;       // 新增
}
```

---

### Q5: 预测接口返回"模型未加载"

**接口信息**：

```http
POST /api/predict/async
```

**问题描述**：

调用预测接口时返回 400 错误。

**响应示例**：

```json
{
  "detail": "模型未加载，请先调用 POST /api/models/load"
}
```

**解决方案**：

1. 先调用模型加载接口：

```http
POST /api/models/load
Content-Type: application/json

{
  "model_key": "kronos-mini",
  "device": "cpu"
}
```

2. 确认模型加载成功后再调用预测接口

---

### Q6: 上传 CSV 文件格式要求

**接口信息**：

```http
POST /api/data/upload
Content-Type: multipart/form-data
```

**问题描述**：

上传文件后报错或数据解析失败。

**原因**：

CSV 文件格式不符合要求。

**解决方案**：

确保 CSV 文件包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| timestamps | datetime | 时间戳 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| volume | float | 成交量 |
| amount | float | 成交额 |

**示例 CSV**：

```csv
timestamps,open,high,low,close,volume,amount
2024-01-01 09:30:00,100.0,105.0,99.0,103.0,10000,1030000
2024-01-01 09:31:00,103.0,104.0,102.0,102.5,8000,820000
...
```

---

## 其他问题

### Q7: npm install 报废弃警告

**问题描述**：

安装依赖时出现多个 npm warn deprecated 警告。

**警告示例**：

```
npm warn deprecated inflight@1.0.6: This module is not supported
npm warn deprecated @humanwhocodes/config-array@0.13.0: Use @eslint/config-array instead
npm warn deprecated rimraf@3.0.2: Rimraf versions prior to v4 are no longer supported
```

**解决方案**：

这些只是废弃警告，**不影响项目运行**，可以忽略。

如需消除警告，可升级依赖：

```powershell
npm install -g npm@latest
npm install eslint@latest
```

---

### Q8: 预测执行时间过长

**问题描述**：

CPU 推理时间超过 60 秒仍未完成。

**原因**：

CPU 推理本身较慢，尤其是首次推理需要模型预热。

**解决方案**：

1. 使用异步预测接口 `/api/predict/async`
2. 页面会自动轮询任务状态，显示进度
3. 首次预测建议耐心等待（10-30 秒）
4. 可以使用较小的 `pred_len` 参数减少推理时间

---

### Q9: 后端启动报错 ImportError

**问题描述**：

启动后端时报 ImportError 错误。

**解决方案**：

1. 安装所有依赖：

```powershell
cd d:/Work_Area/AI/stock_Kronos_app/backend
pip install -r requirements.txt
```

2. 确保 Kronos 源码路径正确，编辑 `config.py`：

```python
KRONOS_REPO_DIR: Path = Path("D:/Work_Area/Kronos")  # 修改为实际路径
```

---

## 历史问题记录

| 日期 | 时间 | 问题 | 解决方案 | 状态 |
|------|------|------|----------|------|
| 2026-04-28 | 16:24 | npm install 报 deprecated 警告 | 确认不影响运行，可忽略 | ✅ 已解决 |
| 2026-04-28 | 16:26 | 前端显示"模型未加载" | 修复 TaskResult 类型定义 | ✅ 已解决 |
| 2026-04-28 | 16:30 | 页面显示"无法连接后端" | 确认后端服务未启动 | ✅ 已解决 |
| 2026-04-28 | 16:44 | 模型列表下拉框为空 | 添加 ModelListResponse 模型修复返回格式 | ✅ 已解决 |
| 2026-04-28 | 21:40 | 模型加载失败 ResponseValidationError | 在 kronos_service.py 中为 model_info 添加 key 字段 | ✅ 已解决 |


---

### Q10: 模型列表 API 返回缺少 models 字段

**问题描述**：

调用 `/api/models` 接口时，返回的数据缺少 `models` 字段。

**错误响应示例**：

```json
{
  "success": true,
  "message": "获取成功"
}
```

**原因**：

路由使用了 `response_model=BaseResponse`，但 `BaseResponse` 只定义了 `success` 和 `message` 字段，导致 `models` 字段被 FastAPI 过滤掉。

**解决方案**：

1. 在 `backend/models/schemas.py` 中添加新的响应模型：

```python
class ModelListResponse(BaseModel):
    """模型列表响应"""
    success: bool = True
    message: str = "操作成功"
    models: list = []
```

2. 在 `backend/routers/model.py` 中导入并使用：

```python
from models.schemas import (
    ModelInfo,
    LoadModelRequest,
    LoadModelResponse,
    ModelStatusResponse,
    ModelListResponse,  # 新增
    BaseResponse,
)

@router.get("", response_model=ModelListResponse)  # 改为使用 ModelListResponse
async def get_available_models():
    ...
```

3. 重启后端服务

---

### Q11: 模型加载失败 ResponseValidationError: Field required key

**问题描述**：

点击"加载模型"按钮后，界面提示"模型加载失败"，后端报错：

```
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'missing', 'loc': ('response', 'model_info', 'key'), 'msg': 'Field required'}
```

**错误响应示例**：

```json
{
  "success": true,
  "message": "模型 Kronos-mini 加载成功",
  "model_info": {
    "name": "Kronos-mini",
    "model_id": "NeoQuasar/Kronos-mini",
    "tokenizer_id": "NeoQuasar/Kronos-Tokenizer-2k",
    "context_length": 2048,
    "params": "4.1M",
    "description": "轻量级模型，适合快速预测，CPU 推理首选",
    "local_model_path": "D:/Work_Area/AI/stock_Kronos_app/model/Kronos-min",
    "local_tokenizer_path": "D:/Work_Area/AI/stock_Kronos_app/model/Kronos-Tokenizer-2k"
  }
}
```

**原因**：

`ModelInfo` Pydantic 模型定义了 `key: str` 字段为必填，但 `kronos_service.py` 返回的 `model_info` 来自 `AVAILABLE_MODELS` 配置，缺少 `key` 字段。

**解决方案**：

在 `backend/services/kronos_service.py` 中，修改返回 `model_info` 时添加 `key` 字段：

```python
# 修复位置1：模型已加载时
if self._predictor is not None:
    if self._current_model_key == model_key and self._device == device:
        return {
            "success": True,
            "message": "模型已加载",
            "model_info": {**AVAILABLE_MODELS[model_key], "key": model_key},  # 添加 key
        }

# 修复位置2：模型加载成功后
return {
    "success": True,
    "message": f"模型 {model_config['name']} 加载成功",
    "model_info": {**model_config, "key": model_key},  # 添加 key
}
```

**相关文件**：

- `backend/services/kronos_service.py` - 第 79-83 行、第 115-119 行
- `backend/models/schemas.py` - `ModelInfo` 类定义

---

## 快速故障排除清单

1. **后端无法启动** → 检查依赖安装和 Python 环境
2. **前端无法访问** → 检查 npm install 和 npm run dev
3. **模型加载失败** → 检查 Kronos 源码路径配置
4. **预测失败** → 检查 CSV 文件格式和数据量
5. **接口报错** → 查看后端控制台日志或 Swagger 文档

---

## 相关资源

- 后端 API 文档：http://localhost:8000/docs
- 前端开发服务器：http://localhost:5173
- 项目文档：[01_需求规格说明书.md](./01_需求规格说明书.md)
- 架构设计：[02_架构设计.md](./02_架构设计.md)
- 接口文档：[03_API接口文档.md](./03_API接口文档.md)
- 启动指南：[04_快速启动指南.md](./04_快速启动指南.md)
