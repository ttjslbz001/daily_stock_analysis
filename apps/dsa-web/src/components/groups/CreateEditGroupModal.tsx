import React, { useState } from 'react';
import type { StockGroup, CreateGroupRequest, UpdateGroupRequest } from '../../api/groups';

interface Props {
  group?: StockGroup | null;
  onSave: (data: CreateGroupRequest | UpdateGroupRequest) => Promise<void>;
  onClose: () => void;
}

export const CreateEditGroupModal: React.FC<Props> = ({ group, onSave, onClose }) => {
  const [name, setName] = useState(group?.name || '');
  const [description, setDescription] = useState(group?.description || '');
  const [stockCodesInput, setStockCodesInput] = useState(group?.stockCodes.join(', ') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isEdit = !!group;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('分组名称不能为空');
      return;
    }

    const codes = stockCodesInput
      .split(/[,，\s]+/)
      .map(c => c.trim())
      .filter(c => c);

    if (codes.length === 0) {
      setError('请输入至少一个股票代码');
      return;
    }

    setLoading(true);
    try {
      await onSave({
        name: name.trim(),
        description: description.trim() || undefined,
        stockCodes: codes,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || '保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">
            {isEdit ? '编辑分组' : '新建分组'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm text-gray-300 mb-1">分组名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              placeholder="如：科技成长"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm text-gray-300 mb-1">描述（可选）</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              placeholder="如：高增长科技股票"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm text-gray-300 mb-1">股票代码</label>
            <textarea
              value={stockCodesInput}
              onChange={(e) => setStockCodesInput(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white h-24"
              placeholder="多个代码用逗号或空格分隔，如：600519, 300750, 00700"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm mb-4">{error}</p>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded disabled:opacity-50"
            >
              {loading ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
