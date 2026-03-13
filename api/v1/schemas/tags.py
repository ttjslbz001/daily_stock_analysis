# -*- coding: utf-8 -*-
"""Pydantic schemas for stock tags API."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, ConfigDict


class TagCreate(BaseModel):
    """Schema for adding a tag to a stock."""

    model_config = ConfigDict(populate_by_name=True)

    tag_name: str = Field(..., description="标签名称", min_length=1, max_length=50)


class TagListResponse(BaseModel):
    """Schema for tag list response."""

    tags: List[str] = Field(..., description="标签列表")


class AllTagsResponse(BaseModel):
    """Schema for all unique tags response."""

    tags: List[str] = Field(..., description="所有唯一标签")
