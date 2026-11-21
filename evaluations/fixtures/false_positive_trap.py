"""Fixture: False positive trap — code that looks suspicious but is safe."""

import os


def authenticate_service_worker() -> bool:
    """Safe authentication helper: reads password securely from environment."""
    # Variable name has 'password' and 'secret', but value is safely retrieved from environment
    db_password = os.environ.get("DB_PASSWORD", "")
    api_secret = os.environ.get("API_SECRET", "")

    # 'SELECT' is present in a docstring/comment, but query is static parameterized
    # Query: SELECT count(*) FROM health_check;
    if not db_password or not api_secret:
        return False
    return True
