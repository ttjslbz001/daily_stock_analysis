# -*- coding: utf-8 -*-
"""
===================================
关注股票 API 模型
===================================

职责：
1. 定义关注股票相关的 Pydantic 模型
2. 定义请求和响应结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class BollingerBands(BaseModel):
    """布林线指标"""
    upper: float = Field(..., description="布林线上轨")
    middle: float = Field(..., description="布林线中轨")
    lower: float = Field(..., description="布林线下轨")


class MACD(BaseModel):
    """MACD 指标"""
    dif: float = Field(..., description="DIF 快线")
    dea: float = Field(..., description="DEA 慢线")
    bar: float = Field(..., description="MACD 柱状图")


class RSI(BaseModel):
    """RSI 指标"""
    rsi6: float = Field(..., description="RSI(6) 短期")
    rsi12: float = Field(..., description="RSI(12) 中期")
    rsi24: float = Field(..., description="RSI(24) 长期")


class KDJ(BaseModel):
    """KDJ 指标"""
    k: float = Field(..., description="K 值")
    d: float = Field(..., description="D 值")
    j: float = Field(..., description="J 值")


class WatchedStockResponse(BaseModel):
    """关注股票响应"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    change: Optional[float] = Field(None, description="涨跌额")
    change_percent: Optional[float] = Field(None, description="涨跌幅（%）")
    year_high: Optional[float] = Field(None, description="一年内最高价")
    year_low: Optional[float] = Field(None, description="一年内最低价")
    bollinger: BollingerBands = Field(..., description="布林线指标")
    macd: MACD = Field(..., description="MACD 指标")
    rsi: RSI = Field(..., description="RSI 指标")
    kdj: KDJ = Field(..., description="KDJ 指标")
    volume: float = Field(..., description="当日成交量")
    updated_at: datetime = Field(..., description="更新时间")


class WatchedStocksListResponse(BaseModel):
    """关注股票列表响应"""
    total: int = Field(..., description="总数")
    items: List[WatchedStockResponse] = Field(..., description="关注股票列表")


class AddWatchedStockRequest(BaseModel):
    """添加关注股票请求"""
    stock_code: str = Field(..., min_length=1, max_length=20, description="股票代码")
    stock_name: Optional[str] = Field(None, max_length=100, description="股票名称（可选）")


class AddWatchedStockResponse(BaseModel):
    """添加关注股票响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    stock_code: str = Field(..., description="股票代码")


class RemoveWatchedStockResponse(BaseModel):
    """取消关注股票响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    stock_code: str = Field(..., description="股票代码")
