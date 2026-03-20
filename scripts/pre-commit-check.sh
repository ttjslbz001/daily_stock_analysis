#!/bin/bash
#
# Pre-commit 检查脚本
#
# 在 Git 提交前运行，确保代码质量
#

set -e  # 遇到错误立即退出

# 检测 Python 命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found"
    exit 1
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 获取修改的文件
get_changed_files() {
    # 获取暂存的文件
    git diff --cached --name-only --diff-filter=ACM
}

# 检查 Python 文件
check_python_files() {
    local files=$(get_changed_files | grep -E '\.py$' || true)

    if [ -z "$files" ]; then
        return 0
    fi

    print_info "检查 Python 文件..."

    # 检查语法
    for file in $files; do
        if [ -f "$file" ]; then
            print_info "  检查 $file..."
            $PYTHON_CMD -m py_compile "$file" || {
                print_error "Python 语法检查失败: $file"
                return 1
            }
        fi
    done

    # 运行 flake8
    print_info "  运行 flake8 检查..."
    if command -v flake8 &> /dev/null; then
        flake8 $files --max-line-length=120 --ignore=E203,W503 || {
            print_error "flake8 检查失败"
            return 1
        }
    fi

    print_success "Python 文件检查通过"
}

# 检查 TypeScript/JavaScript 文件
check_js_files() {
    local files=$(get_changed_files | grep -E '\.(ts|tsx|js|jsx)$' || true)

    if [ -z "$files" ]; then
        return 0
    fi

    # 只检查 apps/dsa-web 目录下的文件
    local web_files=$(echo "$files" | grep 'apps/dsa-web/' || true)

    if [ -z "$web_files" ]; then
        return 0
    fi

    print_info "检查 TypeScript/JavaScript 文件..."

    cd apps/dsa-web

    # 运行 ESLint
    print_info "  运行 ESLint..."
    npm run lint || {
        print_error "ESLint 检查失败"
        cd - > /dev/null
        return 1
    }

    # 运行类型检查
    print_info "  运行 TypeScript 类型检查..."
    npm run type-check || {
        print_error "TypeScript 类型检查失败"
        cd - > /dev/null
        return 1
    }

    cd - > /dev/null

    print_success "TypeScript/JavaScript 文件检查通过"
}

# 检查 JSON/YAML 文件
check_config_files() {
    local files=$(get_changed_files | grep -E '\.(json|yaml|yml)$' || true)

    if [ -z "$files" ]; then
        return 0
    fi

    print_info "检查配置文件..."

    for file in $files; do
        if [ -f "$file" ]; then
            print_info "  验证 $file..."

            if [[ $file == *.json ]]; then
                $PYTHON_CMD -m json.tool "$file" > /dev/null || {
                    print_error "JSON 格式错误: $file"
                    return 1
                }
            elif [[ $file == *.yaml || $file == *.yml ]]; then
                if command -v yamllint &> /dev/null; then
                    yamllint "$file" || {
                        print_error "YAML 格式错误: $file"
                        return 1
                    }
                fi
            fi
        fi
    done

    print_success "配置文件检查通过"
}

# 运行快速测试
run_quick_tests() {
    print_info "运行快速测试..."

    # 检查是否有 Python 虚拟环境
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi

    # 运行 Python 测试（只运行单元测试）
    if command -v pytest &> /dev/null; then
        print_info "  运行后端单元测试..."
        pytest tests/ -v -m "not slow" --tb=line || {
            print_error "后端测试失败"
            return 1
        }
    fi

    # 运行前端测试（如果有修改）
    local js_files=$(get_changed_files | grep -E '\.(ts|tsx|js|jsx)$' | grep 'apps/dsa-web/' || true)
    if [ -n "$js_files" ]; then
        cd apps/dsa-web
        print_info "  运行前端测试..."
        npm run test:run || {
            print_error "前端测试失败"
            cd - > /dev/null
            return 1
        }
        cd - > /dev/null
    fi

    print_success "快速测试通过"
}

# 主函数
main() {
    print_info "========================================"
    print_info "Pre-commit 检查"
    print_info "========================================"

    # 解析命令行参数
    SKIP_TESTS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            *)
                ;;
        esac
    done

    # 检查文件
    check_python_files || exit 1
    check_js_files || exit 1
    check_config_files || exit 1

    # 运行快速测试（可选）
    if [ "$SKIP_TESTS" = false ]; then
        run_quick_tests || exit 1
    fi

    print_success "========================================"
    print_success "Pre-commit 检查通过！"
    print_success "========================================"
}

# 运行主函数
main "$@"
