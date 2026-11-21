"""Fixture: Broken API response schema contract."""

from typing import Any


def serialize_user_response(user_model: Any) -> dict[str, Any]:
    """DEFECT: Breaks API contract by omitting mandatory 'account_status' and renaming 'user_id' to 'id'."""
    return {
        "id": user_model.id,
        "email": user_model.email,
        # Mandatory fields required by OpenAPI schema v2 missing:
        # "account_status": user_model.status,
        # "created_at": user_model.created_at.isoformat(),
    }
