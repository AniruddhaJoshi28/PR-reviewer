"""Fixture: Concurrency defect / race condition on shared mutable state."""

import threading
from typing import Any


class InflightTransactionTracker:
    def __init__(self) -> None:
        self.active_transactions: dict[str, float] = {}

    def record_debit(self, account_id: str, amount: float) -> None:
        """VULNERABILITY: Race condition.

        Concurrent debit transactions from multiple worker threads
        can interleave read and write without a Lock/Mutex, leading to double-spend.
        """
        current_balance = self.active_transactions.get(account_id, 1000.0)
        # Context switch here causes race condition
        self.active_transactions[account_id] = current_balance - amount
