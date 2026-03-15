import apiClient from './index';
import type {
  WatchedStocksListResponse,
  AddWatchedStockRequest,
  AddWatchedStockResponse,
  RemoveWatchedStockResponse,
} from '../types/watchedStocks';

/**
 * 关注股票 API 客户端
 */
export const watchedStocksApi = {
  /**
   * 获取关注股票列表
   */
  async getWatchedStocks(): Promise<WatchedStocksListResponse> {
    const response = await apiClient.get<WatchedStocksListResponse>('/api/v1/watched');
    return response.data;
  },

  /**
   * 添加关注股票
   */
  async addWatchedStock(request: AddWatchedStockRequest): Promise<AddWatchedStockResponse> {
    const response = await apiClient.post<AddWatchedStockResponse>('/api/v1/watched', request);
    return response.data;
  },

  /**
   * 取消关注股票
   */
  async removeWatchedStock(stockCode: string): Promise<RemoveWatchedStockResponse> {
    const response = await apiClient.delete<RemoveWatchedStockResponse>(
      `/api/v1/watched/${stockCode}`
    );
    return response.data;
  },
};
