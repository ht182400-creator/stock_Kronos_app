/**
 * Kronos 金融预测 Web 应用 - 主应用组件
 */

import React, { useState, useEffect, useCallback } from 'react';
import { modelApi, dataApi, predictApi, healthCheck } from './api/client';
import type { ModelInfo, ModelStatusResponse, DataFileInfo, TaskResult, PredictionParams } from './types/api';
import { DEFAULT_PARAMS } from './types/api';
import KLineChart from './components/KLineChart';
import ParameterPanel from './components/ParameterPanel';
import PredictionTable from './components/PredictionTable';
import ModelSelector from './components/ModelSelector';
import FileUpload from './components/FileUpload';

const App: React.FC = () => {
  // 状态
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [modelStatus, setModelStatus] = useState<ModelStatusResponse | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [files, setFiles] = useState<DataFileInfo[]>([]);
  const [selectedFile, setSelectedFile] = useState<DataFileInfo | null>(null);
  const [params, setParams] = useState<PredictionParams>(DEFAULT_PARAMS);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [predicting, setPredicting] = useState(false);

  // 初始化加载
  useEffect(() => {
    const init = async () => {
      try {
        // 健康检查
        const isHealthy = await healthCheck();
        setConnected(isHealthy);

        if (isHealthy) {
          // 获取模型列表
          const modelList = await modelApi.getAvailableModels();
          setModels(modelList);

          // 获取模型状态
          const status = await modelApi.getModelStatus();
          setModelStatus(status);

          // 获取文件列表
          const fileList = await dataApi.getFiles();
          setFiles(fileList);
        }
      } catch (error) {
        console.error('初始化失败:', error);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  // 轮询任务状态
  useEffect(() => {
    if (!taskId || taskResult?.status === 'completed' || taskResult?.status === 'failed') {
      return;
    }

    const pollStatus = async () => {
      try {
        const result = await predictApi.getTaskResult(taskId);
        setTaskResult(result);

        if (result.status === 'completed' || result.status === 'failed') {
          setPredicting(false);
        }
      } catch (error) {
        console.error('获取任务状态失败:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [taskId, taskResult?.status]);

  // 加载模型
  const handleLoadModel = useCallback(async (modelKey: string) => {
    try {
      setLoading(true);
      await modelApi.loadModel({ model_key: modelKey, device: 'cpu' });
      const status = await modelApi.getModelStatus();
      setModelStatus(status);
    } catch (error) {
      console.error('加载模型失败:', error);
      alert('模型加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 选择文件（获取完整信息）
  const handleSelectFile = useCallback(async (file: DataFileInfo | null) => {
    if (!file) {
      setSelectedFile(null);
      return;
    }
    try {
      const fileInfo = await dataApi.getFileInfo(file.file_id);
      setSelectedFile({ ...file, ...fileInfo });
    } catch (error) {
      console.error('获取文件信息失败:', error);
      setSelectedFile(file);
    }
  }, []);

  // 上传文件
  const handleUpload = useCallback(async (file: File) => {
    try {
      setLoading(true);
      const response = await dataApi.uploadFile(file);
      if (response.success) {
        // 获取完整文件信息（包含 preview）
        const fileInfo = await dataApi.getFileInfo(response.file_id);
        
        // 更新文件列表：合并基本信息 + 完整信息（含 preview）
        const newFile = { ...response, ...fileInfo };
        setFiles(prev => [newFile, ...prev]);
        
        // 选中新上传的文件
        setSelectedFile(newFile);
      }
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 执行预测
  const handlePredict = useCallback(async () => {
    if (!selectedFile || !modelStatus?.loaded) {
      alert('请先选择数据文件并加载模型');
      return;
    }

    try {
      setPredicting(true);
      setTaskResult(null);

      const response = await predictApi.predictAsync({
        file_id: selectedFile.file_id,
        params,
      });

      if (response.success) {
        setTaskId(response.task_id);
      }
    } catch (error) {
      console.error('预测失败:', error);
      alert('预测失败');
      setPredicting(false);
    }
  }, [selectedFile, modelStatus?.loaded, params]);

  // 加载状态
  if (loading && !connected) {
    return (
      <div className="app-container">
        <div className="loading">
          <div className="spinner"></div>
          正在连接服务器...
        </div>
      </div>
    );
  }

  // 未连接状态
  if (!connected) {
    return (
      <div className="app-container">
        <header className="header">
          <div className="header-logo">
            <h1>Kronos 金融预测平台</h1>
          </div>
        </header>
        <main className="main-content">
          <div className="card">
            <div className="empty-state">
              <div className="empty-state-icon">⚠️</div>
              <h2>无法连接到后端服务</h2>
              <p>请确保后端服务正在运行 (http://localhost:8000)</p>
              <button className="btn btn-primary" onClick={() => window.location.reload()}>
                重试连接
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* 头部 */}
      <header className="header">
        <div className="header-logo">
          <h1>Kronos 金融预测平台</h1>
        </div>
        <div className="header-actions">
          <ModelSelector
            models={models}
            currentModel={modelStatus?.current_model}
            onLoadModel={handleLoadModel}
            loading={loading}
          />
          <div className={`status-badge ${modelStatus?.loaded ? 'success' : 'warning'}`}>
            <span>{modelStatus?.loaded ? '●' : '○'}</span>
            {modelStatus?.loaded ? '模型已加载' : '模型未加载'}
          </div>
        </div>
      </header>

      {/* 主内容 */}
      <main className="main-content">
        <div className="grid grid-3">
          {/* 模型/文件信息卡片 */}
          <div className="card">
            <h3 className="card-title">数据选择</h3>
            <FileUpload
              files={files}
              selectedFile={selectedFile}
              onUpload={handleUpload}
              onSelect={handleSelectFile}
              loading={loading}
            />
          </div>

          {/* 参数面板 */}
          <div className="card">
            <h3 className="card-title">预测参数</h3>
            <ParameterPanel
              params={params}
              onChange={setParams}
              maxLookback={512}
              disabled={predicting}
            />
          </div>

          {/* 状态/操作卡片 */}
          <div className="card">
            <h3 className="card-title">执行预测</h3>
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 14, color: '#666', marginBottom: 16 }}>
                {selectedFile
                  ? `已选择: ${selectedFile.file_name} (${selectedFile.rows} 行)`
                  : '请先选择数据文件'}
              </p>
              {predicting && taskResult && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 14, marginBottom: 8 }}>
                    预测进度: {taskResult.progress || 0}%
                  </div>
                  <div
                    style={{
                      height: 8,
                      background: '#e8e8e8',
                      borderRadius: 4,
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${taskResult.progress || 0}%`,
                        background: '#1890ff',
                        transition: 'width 0.3s',
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
            <button
              className="btn btn-primary"
              onClick={handlePredict}
              disabled={!selectedFile || !modelStatus?.loaded || predicting}
              style={{ width: '100%' }}
            >
              {predicting ? '预测中...' : '开始预测'}
            </button>
          </div>
        </div>

        {/* 图表 */}
        <div className="card">
          <h3 className="card-title">预测结果</h3>
          {taskResult?.result ? (
            <KLineChart config={taskResult.result.chart_config} />
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📈</div>
              <p>{predicting ? '预测进行中，请稍候...' : '暂无预测结果'}</p>
            </div>
          )}
        </div>

        {/* 数据表格 */}
        {taskResult?.result && (
          <div className="card">
            <h3 className="card-title">预测数据</h3>
            <PredictionTable
              data={taskResult.result.predictions}
              statistics={taskResult.result.statistics}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default App;