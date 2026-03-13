import apiClient from './index';
import { toCamelCase } from './utils';

export interface StockGroup {
  id: number;
  name: string;
  description?: string;
  stockCodes: string[];
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateGroupRequest {
  name: string;
  description?: string;
  stockCodes: string[];
  sortOrder?: number;
}

export interface UpdateGroupRequest {
  name?: string;
  description?: string;
  stockCodes?: string[];
  sortOrder?: number;
}

export const groupsApi = {
  list: async (): Promise<StockGroup[]> => {
    const response = await apiClient.get('/api/v1/groups');
    return toCamelCase(response.data.groups);
  },

  create: async (data: CreateGroupRequest): Promise<StockGroup> => {
    const response = await apiClient.post('/api/v1/groups', data);
    return toCamelCase(response.data);
  },

  update: async (id: number, data: UpdateGroupRequest): Promise<StockGroup> => {
    const response = await apiClient.put(`/api/v1/groups/${id}`, data);
    return toCamelCase(response.data);
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/groups/${id}`);
  },

  batchReorder: async (orders: Array<{id: number; sortOrder: number}>): Promise<void> => {
    await apiClient.post('/api/v1/groups/batch-reorder', { orders });
  },

  getGroupStocks: async (id: number): Promise<any> => {
    const response = await apiClient.get(`/api/v1/groups/${id}/stocks`);
    return toCamelCase(response.data);
  },
};
