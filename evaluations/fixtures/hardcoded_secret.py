"""Fixture: Hardcoded secrets and cloud credentials."""

import os
from typing import Any

# VULNERABILITY: Hardcoded AWS credential in source code
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


def init_s3_client() -> Any:
    """Connect to S3 using hardcoded credentials."""
    import boto3

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
