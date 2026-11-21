"""Fixture: Intentionally failing test suite case."""


def test_mandatory_encryption_enabled():
    """DEFECT: Test assertion fails, indicating broken contract."""
    encryption_status = False
    assert encryption_status is True, "Encryption at rest must be enabled for all data partitions"
