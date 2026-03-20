# -*- coding: utf-8 -*-
"""Pydantic schemas for stock groups API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class GroupCreate(BaseModel):
    """Schema for creating a new group."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="分组名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="分组描述")
    stock_codes: List[str] = Field(default_factory=list, description="股票代码列表")
    sort_order: int = Field(0, description="排序顺序", ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "科技成长",
                "description": "高增长科技股票",
                "stock_codes": ["00700", "09988", "BABA"],
                "sort_order": 0
            }
        }
    }


class GroupUpdate(BaseModel):
    """Schema for updating a group."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, description="分组名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="分组描述")
    stock_codes: Optional[List[str]] = Field(None, description="股票代码列表")
    sort_order: Optional[int] = Field(None, description="排序顺序", ge=0)


class GroupResponse(BaseModel):
    """Schema for group response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分组ID")
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    stock_codes: List[str] = Field(..., description="股票代码列表")
    sort_order: int = Field(..., description="排序顺序")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class GroupListResponse(BaseModel):
    """Schema for group list response."""

    groups: List[GroupResponse] = Field(..., description="分组列表")


class BatchReorderRequest(BaseModel):
    """Schema for batch reorder request."""

    orders: List[dict] = Field(
        ...,
        description="排序更新列表，每项包含 id 和 sort_order",
        json_schema_extra={
            "example": [
                {"id": 1, "sort_order": 2},
                {"id": 2, "sort_order": 1}
            ]
        }
    )
