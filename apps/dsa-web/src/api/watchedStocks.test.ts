/**
 * WatchedStocks API 客户端测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getWatchedStocks, addWatchedStock, removeWatchedStock } from './watchedStocks'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
    }),
  },
}))

describe('WatchedStocks API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getWatchedStocks', () => {
    it('should fetch watched stocks successfully', async () => {
      const response = await getWatchedStocks()

      expect(response).toBeDefined()
      // 根据实际实现调整断言
    })

    it('should handle API errors', async () => {
      // 测试错误处理
      await expect(getWatchedStocks()).rejects.toThrow()
    })
  })

  describe('addWatchedStock', () => {
    it('should add a stock to watch list', async () => {
      const stockCode = '600519'

      const result = await addWatchedStock(stockCode)

      expect(result).toBeDefined()
    })

    it('should validate stock code format', async () => {
      const invalidCode = 'invalid'

      await expect(addWatchedStock(invalidCode)).rejects.toThrow()
    })
  })

  describe('removeWatchedStock', () => {
    it('should remove a stock from watch list', async () => {
      const stockCode = '600519'

      const result = await removeWatchedStock(stockCode)

      expect(result).toBeDefined()
    })
  })
})
