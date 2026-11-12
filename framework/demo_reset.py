"""Protection against the hourly reset of the public demo database.

The demo site rebuilds its database at the start of every hour (UTC). For a
short time the data is missing, and after the reset every product has a new id.
A test run that crosses this moment fails for no real reason. So we do not
start a run shortly before the reset, and after the reset we wait until the
data is back.
"""

from __future__ import annotations

from datetime import datetime, timedelta

# How long the reset can take. Do not start tests earlier than this after the hour.
RESET_TIME = timedelta(seconds=60)
# A full run takes less than this. Do not start a run closer than this to the next reset.
MAX_RUN_TIME = timedelta(minutes=2)

HOUR = timedelta(hours=1)


def time_until_safe_start(now: datetime) -> timedelta:
    """How long to wait before a test run can start. Zero if it can start now."""
    since_reset = timedelta(minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    if since_reset < RESET_TIME:
        return RESET_TIME - since_reset
    until_next_reset = HOUR - since_reset
    if until_next_reset < MAX_RUN_TIME:
        return until_next_reset + RESET_TIME
    return timedelta(0)
