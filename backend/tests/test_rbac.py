"""
Tests for Role-Based Access Control (RBAC).
SPEC Section 5 compliant - testing role permissions.
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


class TestRoleCheckerUnit:
    """Unit tests for RoleChecker dependency."""

    def test_role_enum_values(self) -> None:
        """Test that UserRole enum has correct values."""
        from app.core.rbac import UserRole

        assert UserRole.USER == "user"
        assert UserRole.MODERATOR == "moderator"
        assert UserRole.ADMIN == "admin"

    def test_role_hierarchy_admin_includes_all(self) -> None:
        """Test that admin role includes all permissions."""
        from app.core.rbac import UserRole, has_required_role

        # Admin should pass all role checks
        assert has_required_role(UserRole.ADMIN, UserRole.USER) is True
        assert has_required_role(UserRole.ADMIN, UserRole.MODERATOR) is True
        assert has_required_role(UserRole.ADMIN, UserRole.ADMIN) is True

    def test_role_hierarchy_moderator_includes_user(self) -> None:
        """Test that moderator role includes user permissions."""
        from app.core.rbac import UserRole, has_required_role

        # Moderator should pass user and moderator checks
        assert has_required_role(UserRole.MODERATOR, UserRole.USER) is True
        assert has_required_role(UserRole.MODERATOR, UserRole.MODERATOR) is True
        assert has_required_role(UserRole.MODERATOR, UserRole.ADMIN) is False

    def test_role_hierarchy_user_only_user(self) -> None:
        """Test that user role only has user permissions."""
        from app.core.rbac import UserRole, has_required_role

        # User should only pass user checks
        assert has_required_role(UserRole.USER, UserRole.USER) is True
        assert has_required_role(UserRole.USER, UserRole.MODERATOR) is False
        assert has_required_role(UserRole.USER, UserRole.ADMIN) is False

    def test_role_checker_creation(self) -> None:
        """Test RoleChecker can be created with required role."""
        from app.core.rbac import RoleChecker, UserRole

        checker = RoleChecker(UserRole.MODERATOR)
        assert checker.required_role == UserRole.MODERATOR

    def test_role_checker_multiple_roles(self) -> None:
        """Test RoleChecker can be created with multiple required roles."""
        from app.core.rbac import RoleChecker, UserRole

        checker = RoleChecker(UserRole.MODERATOR, UserRole.ADMIN)
        assert UserRole.MODERATOR in checker.allowed_roles
        assert UserRole.ADMIN in checker.allowed_roles


class TestRoleCheckerIntegration:
    """Integration tests for RoleChecker with FastAPI endpoints."""

    @pytest.fixture
    def mock_user_data(self) -> dict:
        """Create mock user data."""
        return {
            "id": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "role": "user",
            "department": "Engineering",
            "balance": 1000.00,
        }

    def _create_app_with_mock_user(self, user_data: dict) -> FastAPI:
        """Create a test app with mocked user data."""
        from app.core.error_handlers import register_exception_handlers
        from app.core.rbac import RoleChecker, UserRole, get_current_user_data

        app = FastAPI()
        register_exception_handlers(app)

        # Override the dependency with mock data
        async def mock_get_current_user_data() -> dict:
            return user_data

        app.dependency_overrides[get_current_user_data] = mock_get_current_user_data

        # User-level endpoint
        @app.get("/user-only")
        async def user_only(
            user: dict = Depends(RoleChecker(UserRole.USER))
        ):
            return {"message": "User access granted", "user_id": user["id"]}

        # Moderator-level endpoint
        @app.get("/moderator-only")
        async def moderator_only(
            user: dict = Depends(RoleChecker(UserRole.MODERATOR))
        ):
            return {"message": "Moderator access granted", "user_id": user["id"]}

        # Admin-level endpoint
        @app.get("/admin-only")
        async def admin_only(
            user: dict = Depends(RoleChecker(UserRole.ADMIN))
        ):
            return {"message": "Admin access granted", "user_id": user["id"]}

        return app

    def test_user_can_access_user_endpoint(
        self, mock_user_data: dict
    ) -> None:
        """Test that user role can access user-level endpoints."""
        mock_user_data["role"] = "user"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)
        response = client.get("/user-only")

        assert response.status_code == 200
        assert response.json()["message"] == "User access granted"

    def test_user_cannot_access_moderator_endpoint(
        self, mock_user_data: dict
    ) -> None:
        """Test that user role cannot access moderator-level endpoints."""
        mock_user_data["role"] = "user"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)
        response = client.get("/moderator-only")

        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_user_cannot_access_admin_endpoint(
        self, mock_user_data: dict
    ) -> None:
        """Test that user role cannot access admin-level endpoints."""
        mock_user_data["role"] = "user"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)
        response = client.get("/admin-only")

        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_moderator_can_access_user_endpoint(
        self, mock_user_data: dict
    ) -> None:
        """Test that moderator role can access user-level endpoints."""
        mock_user_data["role"] = "moderator"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)
        response = client.get("/user-only")

        assert response.status_code == 200

    def test_moderator_can_access_moderator_endpoint(
        self, mock_user_data: dict
    ) -> None:
        """Test that moderator role can access moderator-level endpoints."""
        mock_user_data["role"] = "moderator"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)
        response = client.get("/moderator-only")

        assert response.status_code == 200

    def test_moderator_cannot_access_admin_endpoint(
        self, mock_user_data: dict
    ) -> None:
        """Test that moderator role cannot access admin-level endpoints."""
        mock_user_data["role"] = "moderator"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)
        response = client.get("/admin-only")

        assert response.status_code == 403

    def test_admin_can_access_all_endpoints(
        self, mock_user_data: dict
    ) -> None:
        """Test that admin role can access all endpoints."""
        mock_user_data["role"] = "admin"
        app = self._create_app_with_mock_user(mock_user_data)

        client = TestClient(app)

        # Admin can access user endpoint
        response = client.get("/user-only")
        assert response.status_code == 200

        # Admin can access moderator endpoint
        response = client.get("/moderator-only")
        assert response.status_code == 200

        # Admin can access admin endpoint
        response = client.get("/admin-only")
        assert response.status_code == 200

    def test_unauthenticated_request_returns_401(
        self,
    ) -> None:
        """Test that unauthenticated requests return 401."""
        from app.core.error_handlers import register_exception_handlers
        from app.core.exceptions import UnauthorizedError
        from app.core.rbac import RoleChecker, UserRole, get_current_user_data

        app = FastAPI()
        register_exception_handlers(app)

        # Override to raise UnauthorizedError
        async def mock_unauthorized() -> dict:
            raise UnauthorizedError()

        app.dependency_overrides[get_current_user_data] = mock_unauthorized

        @app.get("/user-only")
        async def user_only(
            user: dict = Depends(RoleChecker(UserRole.USER))
        ):
            return {"message": "User access granted"}

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/user-only")

        assert response.status_code == 401


class TestRolePermissionMatrix:
    """Test the complete role permission matrix from SPEC Section 5."""

    @pytest.mark.parametrize(
        "user_role,required_role,expected",
        [
            # User permissions
            ("user", "user", True),
            ("user", "moderator", False),
            ("user", "admin", False),
            # Moderator permissions
            ("moderator", "user", True),
            ("moderator", "moderator", True),
            ("moderator", "admin", False),
            # Admin permissions
            ("admin", "user", True),
            ("admin", "moderator", True),
            ("admin", "admin", True),
        ],
    )
    def test_role_permission_matrix(
        self, user_role: str, required_role: str, expected: bool
    ) -> None:
        """Test all combinations of user roles and required permissions."""
        from app.core.rbac import UserRole, has_required_role

        user_role_enum = UserRole(user_role)
        required_role_enum = UserRole(required_role)

        result = has_required_role(user_role_enum, required_role_enum)
        assert result is expected, (
            f"Expected {user_role} to {'have' if expected else 'not have'} "
            f"permission for {required_role}"
        )
