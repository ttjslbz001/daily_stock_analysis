import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    // 全局测试环境设置
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],

    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        'dist/',
      ],
      // 覆盖率阈值
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },

    // 测试匹配模式
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],

    // 排除测试文件
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],

    // 测试超时时间（毫秒）
    testTimeout: 10000,
    hookTimeout: 10000,

    // 并行执行测试
    threads: true,
    maxThreads: 4,

    // 监听模式配置
    watch: true,

    // 报告器
    reporters: ['verbose', 'json', 'html'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
