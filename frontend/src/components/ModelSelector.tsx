/**
 * Kronos 金融预测 Web 应用 - 模型选择器组件
 */

import React from 'react';
import type { ModelInfo } from '../types/api';

interface ModelSelectorProps {
  models: ModelInfo[];
  currentModel?: string;
  onLoadModel: (modelKey: string) => void;
  loading: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  currentModel,
  onLoadModel,
  loading,
}) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <select
        className="form-input"
        style={{ width: 180 }}
        disabled={loading}
        value={currentModel || ''}
        onChange={(e) => {
          if (e.target.value) {
            onLoadModel(e.target.value);
          }
        }}
      >
        <option value="">选择模型...</option>
        {models.map((model) => (
          <option key={model.key} value={model.key}>
            {model.name} ({model.params})
          </option>
        ))}
      </select>
      {loading && <span className="spinner" style={{ width: 16, height: 16 }} />}
    </div>
  );
};

export default ModelSelector;