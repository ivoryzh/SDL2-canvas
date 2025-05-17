import os
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api import app
from sqlalchemy_models import Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
async def test_client():
    """Create a test client for the FastAPI application."""
    async with app.test_client() as client:
        yield client

@pytest.fixture
def test_workflow_data():
    """Sample workflow data for testing."""
    return {
        "name": "Test_Workflow",
        "description": "Test workflow for unit testing",
        "operations": [
            {
                "id": "test_cv",
                "type": "uo_sdl2_cv",
                "params": {
                    "v_range": [-0.5, 0.5],
                    "freq": 0.1
                }
            }
        ]
    }

@pytest.fixture
def test_csv_data():
    """Sample CSV data for testing."""
    return {
        "time": [0, 1, 2, 3, 4],
        "voltage": [-0.5, -0.25, 0, 0.25, 0.5],
        "current": [0.1, 0.2, 0.3, 0.2, 0.1]
    } 