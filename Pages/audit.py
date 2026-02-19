"""Audit page entrypoint."""

from __future__ import annotations

from services.auth_guard import ensure_authenticated
from ui.compliance_ui import main as audit_main


def main() -> None:
    if not ensure_authenticated("audit"):
        return
    audit_main(set_page_config=False)


if __name__ == "__main__":
    main()
