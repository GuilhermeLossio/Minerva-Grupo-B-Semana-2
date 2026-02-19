"""Login page wrapper for legacy app entrypoints."""

from __future__ import annotations

from ui.login_ui import main as login_main


def render() -> None:
    login_main(set_page_config=False)

