"""Fixture: Authorization bypass in administrative endpoint."""

from typing import Any


class AdminService:
    def __init__(self, db: Any) -> None:
        self.db = db

    def delete_tenant_data(self, tenant_id: str, request_user: dict[str, Any]) -> bool:
        """VULNERABILITY: Missing authorization check.

        Any authenticated user can delete tenant data without checking role or ownership.
        """
        # Missing: if not request_user.get("is_admin") or request_user.get("tenant_id") != tenant_id: raise PermissionError()
        self.db.delete_all(tenant_id)
        return True
