"""
Tests for Category model and API.
SPEC Section 4 & 5 compliant.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestCategoryModel:
    """Unit tests for Category model (SPEC Section 4)."""

    def test_category_has_uuid_id_column(self) -> None:
        """Test that Category has UUID id column."""
        from app.models.category import Category

        assert hasattr(Category, "id")

    def test_category_has_name_field(self) -> None:
        """Test that Category has name field (VARCHAR 50)."""
        from app.models.category import Category

        assert hasattr(Category, "name")

    def test_category_has_description_field(self) -> None:
        """Test that Category has description field (TEXT)."""
        from app.models.category import Category

        assert hasattr(Category, "description")

    def test_category_has_sort_order_field(self) -> None:
        """Test that Category has sort_order field (INT)."""
        from app.models.category import Category

        assert hasattr(Category, "sort_order")

    def test_category_table_name(self) -> None:
        """Test that Category table name is 'categories'."""
        from app.models.category import Category

        assert Category.__tablename__ == "categories"


class TestCategoryModelDatabase:
    """Database integration tests for Category model."""

    @pytest.fixture
    async def db_session(self):
        """Create a test database session."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.db.base import Base

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_create_category(self, db_session: AsyncSession) -> None:
        """Test creating a category."""
        from app.models.category import Category

        category = Category(
            name="Product",
            description="Product related predictions",
            sort_order=1,
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        assert category.id is not None
        assert isinstance(category.id, uuid.UUID)
        assert category.name == "Product"
        assert category.description == "Product related predictions"
        assert category.sort_order == 1

    @pytest.mark.asyncio
    async def test_category_defaults(self, db_session: AsyncSession) -> None:
        """Test category default values."""
        from app.models.category import Category

        category = Category(name="Test")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        assert category.id is not None
        assert category.sort_order == 0  # Default sort order

    @pytest.mark.asyncio
    async def test_category_name_unique(self, db_session: AsyncSession) -> None:
        """Test that category name is unique."""
        from sqlalchemy.exc import IntegrityError

        from app.models.category import Category

        category1 = Category(name="Unique", sort_order=1)
        db_session.add(category1)
        await db_session.commit()

        category2 = Category(name="Unique", sort_order=2)
        db_session.add(category2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_list_categories_ordered_by_sort_order(
        self, db_session: AsyncSession
    ) -> None:
        """Test that categories are ordered by sort_order."""
        from app.models.category import Category

        # Create categories in random order
        cat_c = Category(name="Category C", sort_order=3)
        cat_a = Category(name="Category A", sort_order=1)
        cat_b = Category(name="Category B", sort_order=2)

        db_session.add_all([cat_c, cat_a, cat_b])
        await db_session.commit()

        # Query ordered by sort_order
        result = await db_session.execute(
            select(Category).order_by(Category.sort_order)
        )
        categories = result.scalars().all()

        assert len(categories) == 3
        assert categories[0].name == "Category A"
        assert categories[1].name == "Category B"
        assert categories[2].name == "Category C"


class TestCategoryAPI:
    """Integration tests for Category API endpoints."""

    @pytest.fixture
    def mock_user_data(self) -> dict:
        """Create mock user data."""
        return {
            "id": str(uuid.uuid4()),
            "email": "user@example.com",
            "name": "Test User",
            "role": "user",
            "department": "Engineering",
            "balance": 1000.00,
        }

    @pytest.fixture
    def mock_admin_data(self) -> dict:
        """Create mock admin data."""
        return {
            "id": str(uuid.uuid4()),
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "admin",
            "department": "Engineering",
            "balance": 1000.00,
        }

    @pytest.fixture
    async def db_session(self):
        """Create a test database session."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.db.base import Base

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            yield session

        await engine.dispose()

    def _create_test_app(self, db_session: AsyncSession, user_data: dict) -> FastAPI:
        """Create a test FastAPI app with mocked dependencies."""
        from app.api.categories import router as categories_router
        from app.core.error_handlers import register_exception_handlers
        from app.core.rbac import get_current_user_data
        from app.db.session import get_db

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(categories_router, prefix="/api/v1")

        # Override dependencies
        async def mock_get_db():
            yield db_session

        async def mock_get_user():
            return user_data

        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[get_current_user_data] = mock_get_user

        return app

    @pytest.mark.asyncio
    async def test_list_categories_empty(
        self, db_session: AsyncSession, mock_user_data: dict
    ) -> None:
        """Test listing categories when none exist."""
        app = self._create_test_app(db_session, mock_user_data)
        client = TestClient(app)

        response = client.get("/api/v1/categories")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_categories_with_data(
        self, db_session: AsyncSession, mock_user_data: dict
    ) -> None:
        """Test listing categories with data."""
        from app.models.category import Category

        # Create test categories
        cat1 = Category(name="Product", description="Product predictions", sort_order=1)
        cat2 = Category(name="Sales", description="Sales predictions", sort_order=2)
        db_session.add_all([cat1, cat2])
        await db_session.commit()

        app = self._create_test_app(db_session, mock_user_data)
        client = TestClient(app)

        response = client.get("/api/v1/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Product"
        assert data[1]["name"] == "Sales"

    @pytest.mark.asyncio
    async def test_create_category_as_admin(
        self, db_session: AsyncSession, mock_admin_data: dict
    ) -> None:
        """Test creating a category as admin."""
        app = self._create_test_app(db_session, mock_admin_data)
        client = TestClient(app)

        response = client.post(
            "/api/v1/categories",
            json={
                "name": "New Category",
                "description": "Test description",
                "sort_order": 5,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Category"
        assert data["description"] == "Test description"
        assert data["sort_order"] == 5
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_category_as_user_forbidden(
        self, db_session: AsyncSession, mock_user_data: dict
    ) -> None:
        """Test that regular users cannot create categories."""
        app = self._create_test_app(db_session, mock_user_data)
        client = TestClient(app)

        response = client.post(
            "/api/v1/categories",
            json={
                "name": "New Category",
                "description": "Test description",
            },
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name(
        self, db_session: AsyncSession, mock_admin_data: dict
    ) -> None:
        """Test creating a category with duplicate name."""
        from app.models.category import Category

        # Create existing category
        existing = Category(name="Existing", sort_order=1)
        db_session.add(existing)
        await db_session.commit()

        app = self._create_test_app(db_session, mock_admin_data)
        client = TestClient(app)

        response = client.post(
            "/api/v1/categories",
            json={"name": "Existing", "sort_order": 2},
        )

        assert response.status_code == 422
        assert "already exists" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_create_category_default_sort_order(
        self, db_session: AsyncSession, mock_admin_data: dict
    ) -> None:
        """Test creating a category with default sort_order."""
        app = self._create_test_app(db_session, mock_admin_data)
        client = TestClient(app)

        response = client.post(
            "/api/v1/categories",
            json={"name": "Minimal Category"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["sort_order"] == 0  # Default


class TestCategorySchemas:
    """Tests for Category Pydantic schemas."""

    def test_category_response_schema(self) -> None:
        """Test CategoryResponse schema."""
        from app.schemas.category import CategoryResponse

        data = CategoryResponse(
            id=uuid.uuid4(),
            name="Test",
            description="Test desc",
            sort_order=1,
        )
        assert data.name == "Test"

    def test_category_create_schema_minimal(self) -> None:
        """Test CategoryCreate schema with minimal data."""
        from app.schemas.category import CategoryCreate

        data = CategoryCreate(name="Test")
        assert data.name == "Test"
        assert data.description is None
        assert data.sort_order == 0

    def test_category_create_schema_full(self) -> None:
        """Test CategoryCreate schema with all fields."""
        from app.schemas.category import CategoryCreate

        data = CategoryCreate(
            name="Full",
            description="Full description",
            sort_order=10,
        )
        assert data.name == "Full"
        assert data.description == "Full description"
        assert data.sort_order == 10
