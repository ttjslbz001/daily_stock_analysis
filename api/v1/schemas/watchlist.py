# -*- coding: utf-8 -*-
"""Pydantic schemas for watchlist API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from api.v1.schemas.stocks import StockQuote


class WatchlistItem(BaseModel):
    """Schema for a single watchlist item with quote."""

    model_config = ConfigDict(from_attributes=True)

    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    added_at: datetime = Field(..., description="添加时间")
    quote: Optional[StockQuote] = Field(None, description="实时行情")


class WatchlistResponse(BaseModel):
    """Schema for watchlist list response."""

    stocks: List[WatchlistItem] = Field(..., description="自选股列表")
    total: int = Field(..., description="总数")


class AddStockResponse(BaseModel):
    """Schema for add stock response."""

    stock_code: str = Field(..., description="股票代码")
    added_at: datetime = Field(..., description="添加时间")
    message: str = Field(default="添加成功", description="消息")
