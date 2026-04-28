/**
 * Kronos 金融预测 Web 应用 - 参数面板组件
 */

import React from 'react';
import type { PredictionParams } from '../types/api';

interface ParameterPanelProps {
  params: PredictionParams;
  onChange: (params: PredictionParams) => void;
  maxLookback: number;
  disabled?: boolean;
}

const ParameterPanel: React.FC<ParameterPanelProps> = ({
  params,
  onChange,
  maxLookback,
  disabled,
}) => {
  const handleChange = (key: keyof PredictionParams, value: number) => {
    onChange({ ...params, [key]: value });
  };

  return (
    <div>
      {/* 回看窗口 */}
      <div className="slider-container">
        <div className="slider-header">
          <span className="slider-label">回看窗口</span>
          <span className="slider-value">{params.lookback}</span>
        </div>
        <input
          type="range"
          className="slider"
          min={100}
          max={maxLookback}
          step={10}
          value={params.lookback}
          onChange={(e) => handleChange('lookback', Number(e.target.value))}
          disabled={disabled}
        />
        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
          100 - {maxLookback} (历史数据点数)
        </div>
      </div>

      {/* 预测长度 */}
      <div className="slider-container">
        <div className="slider-header">
          <span className="slider-label">预测长度</span>
          <span className="slider-value">{params.pred_len}</span>
        </div>
        <input
          type="range"
          className="slider"
          min={1}
          max={256}
          step={10}
          value={params.pred_len}
          onChange={(e) => handleChange('pred_len', Number(e.target.value))}
          disabled={disabled}
        />
        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
          1 - 256 (预测时间点数)
        </div>
      </div>

      {/* 采样温度 */}
      <div className="slider-container">
        <div className="slider-header">
          <span className="slider-label">采样温度</span>
          <span className="slider-value">{params.temperature.toFixed(2)}</span>
        </div>
        <input
          type="range"
          className="slider"
          min={0.1}
          max={1.0}
          step={0.05}
          value={params.temperature}
          onChange={(e) => handleChange('temperature', Number(e.target.value))}
          disabled={disabled}
        />
        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
          0.1 - 1.0 (越低越确定，越高越随机)
        </div>
      </div>

      {/* Nucleus 采样概率 */}
      <div className="slider-container">
        <div className="slider-header">
          <span className="slider-label">Nucleus 采样</span>
          <span className="slider-value">{params.top_p.toFixed(2)}</span>
        </div>
        <input
          type="range"
          className="slider"
          min={0.5}
          max={1.0}
          step={0.05}
          value={params.top_p}
          onChange={(e) => handleChange('top_p', Number(e.target.value))}
          disabled={disabled}
        />
        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
          0.5 - 1.0 (累积概率阈值)
        </div>
      </div>

      {/* 采样路径数 */}
      <div className="slider-container">
        <div className="slider-header">
          <span className="slider-label">采样路径数</span>
          <span className="slider-value">{params.sample_count}</span>
        </div>
        <input
          type="range"
          className="slider"
          min={1}
          max={10}
          step={1}
          value={params.sample_count}
          onChange={(e) => handleChange('sample_count', Number(e.target.value))}
          disabled={disabled}
        />
        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
          1 - 10 (越多越稳定，速度越慢)
        </div>
      </div>
    </div>
  );
};

export default ParameterPanel;