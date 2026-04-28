// Kronos 金融预测 Web 应用 - API 类型定义

// ============ 通用类型 ============

export interface BaseResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

// ============ 模型相关类型 ============

export interface ModelInfo {
  key: string;
  name: string;
  model_id: string;
  tokenizer_id: string;
  context_length: number;
  params: string;
  description: string;
}

export interface LoadModelRequest {
  model_key: string;
  device?: string;
}

export interface LoadModelResponse {
  success: boolean;
  message: string;
  model_info?: ModelInfo;
}

export interface ModelStatusResponse {
  success: boolean;
  loaded: boolean;
  current_model?: string;
  device?: string;
}

// ============ 数据相关类型 ============

export interface DataFileInfo {
  file_id: string;
  file_name: string;
  file_path?: string;
  size: number;
  rows: number;
  columns: string[];
  time_range?: {
    start: string;
    end: string;
  };
  uploaded_at?: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  file_id: string;
  file_name: string;
  rows: number;
}

export interface FilePreview {
  head: Record<string, any>[];
  tail: Record<string, any>[];
}

// ============ 预测相关类型 ============

export interface PredictionParams {
  lookback: number;
  pred_len: number;
  temperature: number;
  top_p: number;
  sample_count: number;
  start_date?: string;
}

export interface PredictionPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PredictionStatistics {
  avg_close: number;
  max_close: number;
  min_close: number;
  volatility: number;
}

export interface PredictionRequest {
  file_id: string;
  params: PredictionParams;
}

export interface PredictionResponse {
  success: boolean;
  message: string;
  predictions: PredictionPoint[];
  statistics: PredictionStatistics;
  execution_time: number;
}

export interface AsyncPredictResponse {
  success: boolean;
  message: string;
  task_id: string;
  status: string;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  error?: string;
}

export interface TaskResult {
  task_id: string;
  status: string;
  result?: {
    predictions: PredictionPoint[];
    chart_config: Record<string, any>;
    statistics: PredictionStatistics;
  };
  error?: string;
  execution_time?: number;
}

export interface PredictionHistoryItem {
  task_id: string;
  file_id: string;
  params: PredictionParams;
  status: string;
  created_at: string;
  execution_time?: number;
}

// ============ 默认值 ============

export const DEFAULT_PARAMS: PredictionParams = {
  lookback: 400,
  pred_len: 120,
  temperature: 0.8,
  top_p: 0.9,
  sample_count: 1,
};
