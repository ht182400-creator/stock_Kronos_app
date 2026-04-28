#!/usr/bin/env python3
"""
Kronos Web 应用测试脚本

使用方法:
    python scripts/test_api.py
"""

import sys
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
SAMPLE_DATA = Path(__file__).parent.parent / "data" / "samples" / "sample_data.csv"


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_health():
    """检查服务健康状态"""
    print_section("1. 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✓ 服务运行正常")
            print(f"  响应: {response.json()}")
            return True
        else:
            print(f"✗ 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 无法连接服务: {e}")
        print(f"  请确保后端服务正在运行: python -m uvicorn main:app --reload --port 8000")
        return False


def get_models():
    """获取可用模型"""
    print_section("2. 获取可用模型")
    try:
        response = requests.get(f"{BASE_URL}/api/models")
        data = response.json()
        if data.get("success"):
            for model in data.get("models", []):
                print(f"  • {model['name']} ({model['params']}) - {model['description']}")
            return data.get("models", [])
        else:
            print(f"✗ 获取模型失败: {data}")
            return []
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return []


def load_model(model_key: str = "kronos-small"):
    """加载模型"""
    print_section(f"3. 加载模型: {model_key}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/models/load",
            json={"model_key": model_key, "device": "cpu"}
        )
        data = response.json()
        if data.get("success"):
            print(f"✓ 模型加载成功")
            print(f"  消息: {data.get('message')}")
            return True
        else:
            print(f"✗ 模型加载失败: {data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def check_model_status():
    """检查模型状态"""
    print_section("4. 检查模型状态")
    try:
        response = requests.get(f"{BASE_URL}/api/models/status")
        data = response.json()
        if data.get("loaded"):
            print(f"✓ 模型已加载")
            print(f"  当前模型: {data.get('current_model')}")
            print(f"  设备: {data.get('device')}")
            return True
        else:
            print("✗ 模型未加载")
            return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def upload_file(file_path: Path):
    """上传文件"""
    print_section(f"5. 上传文件: {file_path.name}")
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/api/data/upload",
                files={"file": f}
            )
        data = response.json()
        if data.get("success"):
            print(f"✓ 文件上传成功")
            print(f"  File ID: {data.get('file_id')}")
            print(f"  行数: {data.get('rows')}")
            return data.get("file_id")
        else:
            print(f"✗ 上传失败: {data.get('detail', data)}")
            return None
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return None


def run_prediction(file_id: str, use_async: bool = True):
    """执行预测"""
    mode = "异步" if use_async else "同步"
    print_section(f"6. 执行{mode}预测")
    
    params = {
        "file_id": file_id,
        "params": {
            "lookback": 20,
            "pred_len": 5,
            "temperature": 0.8,
            "top_p": 0.9,
            "sample_count": 1
        }
    }
    
    try:
        if use_async:
            # 异步预测
            response = requests.post(
                f"{BASE_URL}/api/predict/async",
                json=params
            )
            data = response.json()
            if not data.get("success"):
                print(f"✗ 提交任务失败: {data.get('detail', data)}")
                return None
            
            task_id = data.get("task_id")
            print(f"✓ 任务已提交")
            print(f"  Task ID: {task_id}")
            
            # 轮询结果
            print("\n  轮询任务状态...")
            while True:
                time.sleep(1)
                result_response = requests.get(f"{BASE_URL}/api/predict/{task_id}")
                result = result_response.json()
                
                status = result.get("status")
                if status == "completed":
                    print(f"\n✓ 预测完成!")
                    print_result(result.get("result", {}))
                    return result.get("result")
                elif status == "failed":
                    print(f"\n✗ 预测失败: {result.get('error')}")
                    return None
                else:
                    progress = result.get("progress", 0)
                    print(f"  进度: {progress}%", end="\r")
        else:
            # 同步预测
            response = requests.post(
                f"{BASE_URL}/api/predict",
                json=params,
                timeout=120  # 2分钟超时
            )
            data = response.json()
            if data.get("success"):
                print(f"✓ 预测完成!")
                print_result({
                    "predictions": data.get("predictions", []),
                    "statistics": data.get("statistics", {})
                })
                return data
            else:
                print(f"✗ 预测失败: {data.get('detail', data)}")
                return None
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return None


def print_result(result: dict):
    """打印预测结果"""
    if not result:
        return
    
    predictions = result.get("predictions", [])
    statistics = result.get("statistics", {})
    
    if predictions:
        print("\n  预测数据:")
        for i, pred in enumerate(predictions[:5]):  # 只显示前5条
            print(f"    {i+1}. {pred.get('timestamp')}: "
                  f"O={pred.get('open', 0):.4f} "
                  f"H={pred.get('high', 0):.4f} "
                  f"L={pred.get('low', 0):.4f} "
                  f"C={pred.get('close', 0):.4f}")
        if len(predictions) > 5:
            print(f"    ... (共 {len(predictions)} 条)")
    
    if statistics:
        print("\n  统计信息:")
        print(f"    平均收盘价: {statistics.get('avg_close', 0):.4f}")
        print(f"    最高收盘价: {statistics.get('max_close', 0):.4f}")
        print(f"    最低收盘价: {statistics.get('min_close', 0):.4f}")
        print(f"    波动率: {(statistics.get('volatility', 0) * 100):.2f}%")
    
    if "execution_time" in result:
        print(f"\n  执行时间: {result.get('execution_time', 0):.2f} 秒")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  Kronos Web API 测试脚本")
    print("="*60)
    
    # 1. 检查服务
    if not check_health():
        sys.exit(1)
    
    # 2. 获取模型列表
    models = get_models()
    if not models:
        print("\n无法获取模型列表，请检查服务状态")
        sys.exit(1)
    
    # 3. 加载模型
    if not load_model("kronos-small"):
        print("\n模型加载失败，请检查 Kronos 依赖")
        sys.exit(1)
    
    # 4. 检查模型状态
    if not check_model_status():
        sys.exit(1)
    
    # 5. 检查测试数据
    if not SAMPLE_DATA.exists():
        print(f"\n⚠ 警告: 测试数据不存在: {SAMPLE_DATA}")
        print("  请复制 Kronos 示例数据或创建自己的 CSV 文件")
        sample_from_kronos = Path("D:/Work_Area/Kronos/examples/data/XSHG_5min_600977.csv")
        if sample_from_kronos.exists():
            print(f"  找到 Kronos 示例数据: {sample_from_kronos}")
            print("  建议复制到 data/samples/ 目录")
    
    # 6. 上传文件并预测
    if SAMPLE_DATA.exists():
        file_id = upload_file(SAMPLE_DATA)
        if file_id:
            result = run_prediction(file_id, use_async=True)
            if result:
                print("\n✓ 测试完成!")
            else:
                print("\n⚠ 预测执行失败，请检查错误信息")
    else:
        print("\n⚠ 跳过预测测试（缺少测试数据）")
    
    print("\n" + "="*60)
    print("  测试结束")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
