/**
 * Vitest 测试环境设置文件
 *
 * 在运行所有测试之前执行的初始化代码
 */

import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// 每个测试后清理 DOM
afterEach(() => {
  cleanup()
})

// 扩展 Vitest 的 expect 匹配器
expect.extend({})
