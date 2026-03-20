# -*- coding: utf-8 -*-
"""Stock groups API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from api.v1.schemas.groups import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupListResponse,
    BatchReorderRequest
)
from api.v1.schemas.common import ErrorResponse
from src.services.stock_group_service import StockGroupService

logger = logging.getLogger(__name__)

router = APIRouter()


def _group_to_response(group) -> GroupResponse:
    """Convert StockGroup model to response schema."""
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        stock_codes=group.get_stock_codes(),
        sort_order=group.sort_order,
        created_at=group.created_at,
        updated_at=group.updated_at
    )


@router.get(
    "/",
    response_model=GroupListResponse,
    summary="获取所有分组",
    description="获取所有股票分组，按 sort_order 排序"
)
def list_groups():
    """List all stock groups."""
    try:
        service = StockGroupService()
        groups = service.get_all_groups()
        return GroupListResponse(
            groups=[_group_to_response(g) for g in groups]
        )
    except Exception as e:
        logger.error(f"Failed to list groups: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取分组列表失败"}
        )


@router.post(
    "/",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "分组名称已存在", "model": ErrorResponse}
    },
    summary="创建新分组",
    description="创建一个新的股票分组"
)
def create_group(body: GroupCreate):
    """Create a new stock group."""
    try:
        service = StockGroupService()
        group = service.create_group(
            name=body.name,
            description=body.description,
            stock_codes=body.stock_codes,
            sort_order=body.sort_order
        )
        return _group_to_response(group)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "duplicate_name", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Failed to create group: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "创建分组失败"}
        )


@router.put(
    "/{group_id}",
    response_model=GroupResponse,
    responses={
        404: {"description": "分组不存在", "model": ErrorResponse}
    },
    summary="更新分组",
    description="更新指定分组的信息"
)
def update_group(group_id: int, body: GroupUpdate):
    """Update an existing group."""
    try:
        service = StockGroupService()
        group = service.update_group(
            group_id=group_id,
            name=body.name,
            description=body.description,
            stock_codes=body.stock_codes,
            sort_order=body.sort_order
        )

        if not group:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": f"分组 {group_id} 不存在"}
            )

        return _group_to_response(group)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update group: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "更新分组失败"}
        )


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "分组不存在", "model": ErrorResponse}
    },
    summary="删除分组",
    description="删除指定的股票分组"
)
def delete_group(group_id: int):
    """Delete a group."""
    try:
        service = StockGroupService()
        deleted = service.delete_group(group_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": f"分组 {group_id} 不存在"}
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete group: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "删除分组失败"}
        )


@router.post(
    "/batch-reorder",
    status_code=status.HTTP_200_OK,
    summary="批量重排序",
    description="批量更新多个分组的排序顺序"
)
def batch_reorder(body: BatchReorderRequest):
    """Batch update sort orders."""
    try:
        service = StockGroupService()
        service.batch_reorder(body.orders)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Failed to batch reorder: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "批量重排序失败"}
        )


@router.get(
    "/{group_id}/stocks",
    summary="获取分组股票详情",
    description="获取指定分组中所有股票的详细信息（含实时行情）"
)
def get_group_stocks(group_id: int):
    """Get detailed stock information for a group."""
    try:
        service = StockGroupService()
        group = service.get_group_by_id(group_id)

        if not group:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": f"分组 {group_id} 不存在"}
            )

        # Get stock details
        from src.services.stock_service import StockService
        stock_service = StockService()

        stocks = []
        for code in group.get_stock_codes():
            quote = stock_service.get_realtime_quote(code)
            stocks.append({
                "code": code,
                "name": quote.get("stock_name") if quote else None,
                "quote": quote
            })

        return {
            "group": _group_to_response(group),
            "stocks": stocks
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get group stocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取分组股票失败"}
        )
