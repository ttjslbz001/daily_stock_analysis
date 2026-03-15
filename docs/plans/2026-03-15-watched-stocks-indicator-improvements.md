# 关注股票指标改进实施计划

## 项目概述

对"我关注的股票"功能进行两项改进：
1. 每只股票的指标行添加单独的刷新按钮，允许单独刷新某只股票的指标数据
2. 优化指标行布局，让布林线、MACD、RSI、年高/低等数据对齐显示更美观

**创建日期**: 2026-03-15
**优先级**: 中
**预计工期**: 30-45分钟

## 当前状态分析

### 现有架构
- 前端: React + TypeScript + Tailwind CSS
- 后端: FastAPI (已支持 `GET /api/v1/watched/{stock_code}/indicators?force_refresh=true`)
- 当前组件: `WatchedStocksPanel` 位于 `apps/dsa-web/src/components/watchedStocks/WatchedStocksPanel.tsx`

### 当前问题
1. 缺少单只股票刷新功能 - 只能全局刷新所有股票
2. 指标行布局使用 flex wrap，在不同屏幕尺寸下对齐不一致
3. 各指标组的 min-width 固定但内容长度变化导致对齐问题

## 实施任务

### Phase 1: 单只股票刷新功能 (15分钟)

#### 1.1 添加单只股票刷新状态
- [ ] 在 `StockWithLoading` 接口中添加 `refreshing` 状态
- [ ] 在组件 state 中跟踪各股票的刷新状态

**文件**: `apps/dsa-web/src/components/watchedStocks/WatchedStocksPanel.tsx`

修改后的接口:
```typescript
// 加载状态
interface StockWithLoading extends WatchedStock {
  loading?: boolean;
  error?: string;
  refreshing?: boolean;  // 新增：单只股票刷新状态
}
```

#### 1.2 实现单只股票刷新函数
- [ ] 创建 `handleRefreshStock` 函数
- [ ] 调用 `fetchStockIndicators` 并设置 `force_refresh=true`
- [ ] 更新对应股票的 `refreshing` 状态

**代码**:
```typescript
// 单只股票刷新
const handleRefreshStock = async (stockCode: string) => {
  setStocks(prev => prev.map(s => {
    if (s.stock_code === stockCode) {
      return { ...s, refreshing: true };
    }
    return s;
  }));

  try {
    const data = await fetchStockIndicators(stockCode, true);
    if (data) {
      setStocks(prev => prev.map(s => {
        if (s.stock_code === stockCode) {
          return { ...data, loading: false, refreshing: false };
        }
        return s;
      }));
    } else {
      setStocks(prev => prev.map(s => {
        if (s.stock_code === stockCode) {
          return { ...s, refreshing: false, error: '刷新失败' };
        }
        return s;
      }));
    }
  } catch (err) {
    console.error(`刷新 ${stockCode} 失败:`, err);
    setStocks(prev => prev.map(s => {
      if (s.stock_code === stockCode) {
        return { ...s, refreshing: false, error: '刷新失败' };
      }
      return s;
    }));
  }
};
```

#### 1.3 添加刷新按钮 UI
- [ ] 在指标行右侧添加刷新按钮
- [ ] 显示加载状态（旋转动画）
- [ ] 使用合适的图标和样式

**代码**:
```typescript
// 在 renderStockRow 中，在指标行添加刷新按钮
{!isLoading && (
  <button
    onClick={() => handleRefreshStock(stock.stock_code)}
    disabled={stock.refreshing}
    className="p-1 text-muted hover:text-cyan transition-colors disabled:opacity-50"
    title="刷新指标"
  >
    <svg
      className={`w-4 h-4 ${stock.refreshing ? 'animate-spin' : ''}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  </button>
)}
```

---

### Phase 2: 指标行布局优化 (20-30分钟)

#### 2.1 重新设计指标行布局
- [ ] 使用表格式布局替代 flex wrap
- [ ] 确保各指标组在所有行中对齐
- [ ] 固定各指标列宽度，使用 flex-1 分配剩余空间

**新的布局策略**:
```
[股票代码] [价格/涨跌] | [BOLL] [MACD] [RSI] [年高/低] [刷新]
```

#### 2.2 实现新的指标行组件
- [ ] 创建指标数据统一格式化组件
- [ ] 使用一致的宽度和对齐方式
- [ ] 响应式设计：移动端可换行

**代码**:
```typescript
// 指标数据展示组件
const IndicatorValue: React.FC<{
  label: string;
  values: Array<{ value: string; color: string }>;
  separator?: string;
}> = ({ label, values, separator = '/' }) => (
  <div className="flex items-center gap-2 text-sm min-w-[140px]">
    <span className="text-muted shrink-0 text-xs w-12">{label}</span>
    <div className="flex items-center gap-1 font-mono text-xs">
      {values.map((item, idx) => (
        <React.Fragment key={idx}>
          <span className={item.color}>{item.value}</span>
          {idx < values.length - 1 && (
            <span className="text-muted text-[10px]">{separator}</span>
          )}
        </React.Fragment>
      ))}
    </div>
  </div>
);

