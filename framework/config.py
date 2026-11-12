"""Test settings.

Every value has a default for the public demo site. You can change any value
with an environment variable, for example to run the tests against your own
copy of the Toolshop app.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ui_url: str
    api_url: str
    http_timeout: float
    ui_timeout_ms: int
    # The public demo resets its data every hour. Set AVOID_DEMO_RESET=0 for your own copy.
    avoid_demo_reset: bool

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            ui_url=os.getenv("UI_URL", "https://practicesoftwaretesting.com").rstrip("/"),
            api_url=os.getenv("API_URL", "https://api.practicesoftwaretesting.com").rstrip("/"),
            http_timeout=float(os.getenv("HTTP_TIMEOUT", "15")),
            ui_timeout_ms=int(os.getenv("UI_TIMEOUT_MS", "10000")),
            avoid_demo_reset=os.getenv("AVOID_DEMO_RESET", "1") != "0",
        )
