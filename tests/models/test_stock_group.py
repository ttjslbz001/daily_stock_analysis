# -*- coding: utf-8 -*-
"""Unit tests for StockGroup model."""

import pytest
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.storage import Base, StockGroup


def test_stock_group_creation():
    """Test creating a stock group with valid data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    group = StockGroup(
        name="科技成长",
        description="高增长科技股票",
        stock_codes=json.dumps(["00700", "09988", "BABA"])
    )

    session.add(group)
    session.commit()

    assert group.id is not None
    assert group.name == "科技成长"
    assert group.description == "高增长科技股票"
    codes = json.loads(group.stock_codes)
    assert codes == ["00700", "09988", "BABA"]
    assert isinstance(group.created_at, datetime)

    session.close()


def test_stock_group_unique_name():
    """Test that group names must be unique."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    group1 = StockGroup(name="测试组", stock_codes="[]")
    group2 = StockGroup(name="测试组", stock_codes="[]")

    session.add(group1)
    session.commit()

    session.add(group2)
    with pytest.raises(Exception):  # IntegrityError
        session.commit()

    session.close()


def test_stock_group_default_values():
    """Test default values for optional fields."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    group = StockGroup(name="默认组", stock_codes='["600519"]')
    session.add(group)
    session.commit()

    assert group.sort_order == 0
    assert group.description is None

    session.close()
