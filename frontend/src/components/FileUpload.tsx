/**
 * Kronos 金融预测 Web 应用 - 文件上传组件
 */

import React, { useRef } from 'react';
import type { DataFileInfo } from '../types/api';

interface FileUploadProps {
  files: DataFileInfo[];
  selectedFile: DataFileInfo | null;
  onUpload: (file: File) => void;
  onSelect: (file: DataFileInfo | null) => void;
  loading: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  files,
  selectedFile,
  onUpload,
  onSelect,
  loading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      // 清空 input 以允许重复选择同一文件
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div>
      {/* 上传按钮 */}
      <div style={{ marginBottom: 16 }}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          disabled={loading}
        />
        <button
          className="btn btn-secondary"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          style={{ width: '100%' }}
        >
          {loading ? '上传中...' : '上传 CSV 文件'}
        </button>
        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
          支持 .csv 格式，最大 50MB
        </div>
      </div>

      {/* 文件列表 */}
      {files.length > 0 && (
        <div>
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>已上传文件</div>
          <div style={{ maxHeight: 200, overflowY: 'auto' }}>
            {files.map((file) => (
              <div
                key={file.file_id}
                onClick={() => onSelect(file)}
                style={{
                  padding: '10px 12px',
                  marginBottom: 8,
                  borderRadius: 6,
                  border: `1px solid ${selectedFile?.file_id === file.file_id ? '#1890ff' : '#e8e8e8'
                    }`,
                  background: selectedFile?.file_id === file.file_id ? '#e6f7ff' : '#fff',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
                  {file.file_name}
                </div>
                <div style={{ fontSize: 12, color: '#666' }}>
                  {file.rows} 行 | {formatFileSize(file.size)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {files.length === 0 && (
        <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
          暂无上传文件
        </div>
      )}
    </div>
  );
};

export default FileUpload;