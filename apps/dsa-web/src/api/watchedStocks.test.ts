/**
 * WatchedStocks API client tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockDelete = vi.fn()

vi.mock('./index', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}))

import { watchedStocksApi } from './watchedStocks'

describe('WatchedStocks API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getWatchedStocks', () => {
    it('should fetch watched stocks successfully', async () => {
      const mockData = { items: [], total: 0 }
      mockGet.mockResolvedValue({ data: mockData })

      const response = await watchedStocksApi.getWatchedStocks()

      expect(response).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/api/v1/watched')
    })

    it('should handle API errors', async () => {
      mockGet.mockRejectedValue(new Error('Network error'))

      await expect(watchedStocksApi.getWatchedStocks()).rejects.toThrow('Network error')
    })
  })

  describe('addWatchedStock', () => {
    it('should add a stock to watch list', async () => {
      const stockCode = '600519'
      const mockData = { success: true, stock_code: stockCode }
      mockPost.mockResolvedValue({ data: mockData })

      const result = await watchedStocksApi.addWatchedStock({ stock_code: stockCode })

      expect(result).toEqual(mockData)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/watched', { stock_code: stockCode })
    })

    it('should propagate API errors', async () => {
      mockPost.mockRejectedValue(new Error('Bad request'))

      await expect(
        watchedStocksApi.addWatchedStock({ stock_code: 'invalid' })
      ).rejects.toThrow('Bad request')
    })
  })

  describe('removeWatchedStock', () => {
    it('should remove a stock from watch list', async () => {
      const stockCode = '600519'
      const mockData = { success: true }
      mockDelete.mockResolvedValue({ data: mockData })

      const result = await watchedStocksApi.removeWatchedStock(stockCode)

      expect(result).toEqual(mockData)
      expect(mockDelete).toHaveBeenCalledWith(`/api/v1/watched/${stockCode}`)
    })
  })
})
