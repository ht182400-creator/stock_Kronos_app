# Kronos 金融预测 Web 应用 - API 接口文档

## 概述

本应用提供 RESTful API 接口，用于管理 Kronos 模型、数据文件和执行预测。

**基础 URL**: `http://localhost:8000`

**API 文档**: `http://localhost:8000/docs` (Swagger UI)

---

## 认证

当前版本无需认证，请在生产环境中自行添加。

---

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

---

## 接口列表

### 1. 健康检查

**GET** `/api/health`

检查服务是否正常运行。

**响应示例**:
```json
{
  "status": "healthy",
  "service": "kronos-webapp"
}
```

---

### 2. 模型管理

#### 2.1 获取可用模型列表

**GET** `/api/models`

获取支持的 Kronos 模型列表。

**响应示例**:
```json
{
  "success": true,
  "models": [
    {
      "key": "kronos-mini",
      "name": "Kronos-mini",
      "model_id": "NeoQuasar/Kronos-mini",
      "tokenizer_id": "NeoQuasar/Kronos-Tokenizer-2k",
      "context_length": 2048,
      "params": "4.1M",
      "description": "轻量级模型，适合快速预测"
    }
  ]
}
```

#### 2.2 加载模型

**POST** `/api/models/load`

加载指定的 Kronos 模型。

**请求体**:
```json
{
  "model_key": "kronos-mini",
  "device": "cpu"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_key | string | 否 | 模型标识，默认 "kronos-mini" |
| device | string | 否 | 设备，"cpu" 或 "cuda:0"，默认 "cpu" |

**响应示例**:
```json
{
  "success": true,
  "message": "模型 Kronos-mini 加载成功",
  "model_info": {
    "key": "kronos-mini",
    "name": "Kronos-mini",
    "params": "4.1M",
    "context_length": 2048
  }
}
```

#### 2.3 获取模型状态

**GET** `/api/models/status`

获取当前模型加载状态。

**响应示例**:
```json
{
  "success": true,
  "loaded": true,
  "current_model": "kronos-mini",
  "device": "cpu"
}
```

---

### 3. 数据管理

#### 3.1 获取文件列表

**GET** `/api/data/files`

获取已上传的文件列表。

**响应示例**:
```json
{
  "success": true,
  "files": [
    {
      "file_id": "uuid-string",
      "file_name": "data.csv",
      "size": 102400,
      "uploaded_at": "2024-01-01T12:00:00"
    }
  ]
}
```

#### 3.2 上传文件

**POST** `/api/data/upload`

上传 K 线数据 CSV 文件。

**请求**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | CSV 文件，最大 50MB |

**CSV 文件格式**:
```csv
timestamps,open,high,low,close,volume,amount
2024-06-18 11:15:00,11.27,11.28,11.26,11.27,379.0,427161.0
```

**响应示例**:
```json
{
  "success": true,
  "message": "上传成功",
  "file_id": "uuid-string",
  "file_name": "data.csv",
  "rows": 2502
}
```

#### 3.3 获取文件信息

**GET** `/api/data/{file_id}`

获取指定文件的详细信息和预览。

**响应示例**:
```json
{
  "success": true,
  "file_id": "uuid-string",
  "file_name": "data.csv",
  "rows": 2502,
  "columns": ["timestamps", "open", "high", "low", "close", "volume", "amount"],
  "time_range": {
    "start": "2024-06-18T11:15:00",
    "end": "2024-06-28T15:00:00"
  },
  "preview": {
    "head": [...],
    "tail": [...]
  }
}
```

#### 3.4 删除文件

**DELETE** `/api/data/{file_id}`

删除指定的已上传文件。

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

---

### 4. 预测管理

#### 4.1 同步预测

**POST** `/api/predict`

执行同步预测（适合小数据量，CPU 推理约 5-15 秒，使用 Kronos-mini 更快速）。

**请求体**:
```json
{
  "file_id": "uuid-string",
  "params": {
    "lookback": 400,
    "pred_len": 120,
    "temperature": 0.8,
    "top_p": 0.9,
    "sample_count": 1,
    "start_date": "2024-06-18T11:15:00"
  }
}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file_id | string | 是 | - | 文件 ID |
| params.lookback | integer | 否 | 400 | 回看窗口 (100-2048) |
| params.pred_len | integer | 否 | 120 | 预测长度 (1-512) |
| params.temperature | float | 否 | 0.8 | 采样温度 (0.1-1.0) |
| params.top_p | float | 否 | 0.9 | Nucleus 采样 (0.5-1.0) |
| params.sample_count | integer | 否 | 1 | 采样路径数 (1-10) |
| params.start_date | string | 否 | 最新 | 起始日期时间 |

