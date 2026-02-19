"""Lightweight debug logging utilities."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Iterator


def _enabled() -> bool:
    value = os.getenv("Debug_log", "")
    if value.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    value = os.getenv("DEBUG", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def log(message: str) -> None:
    """Print a debug line to console when DEBUG is enabled."""
    if not _enabled():
        return
    timestamp = time.strftime("%H:%M:%S")
    print(f"[DEBUG {timestamp}] {message}")


@contextmanager
def time_block(label: str) -> Iterator[None]:
    """Log the elapsed time for a labeled block when DEBUG is enabled."""
    if not _enabled():
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        log(f"{label}: {elapsed_ms:.1f} ms")
