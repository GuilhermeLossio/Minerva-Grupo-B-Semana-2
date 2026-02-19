"""Index page entrypoint."""

from __future__ import annotations

from services.auth_guard import ensure_authenticated
from ui.chat_ui import main as chat_main


def main() -> None:
    if not ensure_authenticated("index"):
        return
    chat_main(set_page_config=False)


if __name__ == "__main__":
    main()
