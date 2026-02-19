"""Users page entrypoint."""

from __future__ import annotations

from services.auth_guard import ensure_authenticated
from ui.user_registration_ui import main as users_main


def main() -> None:
    if not ensure_authenticated("users"):
        return
    users_main(set_page_config=False)


if __name__ == "__main__":
    main()
