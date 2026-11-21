"""Fixture: Raw SQL injection via string formatting."""

from typing import Any


def get_user_records(db_connection: Any, tenant_id: str, search_query: str) -> list[dict[str, Any]]:
    """VULNERABILITY: User input formatted directly into raw SQL."""
    # Defect: Direct interpolation allows SQL injection
    sql = f"SELECT id, username, email FROM users WHERE tenant_id = '{tenant_id}' AND username LIKE '%{search_query}%'"
    cursor = db_connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()
