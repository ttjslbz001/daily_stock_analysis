import React, { useEffect, useState } from 'react';
import { useGroupsStore } from '../stores/groupsStore';
import { GroupCard } from '../components/groups/GroupCard';
import { CreateEditGroupModal } from '../components/groups/CreateEditGroupModal';
import type { StockGroup, CreateGroupRequest, UpdateGroupRequest } from '../api/groups';

export const GroupsPage: React.FC = () => {
  const { groups, loading, error, fetchGroups, createGroup, updateGroup, deleteGroup } = useGroupsStore();
  const [showModal, setShowModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState<StockGroup | null>(null);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  const handleCreate = () => {
    setEditingGroup(null);
    setShowModal(true);
  };

  const handleEdit = (group: StockGroup) => {
    setEditingGroup(group);
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('确定要删除这个分组吗？')) {
      await deleteGroup(id);
    }
  };

  const handleSave = async (data: CreateGroupRequest | UpdateGroupRequest) => {
    if (editingGroup) {
      await updateGroup(editingGroup.id, data as UpdateGroupRequest);
    } else {
      await createGroup(data as CreateGroupRequest);
    }
  };

  if (loading && groups.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">自选股分组</h1>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded"
        >
          + 新建分组
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900 border border-red-700 rounded text-red-200">
          {error}
        </div>
      )}

      {groups.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          暂无分组，点击"新建分组"开始
        </div>
      ) : (
        <div className="grid gap-4">
          {groups.map(group => (
            <GroupCard
              key={group.id}
              group={group}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showModal && (
        <CreateEditGroupModal
          group={editingGroup}
          onSave={handleSave}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
};

export default GroupsPage;
