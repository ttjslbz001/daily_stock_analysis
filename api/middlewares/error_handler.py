# -*- coding: utf-8 -*-
"""
===================================
全局异常处理中间件
===================================

职责：
1. 捕获未处理的异常
2. 统一错误响应格式
3. 记录错误日志
4. 提供错误追踪和调试信息
"""

import logging
import traceback
from typing import Callable, Optional, Any
from datetime import datetime

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorCode:
    """错误码定义"""

    # 通用错误
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    BAD_REQUEST = "bad_request"

    # 数据库错误
    DATABASE_ERROR = "database_error"
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    DUPLICATE_KEY_ERROR = "duplicate_key_error"

    # 权限错误
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"

    # 业务逻辑错误
    INVALID_PARAMETER = "invalid_parameter"
    OPERATION_FAILED = "operation_failed"
    RESOURCE_CONFLICT = "resource_conflict"

    # 服务错误
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"


def create_error_response(
    error_code: str,
    message: str,
    detail: Optional[Any] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    创建统一的错误响应

    Args:
        error_code: 错误码
        message: 错误消息
        detail: 错误详情（可选）
        status_code: HTTP 状态码
        request_id: 请求 ID（可选）

    Returns:
        JSONResponse: 错误响应
    """
    content: dict[str, Any] = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if detail is not None:
        content["detail"] = detail

    if request_id:
        content["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=content)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    全局异常处理中间件

    捕获所有未处理的异常，返回统一格式的错误响应

    特性:
    - 记录详细的错误日志
    - 根据环境返回不同详细程度的错误信息
    - 支持请求追踪 ID
    """

    def __init__(self, app, debug: bool = False):
        """
        初始化中间件

        Args:
            app: FastAPI 应用
            debug: 是否启用调试模式（详细错误信息）
        """
        super().__init__(app)
        self._debug = debug

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        处理请求，捕获异常

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            Response: 响应对象
        """
        request_id = request.headers.get("X-Request-ID", self._generate_request_id())

        try:
            response = await call_next(request)
            # 添加请求 ID 到响应头
            response.headers["X-Request-ID"] = request_id
            return response

        except HTTPException as e:
            # HTTP 异常已经处理过，直接传递
            logger.warning(
                f"HTTP 异常: {e.status_code} {e.detail} | "
                f"路径: {request.url.path} | "
                f"方法: {request.method} | "
                f"请求 ID: {request_id}"
            )
            raise

        except ValidationError as e:
            # Pydantic 验证错误
            logger.warning(
                f"验证错误: {e} | "
                f"路径: {request.url.path} | "
                f"方法: {request.method} | "
                f"请求 ID: {request_id}"
            )
            return create_error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="请求参数验证失败",
                detail=e.errors(),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                request_id=request_id
            )

        except SQLAlchemyError as e:
            # 数据库错误
            logger.error(
                f"数据库错误: {e} | "
                f"路径: {request.url.path} | "
                f"方法: {request.method} | "
                f"请求 ID: {request_id} | "
                f"堆栈: {traceback.format_exc()}"
            )
            return create_error_response(
                error_code=ErrorCode.DATABASE_ERROR,
                message="数据库操作失败，请稍后重试",
                detail=str(e) if self._debug else None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=request_id
            )

        except Exception as e:
            # 其他未处理的异常
            logger.error(
                f"未处理的异常: {e} | "
                f"类型: {type(e).__name__} | "
                f"路径: {request.url.path} | "
                f"方法: {request.method} | "
                f"请求 ID: {request_id} | "
                f"堆栈: {traceback.format_exc()}"
            )
            return create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="服务器内部错误，请稍后重试",
                detail=str(e) if self._debug else None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=request_id
            )

    @staticmethod
    def _generate_request_id() -> str:
        """生成唯一的请求 ID"""
        import uuid
        return str(uuid.uuid4())


def add_error_handlers(app, debug: bool = False) -> None:
    """
    添加全局异常处理器

    为 FastAPI 应用添加各类异常的处理器，确保错误响应格式统一

    Args:
        app: FastAPI 应用实例
        debug: 是否启用调试模式（详细错误信息）
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 HTTP 异常"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        # 如果 detail 已经是统一格式的 dict，直接使用
        if isinstance(exc.detail, dict) and "error" in exc.detail and "message" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )

        # 否则将 detail 包装成统一格式
        logger.warning(
            f"HTTP 异常: {exc.status_code} | "
            f"消息: {exc.detail} | "
            f"路径: {request.url.path} | "
            f"请求 ID: {request_id}"
        )

        return create_error_response(
            error_code=ErrorCode.BAD_REQUEST
            if exc.status_code == status.HTTP_400_BAD_REQUEST
            else ErrorCode.FORBIDDEN
            if exc.status_code == status.HTTP_403_FORBIDDEN
            else ErrorCode.NOT_FOUND
            if exc.status_code == status.HTTP_404_NOT_FOUND
            else ErrorCode.UNAUTHORIZED
            if exc.status_code == status.HTTP_401_UNAUTHORIZED
            else ErrorCode.INTERNAL_ERROR,
            message=str(exc.detail) if exc.detail else "请求处理失败",
            status_code=exc.status_code,
            request_id=request_id
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证异常"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        logger.warning(
            f"验证错误: {exc.errors()} | "
            f"路径: {request.url.path} | "
            f"请求 ID: {request_id}"
        )

        return create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="请求参数验证失败",
            detail=exc.errors(),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            request_id=request_id
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """处理数据库异常"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        logger.error(
            f"数据库异常: {exc} | "
            f"路径: {request.url.path} | "
            f"请求 ID: {request_id} | "
            f"堆栈: {traceback.format_exc()}"
        )

        return create_error_response(
            error_code=ErrorCode.DATABASE_ERROR,
            message="数据库操作失败，请稍后重试",
            detail=str(exc) if debug else None,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理通用异常"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        logger.error(
            f"未处理的异常: {exc} | "
            f"类型: {type(exc).__name__} | "
            f"路径: {request.url.path} | "
            f"请求 ID: {request_id} | "
            f"堆栈: {traceback.format_exc()}"
        )

        return create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="服务器内部错误，请稍后重试",
            detail=str(exc) if debug else None,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id
        )
