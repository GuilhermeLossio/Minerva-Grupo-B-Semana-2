"""Central route definitions for the UI layer."""

from __future__ import annotations

from typing import Dict

ROUTES: Dict[str, Dict[str, object]] = {
    "index": {
        "title": "App",
        "module": "Pages.index",
        "callable": "main",
        "roles": ["ADMIN", "NORMAL", "COMPLIANCE"],
    },
    "login": {
        "title": "Login",
        "module": "Pages.login",
        "callable": "main",
    },
    "admin": {
        "title": "SQL Admin",
        "module": "Pages.admin",
        "callable": "main",
        "roles": ["ADMIN"],
    },
}

DEFAULT_ROUTE = "index"
