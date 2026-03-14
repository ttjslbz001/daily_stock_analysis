<template>
  <el-card class="sector-table">
    <template #header>
      <div class="card-header">
        <span class="title">{{ title }}</span>
      </div>
    </template>

    <el-table :data="sectors" stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="rank" label="排名" width="60" align="center" />
      <el-table-column prop="name" label="板块名称" min-width="120" />
      <el-table-column prop="change_pct" label="涨跌幅" width="100" align="right">
        <template #default="{ row }">
          <span :class="getChangeClass(row.change_pct)">
            {{ formatChange(row.change_pct) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="leading_stock" label="领涨股" min-width="100" />
    </el-table>
  </el-card>
</template>

<script setup>
const props = defineProps({
  title: { type: String, required: true },
  sectors: { type: Array, required: true },
  loading: { type: Boolean, default: false }
})

const getChangeClass = (change) => {
  if (change > 0) return 'change-up'
  if (change < 0) return 'change-down'
  return 'change-flat'
}

const formatChange = (change) => {
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}
</script>

<style scoped>
.sector-table { height: 100%; }
.title { font-size: 18px; font-weight: bold; }
.change-up { color: #67C23A; font-weight: bold; }
.change-down { color: #F56C6C; font-weight: bold; }
</style>