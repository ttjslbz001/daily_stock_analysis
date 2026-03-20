# Makefile for Daily Stock Analysis
# 使用说明: make help 查看可用命令

.PHONY: help
help: ## 显示帮助信息
	@echo "========================================"
	@echo "Daily Stock Analysis - Makefile"
	@echo "========================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "========================================"

.PHONY: install-backend
install-backend: ## 安装后端依赖
	@echo "安装后端依赖..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ 后端依赖安装完成"

.PHONY: install-frontend
install-frontend: ## 安装前端依赖
	@echo "安装前端依赖..."
	cd apps/dsa-web && npm install
	@echo "✅ 前端依赖安装完成"

.PHONY: install
install: install-backend install-frontend ## 安装所有依赖

.PHONY: test-backend
test-backend: ## 运行后端测试
	@echo "运行后端测试..."
	pytest tests/ -v --tb=short --cov=src --cov=api --cov-report=term-missing

.PHONY: test-frontend
test-frontend: ## 运行前端测试
	@echo "运行前端测试..."
	cd apps/dsa-web && npm run test:run

.PHONY: test-coverage-backend
test-coverage-backend: ## 运行后端测试覆盖率
	@echo "运行后端测试覆盖率..."
	pytest tests/ --cov=src --cov=api --cov-report=html --cov-report=term-missing --cov-fail-under=48
	@echo "✅ 覆盖率报告: htmlcov/index.html"

.PHONY: test-coverage-frontend
test-coverage-frontend: ## 运行前端测试覆盖率
	@echo "运行前端测试覆盖率..."
	cd apps/dsa-web && npm run test:coverage
	@echo "✅ 覆盖率报告: apps/dsa-web/coverage/index.html"

.PHONY: test-all
test-all: ## 运行所有测试
	@echo "运行所有测试..."
	./scripts/test-all.sh

.PHONY: test-quick
test-quick: ## 运行快速测试（跳过慢测试）
	@echo "运行快速测试..."
	pytest tests/ -v -m "not slow" --tb=line
	cd apps/dsa-web && npm run test:run

.PHONY: lint-backend
lint-backend: ## 检查后端代码风格
	@echo "检查后端代码风格..."
	flake8 src/ api/ --max-line-length=120 --ignore=E203,W503
	@echo "✅ 后端代码风格检查通过"

.PHONY: lint-frontend
lint-frontend: ## 检查前端代码风格
	@echo "检查前端代码风格..."
	cd apps/dsa-web && npm run lint
	@echo "✅ 前端代码风格检查通过"

.PHONY: type-check-backend
type-check-backend: ## 检查后端类型
	@echo "检查后端类型..."
	python -m py_compile src/storage.py
	python -m py_compile api/middlewares/error_handler.py
	python -m py_compile src/repositories/base.py
	find src api -name "*.py" -type f -exec python -m py_compile {} \;
	@echo "✅ 后端类型检查通过"

.PHONY: type-check-frontend
type-check-frontend: ## 检查前端类型
	@echo "检查前端类型..."
	cd apps/dsa-web && npm run type-check
	@echo "✅ 前端类型检查通过"

.PHONY: check
check: type-check-backend type-check-frontend lint-backend lint-frontend test-quick ## 运行所有检查

.PHONY: build-frontend
build-frontend: ## 构建前端
	@echo "构建前端..."
	cd apps/dsa-web && npm run build
	@echo "✅ 前端构建完成"

.PHONY: build-backend
build-backend: ## 构建后端
	@echo "构建后端..."
	@echo "✅ 后端无需构建（Python）"

.PHONY: build
build: build-backend build-frontend ## 构建所有项目

.PHONY: dev-backend
dev-backend: ## 启动后端开发服务器
	@echo "启动后端开发服务器..."
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend: ## 启动前端开发服务器
	@echo "启动前端开发服务器..."
	cd apps/dsa-web && npm run dev

.PHONY: dev
dev: dev-backend ## 启动后端开发服务器（默认）

.PHONY: clean
clean: ## 清理构建文件
	@echo "清理构建文件..."
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf apps/dsa-web/dist/
	rm -rf apps/dsa-web/node_modules/.vite
	@echo "✅ 清理完成"

.PHONY: clean-all
clean-all: clean ## 清理所有生成文件
	@echo "清理所有生成文件..."
	rm -rf apps/dsa-web/node_modules/
	rm -rf .venv/
	@echo "✅ 清理完成"

.PHONY: docker-build
docker-build: ## 构建 Docker 镜像
	@echo "构建 Docker 镜像..."
	docker build -t stock-analysis:latest -f docker/Dockerfile .
	@echo "✅ Docker 镜像构建完成"

.PHONY: docker-run
docker-run: ## 运行 Docker 容器
	@echo "运行 Docker 容器..."
	docker run --rm -p 8000:8000 stock-analysis:latest

.PHONY: pre-commit
pre-commit: ## 运行 pre-commit 检查
	@echo "运行 pre-commit 检查..."
	./scripts/pre-commit-check.sh

.PHONY: format-python
format-python: ## 格式化 Python 代码
	@echo "格式化 Python 代码..."
	black src/ api/
	isort src/ api/
	@echo "✅ Python 代码格式化完成"

.PHONY: format-frontend
format-frontend: ## 格式化前端代码
	@echo "格式化前端代码..."
	cd apps/dsa-web && npm run lint -- --fix
	@echo "✅ 前端代码格式化完成"

.PHONY: format
format: format-python format-frontend ## 格式化所有代码
