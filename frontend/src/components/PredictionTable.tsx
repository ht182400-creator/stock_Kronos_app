/**
 * Kronos 金融预测 Web 应用 - 预测表格组件
 */

import React, { useState } from 'react';
import type { PredictionPoint, PredictionStatistics } from '../types/api';

interface PredictionTableProps {
  data: PredictionPoint[];
  statistics: PredictionStatistics;
}

const PredictionTable: React.FC<PredictionTableProps> = ({ data, statistics }) => {
  const [exportFormat, setExportFormat] = useState<'csv' | 'json' | null>(null);

  // 导出 CSV
  const exportCSV = () => {
    const headers = ['时间戳', '开盘价', '最高价', '最低价', '收盘价', '成交量'];
    const rows = data.map((d) => [
      d.timestamp,
      d.open.toFixed(4),
      d.high.toFixed(4),
      d.low.toFixed(4),
      d.close.toFixed(4),
      d.volume.toFixed(2),
    ]);

    const csvContent = [headers, ...rows].map((r) => r.join(',')).join('\n');
    downloadFile(csvContent, 'prediction.csv', 'text/csv');
  };

  // 导出 JSON
  const exportJSON = () => {
    const jsonContent = JSON.stringify({ predictions: data, statistics }, null, 2);
    downloadFile(jsonContent, 'prediction.json', 'application/json');
  };

  // 下载文件
  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      {/* 统计信息 */}
      <div className="grid grid-4" style={{ marginBottom: 20 }}>
        <div style={{ padding: 16, background: '#f5f5f5', borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#666' }}>平均收盘价</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#1890ff' }}>
            {statistics.avg_close.toFixed(4)}
          </div>
        </div>
        <div style={{ padding: 16, background: '#f5f5f5', borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#666' }}>最高收盘价</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#52c41a' }}>
            {statistics.max_close.toFixed(4)}
          </div>
        </div>
        <div style={{ padding: 16, background: '#f5f5f5', borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#666' }}>最低收盘价</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#ff4d4f' }}>
            {statistics.min_close.toFixed(4)}
          </div>
        </div>
        <div style={{ padding: 16, background: '#f5f5f5', borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#666' }}>波动率</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#faad14' }}>
            {(statistics.volatility * 100).toFixed(2)}%
          </div>
        </div>
      </div>

      {/* 导出按钮 */}
      <div style={{ marginBottom: 16 }}>
        <button className="btn btn-secondary" onClick={exportCSV} style={{ marginRight: 8 }}>
          导出 CSV
        </button>
        <button className="btn btn-secondary" onClick={exportJSON}>
          导出 JSON
        </button>
      </div>

      {/* 数据表格 */}
      <div className="table-container" style={{ maxHeight: 400, overflowY: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>时间戳</th>
              <th>开盘价</th>
              <th>最高价</th>
              <th>最低价</th>
              <th>收盘价</th>
              <th>成交量</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={index}>
                <td>{new Date(item.timestamp).format('yyyy-MM-dd HH:mm')}</td>
                <td>{item.open.toFixed(4)}</td>
                <td>{item.high.toFixed(4)}</td>
                <td>{item.low.toFixed(4)}</td>
                <td
                  style={{
                    color: item.close >= item.open ? '#52c41a' : '#ff4d4f',
                    fontWeight: 500,
                  }}
                >
                  {item.close.toFixed(4)}
                </td>
                <td>{item.volume.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// 添加 Date 格式化方法
declare global {
  interface Date {
    format(fmt: string): string;
  }
}

Date.prototype.format = function (fmt: string): string {
  const o: Record<string, number> = {
    'M+': this.getMonth() + 1,
    'd+': this.getDate(),
    'H+': this.getHours(),
    'm+': this.getMinutes(),
    's+': this.getSeconds(),
    'q+': Math.floor((this.getMonth() + 3) / 3),
    S: this.getMilliseconds(),
  };

  if (/(y+)/.test(fmt)) {
    fmt = fmt.replace(RegExp.$1, (this.getFullYear() + '').substr(4 - RegExp.$1.length));
  }

  for (const k in o) {
    if (new RegExp('(' + k + ')').test(fmt)) {
      fmt = fmt.replace(
        RegExp.$1,
        RegExp.$1.length === 1 ? String(o[k]) : ('00' + o[k]).substr(('' + o[k]).length)
      );
    }
  }
  return fmt;
};

export default PredictionTable;