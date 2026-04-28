# Kronos 金融预测 Web 应用

基于 Kronos 金融模型的 Web 预测平台，支持 K 线图可视化、参数调节、批量预测等功能。

## 技术栈

- **后端**：FastAPI + Python
- **前端**：React + TypeScript + ECharts
- **模型**：Kronos-small (CPU 推理优化)

## 快速启动

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动后端服务

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 4. 启动前端服务（新终端）

```bash
cd frontend
npm run dev
```

### 5. 访问应用

打开浏览器访问 **http://localhost:5173**

## 项目结构

```
├── backend/              # FastAPI 后端
│   ├── main.py         # 应用入口
│   ├── config.py       # 配置文件
│   ├── routers/        # API 路由
│   ├── services/       # 业务逻辑
│   └── models/         # 数据模型
│
├── frontend/            # React 前端
│   ├── src/
│   │   ├── App.tsx     # 主组件
│   │   ├── api/        # API 客户端
│   │   ├── components/ # UI 组件
│   │   └── types/      # TypeScript 类型
│   └── package.json
│
├── docs/                # 项目文档
├── scripts/              # 测试脚本
└── data/                 # 数据目录
```

## 核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/models/load | 加载模型 |
| POST | /api/data/upload | 上传 CSV |
| POST | /api/predict/async | 异步预测 |
| GET | /api/predict/{id} | 查询结果 |

完整 API 文档：http://localhost:8000/docs
