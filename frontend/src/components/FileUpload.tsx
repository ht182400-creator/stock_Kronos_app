/**
 * Kronos 金融预测 Web 应用 - 文件上传组件
 */

import React, { useRef, useState, useEffect } from 'react';
import type { DataFileInfo, FilePreview, PaginationInfo } from '../types/api';

interface FileUploadProps {
  files: DataFileInfo[];
  selectedFile: DataFileInfo | null;
  onUpload: (file: File) => void;
  onSelect: (file: DataFileInfo | null) => void;
  loading: boolean;
}

const PAGE_SIZE = 5;

const FileUpload: React.FC<FileUploadProps> = ({
  files,
  selectedFile,
  onUpload,
  onSelect,
  loading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [expandedFile, setExpandedFile] = useState<string | null>(null);
  
  // 分页状态
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loadingPreview, setLoadingPreview] = useState(false);
  
  // 缓存已加载的分页数据
  const pageCache = useRef<Map<string, Map<number, PaginationInfo>>>(new Map());

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
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

  const toggleExpand = async (e: React.MouseEvent, fileId: string) => {
    e.stopPropagation();
    
    if (expandedFile === fileId) {
      setExpandedFile(null);
      setPagination(null);
      setCurrentPage(1);
    } else {
      setExpandedFile(fileId);
      setCurrentPage(1);
      await loadPage(fileId, 1);
    }
  };

  const loadPage = async (fileId: string, page: number) => {
    // 检查缓存
    const fileCache = pageCache.current.get(fileId);
    if (fileCache && fileCache.has(page)) {
      setPagination(fileCache.get(page)!);
      setCurrentPage(page);
      return;
    }

    setLoadingPreview(true);
    try {
      const response = await fetch(`/api/data/${fileId}?page=${page}&page_size=${PAGE_SIZE}`);
      const data = await response.json();
      
      if (data.success) {
        // 更新缓存
        if (!pageCache.current.has(fileId)) {
          pageCache.current.set(fileId, new Map());
        }
        pageCache.current.get(fileId)!.set(page, data.pagination);
        
        setPagination(data.pagination);
        setCurrentPage(page);
      }
    } catch (error) {
      console.error('加载预览失败:', error);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handlePrevPage = () => {
    if (expandedFile && currentPage > 1) {
      loadPage(expandedFile, currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (expandedFile && pagination && currentPage < pagination.total_pages) {
      loadPage(expandedFile, currentPage + 1);
    }
  };

  const handlePageInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    if (!isNaN(value) && pagination) {
      const page = Math.max(1, Math.min(value, pagination.total_pages));
      if (expandedFile) {
        loadPage(expandedFile, page);
      }
    }
  };

  // 渲染预览表格
  const renderPreviewTable = (data: Record<string, any>[]) => {
    if (!data || data.length === 0) return null;
    
    const columns = Object.keys(data[0]);
    
    return (
      <div style={{ overflowX: 'auto', maxHeight: '300px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead style={{ position: 'sticky', top: 0, background: '#f5f5f5', zIndex: 1 }}>
            <tr>
              <th style={{ border: '1px solid #d9d9d9', padding: '6px 8px', textAlign: 'center', width: 50 }}>
                #
              </th>
              {columns.map(key => (
                <th key={key} style={{ border: '1px solid #d9d9d9', padding: '6px 8px', textAlign: 'left', minWidth: 80 }}>
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                <td style={{ border: '1px solid #d9d9d9', padding: '4px 8px', textAlign: 'center', color: '#999' }}>
                  {(currentPage - 1) * PAGE_SIZE + i + 1}
                </td>
                {columns.map((key, j) => (
                  <td key={j} style={{ border: '1px solid #d9d9d9', padding: '4px 8px' }}>
                    {String(row[key] ?? '').slice(0, 15)}{String(row[key] ?? '').length > 15 ? '...' : ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // 渲染快捷跳转
  const renderQuickNav = () => {
    if (!pagination) return null;
    
    return (
      <div style={{ marginTop: 8, padding: '8px 0', borderTop: '1px solid #e8e8e8' }}>
        <div style={{ fontSize: 11, color: '#52c41a', marginBottom: 6 }}>前5条记录（快捷查看）</div>
        {renderPreviewTable(pagination.head)}
      </div>
    );
  };

  // 渲染分页控件
  const renderPagination = () => {
    if (!pagination) return null;
    
    const { total_rows, total_pages, has_prev, has_next } = pagination;
    
    return (
      <div style={{ marginTop: 12, padding: '10px 12px', background: '#f8f8f8', borderRadius: 6 }}>
        {/* 统计信息 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ fontSize: 12 }}>
            <span style={{ color: '#1890ff', fontWeight: 500 }}>第 {currentPage} / {total_pages} 页</span>
            <span style={{ color: '#999', marginLeft: 12 }}>共 {total_rows.toLocaleString()} 条</span>
            <span style={{ color: '#999', marginLeft: 12 }}>每页 {PAGE_SIZE} 条</span>
          </div>
        </div>
        
        {/* 分页表格 */}
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>当前页数据:</div>
          {loadingPreview ? (
            <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>加载中...</div>
          ) : (
            renderPreviewTable(pagination.data)
          )}
        </div>
        
        {/* 翻页按钮 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            onClick={handlePrevPage}
            disabled={!has_prev}
            style={{
              padding: '6px 16px',
              fontSize: 12,
              border: '1px solid #d9d9d9',
              borderRadius: 4,
              background: has_prev ? '#fff' : '#f5f5f5',
              color: has_prev ? '#333' : '#ccc',
              cursor: has_prev ? 'pointer' : 'not-allowed',
              disabled: !has_prev,
            }}
          >
            ← 上一页
          </button>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 12, color: '#666' }}>跳转到</span>
            <input
              type="number"
              min={1}
              max={total_pages}
              defaultValue={currentPage}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handlePageInput(e as any);
                }
              }}
              style={{
                width: 60,
                padding: '4px 8px',
                fontSize: 12,
                border: '1px solid #d9d9d9',
                borderRadius: 4,
                textAlign: 'center',
              }}
            />
            <span style={{ fontSize: 12, color: '#666' }}>页</span>
            <button
              onClick={() => {
                const input = document.querySelector('input[type=number]') as HTMLInputElement;
                if (input) {
                  const value = parseInt(input.value);
                  if (!isNaN(value) && pagination) {
                    const page = Math.max(1, Math.min(value, pagination.total_pages));
                    if (expandedFile) loadPage(expandedFile, page);
                  }
                }
              }}
              style={{
                padding: '4px 12px',
                fontSize: 12,
                border: '1px solid #1890ff',
                borderRadius: 4,
                background: '#1890ff',
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              确定
            </button>
          </div>
          
          <button
            onClick={handleNextPage}
            disabled={!has_next}
            style={{
              padding: '6px 16px',
              fontSize: 12,
              border: '1px solid #d9d9d9',
              borderRadius: 4,
              background: has_next ? '#fff' : '#f5f5f5',
              color: has_next ? '#333' : '#ccc',
              cursor: has_next ? 'pointer' : 'not-allowed',
            }}
          >
            下一页 →
          </button>
        </div>
        
        {/* 后5条快捷查看 */}
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px dashed #e8e8e8' }}>
          <div style={{ fontSize: 11, color: '#fa8c16', marginBottom: 6 }}>后5条记录（快捷查看）</div>
          {renderPreviewTable(pagination.tail)}
        </div>
      </div>
    );
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
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {files.map((file) => (
              <div
                key={file.file_id}
                onClick={() => onSelect(file)}
                style={{
                  padding: '10px 12px',
                  marginBottom: 8,
                  borderRadius: 6,
                  border: `1px solid ${selectedFile?.file_id === file.file_id ? '#1890ff' : '#e8e8e8'}`,
                  background: selectedFile?.file_id === file.file_id ? '#e6f7ff' : '#fff',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
                      {file.file_name}
                    </div>
                    <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                      {file.rows.toLocaleString()} 行 | {formatFileSize(file.size)}
                    </div>
                    {file.time_range && (
                      <div style={{ fontSize: 11, color: '#1890ff', marginBottom: 2 }}>
                        📅 {file.time_range.start} ~ {file.time_range.end}
                      </div>
                    )}
                    {file.columns && file.columns.length > 0 && (
                      <div style={{ fontSize: 11, color: '#52c41a', marginBottom: 2 }}>
                        📊 列: {file.columns.slice(0, 5).join(', ')}
                        {file.columns.length > 5 && ` (+${file.columns.length - 5} more)`}
                      </div>
                    )}
                    {file.uploaded_at && (
                      <div style={{ fontSize: 11, color: '#999' }}>
                        ⏰ {new Date(file.uploaded_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                  {/* 展开/收起按钮 */}
                  {'preview' in file && (
                    <button
                      onClick={(e) => toggleExpand(e, file.file_id)}
                      style={{
                        padding: '4px 8px',
                        fontSize: 11,
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        background: expandedFile === file.file_id ? '#f0f0f0' : '#fff',
                        cursor: 'pointer',
                        marginLeft: 8,
                      }}
                    >
                      {expandedFile === file.file_id ? '收起 ▲' : '预览 ▼'}
                    </button>
                  )}
                </div>

                {/* 数据预览（分页模式） */}
                {expandedFile === file.file_id && renderPagination()}
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
