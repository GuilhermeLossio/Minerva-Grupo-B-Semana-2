"""Login page entrypoint."""

from __future__ import annotations

from ui.login_ui import main as login_main


def main() -> None:
    login_main(set_page_config=False)

if __name__ == "__main__":
    main()