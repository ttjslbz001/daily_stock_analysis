import React, { useState, useEffect, useRef } from 'react';
import { useTagsStore } from '../../stores/tagsStore';

interface Props {
  stockCode: string;
  onClose?: () => void;
}

export const StockTagEditor: React.FC<Props> = ({ stockCode, onClose }) => {
  const { stockTags, allTags, fetchStockTags, fetchAllTags, addTag, removeTag } = useTagsStore();
  const [newTag, setNewTag] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const tags = stockTags[stockCode] || [];

  useEffect(() => {
    fetchStockTags(stockCode);
    if (allTags.length === 0) {
      fetchAllTags();
    }
  }, [stockCode]);

  const suggestions = newTag.trim()
    ? allTags.filter(t => t.toLowerCase().includes(newTag.toLowerCase()) && !tags.includes(t))
    : allTags.filter(t => !tags.includes(t));

  const handleAddTag = async (tag?: string) => {
    const tagToAdd = tag || newTag.trim();
    if (!tagToAdd) return;
    try {
      await addTag(stockCode, tagToAdd);
      setNewTag('');
      setShowSuggestions(false);
    } catch (e) {
      console.error('Failed to add tag:', e);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      await removeTag(stockCode, tag);
    } catch (e) {
      console.error('Failed to remove tag:', e);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      onClose?.();
    }
  };

  return (
    <div className="mt-2 p-2 bg-gray-900 rounded border border-gray-600">
      <div className="text-xs text-gray-400 mb-2">标签管理: {stockCode}</div>
      <div className="flex flex-wrap gap-1 mb-2">
        {tags.map(tag => (
          <span key={tag} className="inline-flex items-center px-2 py-0.5 bg-cyan-900/50 text-cyan-300 rounded text-xs">
            {tag}
            <button onClick={() => handleRemoveTag(tag)} className="ml-1 text-cyan-400 hover:text-red-400">×</button>
          </span>
        ))}
        {tags.length === 0 && <span className="text-xs text-gray-500">暂无标签</span>}
      </div>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={newTag}
          onChange={e => { setNewTag(e.target.value); setShowSuggestions(true); }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={handleKeyDown}
          placeholder="添加标签..."
          className="w-full px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
        />
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-600 rounded shadow-lg max-h-32 overflow-y-auto">
            {suggestions.slice(0, 5).map(tag => (
              <button key={tag} onClick={() => handleAddTag(tag)} className="w-full px-2 py-1 text-left text-sm text-white hover:bg-gray-700">
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="flex justify-end mt-2">
        <button onClick={onClose} className="text-xs text-gray-400 hover:text-white">完成</button>
      </div>
    </div>
  );
};
