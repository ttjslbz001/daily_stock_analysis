#!/bin/bash
# -*- coding: utf-8 -*-
"""
===================================
全项目测试脚本
===================================

运行所有测试（前端 + 后端），确保代码质量
"""

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 未安装"
        exit 1
    fi
}

# 检查 Python 语法
check_python_syntax() {
    print_info "检查 Python 语法..."
    python -m py_compile src/storage.py
    python -m py_compile api/middlewares/error_handler.py
    python -m py_compile src/repositories/base.py

    # 检查所有 Python 文件
    find src api -name "*.py" -type f -exec python -m py_compile {} \;

    print_success "Python 语法检查通过"
}

# 运行后端测试
run_backend_tests() {
    print_info "运行后端测试..."

    # 检查是否在虚拟环境中
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "未检测到 Python 虚拟环境，正在激活..."
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            print_error "未找到 .venv 虚拟环境"
            exit 1
        fi
    fi

    # 运行 pytest
    pytest tests/ -v --tb=short --cov=src --cov=api --cov-report=term-missing --cov-fail-under=48

    print_success "后端测试通过"
}

# 运行前端测试
run_frontend_tests() {
    print_info "运行前端测试..."

    if [ ! -d "apps/dsa-web" ]; then
        print_warning "前端目录不存在，跳过前端测试"
        return
    fi

    cd apps/dsa-web

    # 检查是否安装了依赖
    if [ ! -d "node_modules" ]; then
        print_info "安装前端依赖..."
        npm ci
    fi

    # 运行类型检查
    print_info "运行 TypeScript 类型检查..."
    npm run type-check

    # 运行 lint
    print_info "运行 ESLint..."
    npm run lint

    # 运行测试
    print_info "运行前端测试..."
    npm run test:run

    cd - > /dev/null

    print_success "前端测试通过"
}

# 构建前端
build_frontend() {
    print_info "构建前端..."

    if [ ! -d "apps/dsa-web" ]; then
        print_warning "前端目录不存在，跳过构建"
        return
    fi

    cd apps/dsa-web

    # 运行构建
    npm run build

    cd - > /dev/null

    print_success "前端构建成功"
}

# 主函数
main() {
    print_info "开始全项目测试..."

    # 解析命令行参数
    SKIP_BACKEND=false
    SKIP_FRONTEND=false
    SKIP_BUILD=false
    SKIP_SYNTAX=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backend)
                SKIP_BACKEND=true
                shift
                ;;
            --skip-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-syntax)
                SKIP_SYNTAX=true
                shift
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --skip-backend    跳过后端测试"
                echo "  --skip-frontend  跳过前端测试"
                echo "  --skip-build     跳过前端构建"
                echo "  --skip-syntax    跳过语法检查"
                echo "  --help          显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                exit 1
                ;;
        esac
    done

    # 检查必要的命令
    check_command python
    check_command npm

    # Python 语法检查
    if [ "$SKIP_SYNTAX" = false ]; then
        check_python_syntax
    fi

    # 后端测试
    if [ "$SKIP_BACKEND" = false ]; then
        run_backend_tests
    fi

    # 前端测试
    if [ "$SKIP_FRONTEND" = false ]; then
        run_frontend_tests
    fi

    # 前端构建
    if [ "$SKIP_BUILD" = false ]; then
        build_frontend
    fi

    print_success "========================================"
    print_success "所有测试通过！"
    print_success "========================================"
}

# 运行主函数
main "$@"
