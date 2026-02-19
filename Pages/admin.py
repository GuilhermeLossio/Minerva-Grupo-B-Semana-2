"""Admin page entrypoint."""

from __future__ import annotations

from services.auth_guard import ensure_authenticated
from ui.admin_ui import main as admin_main


def main() -> None:
    if not ensure_authenticated("admin"):
        return
    admin_main(set_page_config=False)


if __name__ == "__main__":
    main()
