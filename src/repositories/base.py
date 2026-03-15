# -*- coding: utf-8 -*-
"""
===================================
基础 Repository 类
===================================

职责：
1. 提供通用的数据库操作方法
2. 封装常见的查询和 CRUD 操作
3. 减少代码重复
4. 提供统一的错误处理
"""

import logging
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from datetime import datetime

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.storage import DatabaseManager

logger = logging.getLogger(__name__)

# 泛型类型变量
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    基础 Repository 类

    提供通用的数据库操作方法，所有具体的 Repository 都应该继承此类。

    特性:
    - 通用的 CRUD 操作
    - 自动错误处理和日志记录
    - 支持 Session 上下文管理
    - 类型安全的查询构建
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化 Repository

        Args:
            model: SQLAlchemy 模型类
        """
        self._model = model
        self._db = DatabaseManager.get_instance()

    def get_session(self, auto_commit: bool = True):
        """
        获取数据库会话

        Args:
            auto_commit: 是否自动提交

        Returns:
            SessionContext: 会话上下文管理器
        """
        return self._db.get_session(auto_commit=auto_commit)

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据 ID 获取单个记录

        Args:
            id: 记录 ID

        Returns:
            Optional[ModelType]: 找到的记录，未找到返回 None
        """
        with self.get_session(auto_commit=False) as session:
            try:
                result = session.execute(
                    select(self._model).where(self._model.id == id)
                )
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(f"查询 {self._model.__name__} ID {id} 失败: {e}")
                raise

    def get_by_field(
        self,
        field_name: str,
        field_value: Any
    ) -> Optional[ModelType]:
        """
        根据字段获取单个记录

        Args:
            field_name: 字段名
            field_value: 字段值

        Returns:
            Optional[ModelType]: 找到的记录，未找到返回 None
        """
        with self.get_session(auto_commit=False) as session:
            try:
                field = getattr(self._model, field_name)
                result = session.execute(
                    select(self._model).where(field == field_value)
                )
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(
                    f"查询 {self._model.__name__} by {field_name}={field_value} 失败: {e}"
                )
                raise

    def get_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """
        获取所有记录

        Args:
            limit: 限制返回数量
            offset: 偏移量
            order_by: 排序字段
            desc: 是否降序

        Returns:
            List[ModelType]: 记录列表
        """
        with self.get_session(auto_commit=False) as session:
            try:
                query = select(self._model)

                if order_by:
                    order_field = getattr(self._model, order_by)
                    query = query.order_by(
                        order_field.desc() if desc else order_field
                    )

                query = query.offset(offset)

                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                return list(result.scalars().all())
            except SQLAlchemyError as e:
                logger.error(f"查询 {self._model.__name__} 列表失败: {e}")
                raise

    def filter(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ModelType]:
        """
        根据条件过滤记录

        Args:
            filters: 过滤条件字典 {字段名: 值}
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            List[ModelType]: 过滤后的记录列表
        """
        with self.get_session(auto_commit=False) as session:
            try:
                query = select(self._model)

                for field_name, field_value in filters.items():
                    field = getattr(self._model, field_name)
                    query = query.where(field == field_value)

                query = query.offset(offset)

                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                return list(result.scalars().all())
            except SQLAlchemyError as e:
                logger.error(f"过滤 {self._model.__name__} 失败: {e}")
                raise

    def create(self, **kwargs) -> ModelType:
        """
        创建新记录

        Args:
            **kwargs: 模型字段值

        Returns:
            ModelType: 创建的记录
        """
        with self.get_session() as session:
            try:
                obj = self._model(**kwargs)
                session.add(obj)
                session.flush()
                session.refresh(obj)
                logger.info(f"创建 {self._model.__name__}: {obj}")
                return obj
            except SQLAlchemyError as e:
                logger.error(f"创建 {self._model.__name__} 失败: {e}")
                raise

    def update(
        self,
        id: int,
        **kwargs
    ) -> Optional[ModelType]:
        """
        更新记录

        Args:
            id: 记录 ID
            **kwargs: 要更新的字段和值

        Returns:
            Optional[ModelType]: 更新后的记录
        """
        with self.get_session() as session:
            try:
                query = update(self._model).where(
                    self._model.id == id
                ).values(**kwargs)

                result = session.execute(query)
                if result.rowcount == 0:
                    return None

                session.flush()
                # 重新获取更新后的对象
                updated_obj = session.execute(
                    select(self._model).where(self._model.id == id)
                ).scalar_one()
                logger.info(f"更新 {self._model.__name__} ID {id}: {updated_obj}")
                return updated_obj
            except SQLAlchemyError as e:
                logger.error(f"更新 {self._model.__name__} ID {id} 失败: {e}")
                raise

    def delete(self, id: int) -> bool:
        """
        删除记录

        Args:
            id: 记录 ID

        Returns:
            bool: 是否删除成功
        """
        with self.get_session() as session:
            try:
                query = delete(self._model).where(self._model.id == id)
                result = session.execute(query)
                success = result.rowcount > 0
                if success:
                    logger.info(f"删除 {self._model.__name__} ID {id}")
                return success
            except SQLAlchemyError as e:
                logger.error(f"删除 {self._model.__name__} ID {id} 失败: {e}")
                raise

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        计算记录数量

        Args:
            filters: 过滤条件（可选）

        Returns:
            int: 记录数量
        """
        with self.get_session(auto_commit=False) as session:
            try:
                query = select(func.count(self._model.id))

                if filters:
                    for field_name, field_value in filters.items():
                        field = getattr(self._model, field_name)
                        query = query.where(field == field_value)

                result = session.execute(query)
                return result.scalar()
            except SQLAlchemyError as e:
                logger.error(f"计算 {self._model.__name__} 数量失败: {e}")
                raise

    def exists(self, id: int) -> bool:
        """
        检查记录是否存在

        Args:
            id: 记录 ID

        Returns:
            bool: 是否存在
        """
        return self.count({"id": id}) > 0

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        批量创建记录

        Args:
            items: 字段值字典列表

        Returns:
            List[ModelType]: 创建的记录列表
        """
        with self.get_session() as session:
            try:
                objects = [self._model(**item) for item in items]
                session.add_all(objects)
                session.flush()
                for obj in objects:
                    session.refresh(obj)
                logger.info(f"批量创建 {len(objects)} 个 {self._model.__name__}")
                return objects
            except SQLAlchemyError as e:
                logger.error(f"批量创建 {self._model.__name__} 失败: {e}")
                raise
