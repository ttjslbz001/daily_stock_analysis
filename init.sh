#!/bin/bash
# 初始化关注股票功能开发环境

set -e  # 遇到错误立即退出

echo "=== 关注股票功能开发环境初始化 ==="

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 检查 Python 虚拟环境
if [ ! -d ".venv" ]; then
    echo "错误: 未找到 Python 虚拟环境，请先运行 python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查后端依赖
echo "检查后端依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "安装后端依赖..."
    pip install -e . -q
fi

# 检查前端依赖
echo "检查前端依赖..."
if [ ! -d "apps/dsa-web/node_modules" ]; then
    echo "安装前端依赖..."
    cd apps/dsa-web
    npm install --silent
    cd "$PROJECT_ROOT"
fi

# 初始化数据库表
echo "初始化数据库表..."
python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from src.repositories.watched_stocks_repo import WatchedStocksRepository
try:
    repo = WatchedStocksRepository()
    print('数据库表初始化成功')
except Exception as e:
    print(f'数据库表初始化失败: {e}')
    sys.exit(1)
"

echo ""
echo "=== 环境初始化完成 ==="
echo ""
echo "可用的开发命令:"
echo "  启动后端:     python -m uvicorn api.app:app --reload"
echo "  启动前端:     cd apps/dsa-web && npm run dev"
echo "  运行测试:     pytest"
echo ""
