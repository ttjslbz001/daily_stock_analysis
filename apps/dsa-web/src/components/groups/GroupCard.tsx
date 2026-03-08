import React from 'react';
import { StockGroup } from '../../api/groups';

interface Props {
  group: StockGroup;
  onEdit: (group: StockGroup) => void;
  onDelete: (id: number) => void;
}

export const GroupCard: React.FC<Props> = ({ group, onEdit, onDelete }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-semibold text-white">{group.name}</h3>
          {group.description && (
            <p className="text-sm text-gray-400">{group.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(group)}
            className="text-cyan-400 hover:text-cyan-300 text-sm"
          >
            编辑
          </button>
          <button
            onClick={() => onDelete(group.id)}
            className="text-red-400 hover:text-red-300 text-sm"
          >
            删除
          </button>
        </div>
      </div>

      <div className="text-sm text-gray-500 mb-3">
        {group.stockCodes.length} 只股票
      </div>

      <div className="flex flex-wrap gap-2">
        {group.stockCodes.map(code => (
          <span
            key={code}
            className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
          >
            {code}
          </span>
        ))}
      </div>
    </div>
  );
};