// 在 renderStockRow 中使用
{!isLoading && (
  <div className="flex items-center gap-3 flex-1 overflow-hidden">
    <IndicatorValue
      label="BOLL"
      values={[
        { value: stock.bollinger.upper.toFixed(1), color: 'text-red-400' },
        { value: stock.bollinger.middle.toFixed(1), color: 'text-secondary' },
        { value: stock.bollinger.lower.toFixed(1), color: 'text-green-400' }
      ]}
    />
    <IndicatorValue
      label="MACD"
      values={[{
        value: stock.macd.bar.toFixed(2),
        color: stock.macd.bar >= 0 ? 'text-red-400' : 'text-green-400'
      }]}
    />
    <IndicatorValue
      label="RSI"
      values={[
        { value: stock.rsi.rsi6.toFixed(0), color: 'text-secondary' },
        { value: stock.rsi.rsi12.toFixed(0), color: 'text-secondary' },
        { value: stock.rsi.rsi24.toFixed(0), color: 'text-secondary' }
      ]}
    />
    <IndicatorValue
      label="年高/低"
      values={[
        { value: stock.year_high?.toFixed(2) || '-', color: 'text-red-400' },
        { value: stock.year_low?.toFixed(2) || '-', color: 'text-green-400' }
      ]}
    />
  </div>
)}
```

#### 2.3 优化表头对齐
- [ ] 更新表头宽度与指标列匹配
- [ ] 确保表头和内容列对齐

**代码**:
```typescript
{/* 表头 */}
{stocks.length > 0 && (
  <div className="flex items-center gap-3 px-4 py-2 text-xs text-muted border-b border-white/5 bg-white/[0.01]">
    <div className="min-w-[140px]">股票</div>
    <div className="min-w-[160px]">价格 / 涨跌</div>
    <div className="w-px h-4 bg-white/10 hidden sm:block" />
    <div className="min-w-[140px]">布林线 (上/中/下)</div>
    <div className="min-w-[140px]">MACD</div>
    <div className="min-w-[140px]">RSI (6/12/24)</div>
    <div className="min-w-[140px]">年高/低</div>
    <div className="w-8" /> {/* 刷新按钮占位 */}
  </div>
)}
```

#### 2.4 响应式布局优化
- [ ] 在小屏幕上隐藏部分指标或改为垂直堆叠
- [ ] 添加断点处理

**代码**:
```typescript
// 小屏幕时的布局
<div className="flex items-center gap-3 flex-1 overflow-hidden sm:flex-nowrap flex-wrap sm:flex-nowrap">
  {/* 指标内容 */}
</div>
```

#### 2.5 添加分隔线和视觉层次
- [ ] 在指标之间添加分隔线
- [ ] 使用不同的背景色区分不同区域

**代码**:
```typescript
// 添加分隔线
<div className="flex items-center gap-3 flex-1 overflow-hidden">
  <IndicatorValue label="BOLL" values={...} />
  <div className="w-px h-6 bg-white/10" />
  <IndicatorValue label="MACD" values={...} />
  <div className="w-px h-6 bg-white/10" />
  <IndicatorValue label="RSI" values={...} />
  <div className="w-px h-6 bg-white/10" />
  <IndicatorValue label="年高/低" values={...} />
</div>
```

---

### Phase 3: 测试与验证 (10分钟)

#### 3.1 功能测试
- [ ] 测试单只股票刷新功能
- [ ] 测试刷新按钮加载状态
- [ ] 测试刷新失败错误处理

#### 3.2 布局测试
- [ ] 测试不同屏幕尺寸下的布局
- [ ] 验证各指标列对齐
- [ ] 测试长股票代码或数值的显示

#### 3.3 边界情况测试
- [ ] 测试空数据状态（year_high/low 为 null）
- [ ] 测试连续快速点击刷新按钮
- [ ] 测试网络错误状态

---

## 文件清单

### 修改的文件
1. `apps/dsa-web/src/components/watchedStocks/WatchedStocksPanel.tsx` - 主组件修改

### 测试文件（可选）
- 无需新建测试文件，手动验证即可

---

## 关键决策

1. **刷新策略**: 复用现有的 `GET /api/v1/watched/{stock_code}/indicators?force_refresh=true` API
2. **布局方案**: 使用固定宽度的列布局 + flexbox，而非纯表格，保持响应式能力
3. **状态管理**: 在单个组件内管理各股票的刷新状态，不需要全局状态
4. **响应式设计**: 小屏幕允许换行，大屏幕保持单行对齐

---

## 依赖与风险

### 依赖
- 现有后端 API 支持单只股票刷新（已支持）
- 现有 Tailwind CSS 配置

### 风险
1. 连续快速点击可能导致多个并发请求
2. 刷新过程中数据可能显示不一致

### 缓解措施
1. 添加防抖或节流机制（可选，当前未实现）
2. 使用 refreshing 状态禁用按钮，防止重复点击
3. 刷新时保留旧数据直到新数据到达

---

## 后续优化方向

1. 添加刷新失败的重试按钮
2. 添加自动刷新功能（定时刷新）
3. 添加刷新动画效果
4. 优化移动端体验（可折叠指标）
5. 添加指标排序功能
