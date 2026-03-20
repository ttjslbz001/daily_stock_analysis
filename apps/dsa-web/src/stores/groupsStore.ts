import { create } from 'zustand';
import { groupsApi } from '../api/groups';
import type { StockGroup, CreateGroupRequest, UpdateGroupRequest } from '../api/groups';

interface GroupsState {
  groups: StockGroup[];
  loading: boolean;
  error: string | null;

  fetchGroups: () => Promise<void>;
  createGroup: (data: CreateGroupRequest) => Promise<StockGroup>;
  updateGroup: (id: number, data: UpdateGroupRequest) => Promise<StockGroup>;
  deleteGroup: (id: number) => Promise<void>;
  reorderGroups: (orders: Array<{id: number; sortOrder: number}>) => Promise<void>;
}

const getMsg = (e: unknown) => (e instanceof Error ? e.message : String(e));

export const useGroupsStore = create<GroupsState>((set, get) => ({
  groups: [],
  loading: false,
  error: null,

  fetchGroups: async () => {
    set({ loading: true, error: null });
    try {
      const groups = await groupsApi.list();
      set({ groups, loading: false });
    } catch (error: unknown) {
      set({ error: getMsg(error), loading: false });
    }
  },

  createGroup: async (data) => {
    set({ loading: true, error: null });
    try {
      const group = await groupsApi.create(data);
      const groups = [...get().groups, group].sort((a, b) => a.sortOrder - b.sortOrder);
      set({ groups, loading: false });
      return group;
    } catch (error: unknown) {
      set({ error: getMsg(error), loading: false });
      throw error;
    }
  },

  updateGroup: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const updated = await groupsApi.update(id, data);
      const groups = get().groups.map(g => g.id === id ? updated : g);
      set({ groups, loading: false });
      return updated;
    } catch (error: unknown) {
      set({ error: getMsg(error), loading: false });
      throw error;
    }
  },

  deleteGroup: async (id) => {
    set({ loading: true, error: null });
    try {
      await groupsApi.delete(id);
      const groups = get().groups.filter(g => g.id !== id);
      set({ groups, loading: false });
    } catch (error: unknown) {
      set({ error: getMsg(error), loading: false });
      throw error;
    }
  },

  reorderGroups: async (orders) => {
    try {
      await groupsApi.batchReorder(orders);
      await get().fetchGroups();
    } catch (error: unknown) {
      set({ error: getMsg(error) });
      throw error;
    }
  },
}));