**响应示例**:
```json
{
  "success": true,
  "message": "预测完成",
  "predictions": [
    {
      "timestamp": "2024-06-20T15:00:00",
      "open": 11.27,
      "high": 11.32,
      "low": 11.25,
      "close": 11.29,
      "volume": 456.0
    }
  ],
  "statistics": {
    "avg_close": 11.35,
    "max_close": 11.52,
    "min_close": 11.18,
    "volatility": 0.023
  },
  "execution_time": 15.3
}
```

#### 4.2 异步预测（推荐）

**POST** `/api/predict/async`

提交异步预测任务（推荐使用，防止请求超时）。

**请求体**: 同 4.1

**响应示例**:
```json
{
  "success": true,
  "message": "任务已提交",
  "task_id": "uuid-string",
  "status": "pending"
}
```

#### 4.3 获取任务状态/结果

**GET** `/api/predict/{task_id}`

获取预测任务的状态或结果。

**响应示例（进行中）**:
```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "running",
  "progress": 45
}
```

**响应示例（完成）**:
```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "completed",
  "result": {
    "predictions": [...],
    "chart_config": {...},
    "statistics": {...}
  },
  "execution_time": 15.3
}
```

#### 4.4 获取预测历史

**GET** `/api/predict/history/list`

获取预测历史记录。

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 20 | 返回数量限制 |

**响应示例**:
```json
{
  "success": true,
  "history": [
    {
      "task_id": "uuid-string",
      "file_id": "uuid-string",
      "params": {...},
      "status": "completed",
      "created_at": "2024-01-01T12:00:00",
      "execution_time": 15.3
    }
  ]
}
```

---

## 错误码

| 错误码 | 说明 | HTTP 状态 |
|--------|------|-----------|
| ERR_MODEL_NOT_LOADED | 模型未加载 | 400 |
| ERR_MODEL_LOAD_FAILED | 模型加载失败 | 500 |
| ERR_FILE_NOT_FOUND | 文件不存在 | 404 |
| ERR_FILE_FORMAT_INVALID | 文件格式错误 | 400 |
| ERR_DATA_INSUFFICIENT | 数据不足 | 400 |
| ERR_PREDICTION_FAILED | 预测失败 | 500 |
| ERR_TASK_NOT_FOUND | 任务不存在 | 404 |
| ERR_QUEUE_FULL | 队列已满 | 503 |

---

## 示例代码

### Python (使用 requests)

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. 加载模型
requests.post(f"{BASE_URL}/api/models/load", json={
    "model_key": "kronos-mini",
    "device": "cpu"
})

# 2. 上传文件
with open("data.csv", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/data/upload",
        files={"file": f}
    )
file_id = response.json()["file_id"]

# 3. 异步预测
response = requests.post(f"{BASE_URL}/api/predict/async", json={
    "file_id": file_id,
    "params": {
        "lookback": 400,
        "pred_len": 120
    }
})
task_id = response.json()["task_id"]

# 4. 轮询结果
while True:
    response = requests.get(f"{BASE_URL}/api/predict/{task_id}")
    result = response.json()
    
    if result["status"] == "completed":
        print(result["result"])
        break
    elif result["status"] == "failed":
        print("预测失败:", result["error"])
        break
    
    print(f"进度: {result.get('progress', 0)}%")
    time.sleep(2)
```

### JavaScript (使用 fetch)

```javascript
const BASE_URL = "http://localhost:8000";

// 1. 加载模型
await fetch(`${BASE_URL}/api/models/load`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ model_key: "kronos-mini", device: "cpu" })
});

// 2. 上传文件
const formData = new FormData();
formData.append("file", fileInput.files[0]);
const uploadRes = await fetch(`${BASE_URL}/api/data/upload`, {
  method: "POST",
  body: formData
});
const { file_id } = await uploadRes.json();

// 3. 异步预测
const predictRes = await fetch(`${BASE_URL}/api/predict/async`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ file_id, params: { lookback: 400, pred_len: 120 } })
});
const { task_id } = await predictRes.json();

// 4. 轮询结果
while (true) {
  const result = await fetch(`${BASE_URL}/api/predict/${task_id}`).then(r => r.json());
  
  if (result.status === "completed") {
    console.log(result.result);
    break;
  } else if (result.status === "failed") {
    console.error("预测失败:", result.error);
    break;
  }
  
  console.log(`进度: ${result.progress || 0}%`);
  await new Promise(r => setTimeout(r, 2000));
}
```
