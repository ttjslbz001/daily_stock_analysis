import apiClient from './index';
import { toCamelCase } from './utils';

export interface TagListResponse {
  tags: string[];
}

export interface AddTagRequest {
  tagName: string;
}

export const tagsApi = {
  // Get all unique tags (for autocomplete)
  getAllTags: async (): Promise<string[]> => {
    const response = await apiClient.get('/api/v1/tags');
    return toCamelCase(response.data).tags;
  },

  // Get tags for a specific stock
  getStockTags: async (code: string): Promise<string[]> => {
    const response = await apiClient.get(`/api/v1/stocks/${code}/tags`);
    return toCamelCase(response.data).tags;
  },

  // Add a tag to a stock
  addTag: async (code: string, tagName: string): Promise<string[]> => {
    const response = await apiClient.post(`/api/v1/stocks/${code}/tags`, { tag_name: tagName });
    return toCamelCase(response.data).tags;
  },

  // Remove a tag from a stock
  removeTag: async (code: string, tagName: string): Promise<string[]> => {
    const response = await apiClient.delete(`/api/v1/stocks/${code}/tags/${encodeURIComponent(tagName)}`);
    return toCamelCase(response.data).tags;
  },
};
