"""
Activity Log Model - Chronological system activity logger.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ActivityItem:
    timestamp: str
    event: str
    category: str = "info"  # "voice", "chat", "system", "info"


class ActivityLogModel:
    """Model tracking activity log history."""

    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.logs: List[ActivityItem] = []
        self._init_empty_logs()

    def _init_empty_logs(self):
        """Start with a clean activity log."""
        self.logs = [
            ActivityItem(
                timestamp=datetime.now().strftime("%I:%M %p"),
                event="Hệ thống sẵn sàng",
                category="system"
            )
        ]

    def add_log(self, event: str, category: str = "info", timestamp: str = None) -> ActivityItem:
        if not timestamp:
            timestamp = datetime.now().strftime("%I:%M %p")
        item = ActivityItem(timestamp=timestamp, event=event, category=category)
        self.logs.append(item)
        if len(self.logs) > self.max_items:
            self.logs.pop(0)
        return item

    def get_logs(self) -> List[ActivityItem]:
        return list(reversed(self.logs))
