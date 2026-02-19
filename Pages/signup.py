"""Public sign-up page entrypoint."""

from __future__ import annotations

from ui.signup_ui import main as signup_main


def main() -> None:
    signup_main(set_page_config=False)


if __name__ == "__main__":
    main()
