// Kronos 金融预测 Web 应用 - API 客户端

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  BaseResponse,
  ModelInfo,
  LoadModelRequest,
  LoadModelResponse,
  ModelStatusResponse,
  DataFileInfo,
  UploadResponse,
  PredictionRequest,
  PredictionResponse,
  AsyncPredictResponse,
  TaskResult,
  PredictionHistoryItem,
} from '../types/api';

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5分钟超时（模型加载可能较慢）
  headers: {
    'Content-Type': 'application/json',
  },
});

// 错误处理
function handleError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ error?: { message?: string } }>;
    const message = axiosError.response?.data?.error?.message || axiosError.message;
    throw new Error(message);
  }
  throw error;
}

// ============ 模型 API ============

export const modelApi = {
  /**
   * 获取可用模型列表
   */
  async getAvailableModels(): Promise<ModelInfo[]> {
    try {
      const response = await apiClient.get<{ success: boolean; models: ModelInfo[] }>(
        '/api/models'
      );
      return response.data.models || [];
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 加载模型
   */
  async loadModel(request: LoadModelRequest): Promise<LoadModelResponse> {
    try {
      const response = await apiClient.post<LoadModelResponse>(
        '/api/models/load',
        request
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 获取模型状态
   */
  async getModelStatus(): Promise<ModelStatusResponse> {
    try {
      const response = await apiClient.get<ModelStatusResponse>('/api/models/status');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },
};

// ============ 数据 API ============

export const dataApi = {
  /**
   * 获取文件列表
   */
  async getFiles(): Promise<DataFileInfo[]> {
    try {
      const response = await apiClient.get<{ success: boolean; files: DataFileInfo[] }>(
        '/api/data/files'
      );
      return response.data.files || [];
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 上传文件
   */
  async uploadFile(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post<UploadResponse>(
        '/api/data/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000, // 上传文件可能较慢
        }
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 获取文件信息（支持分页）
   */
  async getFileInfo(
    fileId: string,
    page: number = 1,
    pageSize: number = 5
  ): Promise<DataFileInfo & { preview?: any; pagination?: any }> {
    try {
      const response = await apiClient.get(`/api/data/${fileId}`, {
        params: { page, page_size: pageSize },
      });
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 删除文件
   */
  async deleteFile(fileId: string): Promise<void> {
    try {
      await apiClient.delete(`/api/data/${fileId}`);
    } catch (error) {
      handleError(error);
    }
  },
};

// ============ 预测 API ============

export const predictApi = {
  /**
   * 同步预测（适合小数据量）
   */
  async predict(request: PredictionRequest): Promise<PredictionResponse> {
    try {
      const response = await apiClient.post<PredictionResponse>('/api/predict', request);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 异步预测（推荐）
   */
  async predictAsync(request: PredictionRequest): Promise<AsyncPredictResponse> {
    try {
      const response = await apiClient.post<AsyncPredictResponse>(
        '/api/predict/async',
        request
      );
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 获取任务状态/结果
   */
  async getTaskResult(taskId: string): Promise<TaskResult> {
    try {
      const response = await apiClient.get<{
        success: boolean;
        task_id: string;
        status: string;
        progress?: number;
        result?: TaskResult['result'];
        error?: string;
        execution_time?: number;
      }>(`/api/predict/${taskId}`);
      const data = response.data;
      // 移除 success 字段，只返回 TaskResult 需要的字段
      const { success, ...result } = data;
      return result as TaskResult;
    } catch (error) {
      handleError(error);
    }
  },

  /**
   * 获取预测历史
   */
  async getHistory(limit: number = 20): Promise<PredictionHistoryItem[]> {
    try {
      const response = await apiClient.get<{ success: boolean; history: PredictionHistoryItem[] }>(
        '/api/predict/history/list',
        { params: { limit } }
      );
      return response.data.history || [];
    } catch (error) {
      handleError(error);
    }
  },
};

// ============ 健康检查 ============

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await apiClient.get('/api/health');
    return response.data.status === 'healthy';
  } catch {
    return false;
  }
}

export default apiClient;
