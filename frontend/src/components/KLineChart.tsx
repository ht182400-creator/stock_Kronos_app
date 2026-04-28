/**
 * Kronos 金融预测 Web 应用 - K线图表组件
 */

import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface KLineChartProps {
  config: Record<string, any>;
}

const KLineChart: React.FC<KLineChartProps> = ({ config }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化图表
    chartInstance.current = echarts.init(chartRef.current);

    // 渲染图表
    chartInstance.current.setOption({
      ...config,
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          if (!params || params.length === 0) return '';
          const data = params[0];
          if (!data || !data.data) return '';
          
          const [open, close, low, high] = data.data;
          const color = close >= open ? '#ee0a24' : '#26a69a';
          
          return `
            <div style="font-size: 12px;">
              <div>时间: ${data.axisValue}</div>
              <div style="color: ${color};">
                <div>开盘: ${open?.toFixed(2)}</div>
                <div>收盘: ${close?.toFixed(2)}</div>
                <div>最低: ${low?.toFixed(2)}</div>
                <div>最高: ${high?.toFixed(2)}</div>
              </div>
            </div>
          `;
        },
      },
      axisPointer: {
        link: [{ xAxisIndex: 'all' }],
        label: {
          backgroundColor: '#777',
        },
      },
    });

    // 响应窗口大小变化
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [config]);

  return (
    <div
      ref={chartRef}
      className="chart-container"
      style={{ height: 500 }}
    />
  );
};

export default KLineChart;