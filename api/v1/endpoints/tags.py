# -*- coding: utf-8 -*-
"""Stock tags API endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from api.v1.schemas.tags import TagCreate, TagListResponse, AllTagsResponse
from api.v1.schemas.common import ErrorResponse
from src.services.stock_tag_service import StockTagService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=AllTagsResponse,
    summary="获取所有标签",
    description="获取所有唯一标签名称，用于自动完成"
)
def get_all_tags():
    """Get all unique tags."""
    try:
        service = StockTagService()
        tags = service.get_all_tags()
        return AllTagsResponse(tags=tags)
    except Exception as e:
        logger.error(f"Failed to get all tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取标签列表失败"}
        )


@router.get(
    "/{stock_code}",
    response_model=TagListResponse,
    summary="获取股票标签",
    description="获取指定股票的所有标签"
)
def get_stock_tags(stock_code: str):
    """Get tags for a specific stock."""
    try:
        service = StockTagService()
        tags = service.get_tags(stock_code)
        return TagListResponse(tags=tags)
    except Exception as e:
        logger.error(f"Failed to get tags for {stock_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取股票标签失败"}
        )


@router.post(
    "/{stock_code}",
    response_model=TagListResponse,
    summary="添加股票标签",
    description="为指定股票添加一个标签"
)
def add_stock_tag(stock_code: str, body: TagCreate):
    """Add a tag to a stock."""
    try:
        service = StockTagService()
        service.add_tag(stock_code, body.tag_name)
        tags = service.get_tags(stock_code)
        return TagListResponse(tags=tags)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_tag", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Failed to add tag to {stock_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "添加标签失败"}
        )


@router.delete(
    "/{stock_code}/{tag_name}",
    response_model=TagListResponse,
    summary="删除股票标签",
    description="从指定股票删除一个标签"
)
def remove_stock_tag(stock_code: str, tag_name: str):
    """Remove a tag from a stock."""
    try:
        service = StockTagService()
        service.remove_tag(stock_code, tag_name)
        tags = service.get_tags(stock_code)
        return TagListResponse(tags=tags)
    except Exception as e:
        logger.error(f"Failed to remove tag from {stock_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "删除标签失败"}
        )
