"""Theme helpers shared across pages."""

from __future__ import annotations

import streamlit as st

from ui.chat_markup import build_theme_css


_DARK_MODE_KEY = "dark_mode"


def init_theme_state() -> None:
    """Ensure the theme preference exists in session state."""
    if _DARK_MODE_KEY not in st.session_state:
        st.session_state[_DARK_MODE_KEY] = True


def apply_theme(dark_mode: bool) -> None:
    """Render theme CSS based on the selected mode."""
    if dark_mode:
        colors = {
            "app_bg": (
                "radial-gradient(1200px circle at 12% -20%, "
                "rgba(76, 195, 255, 0.22) 0%, rgba(10, 16, 32, 0.96) 55%, #05070f 100%)"
            ),
            "panel_bg": "rgba(9, 17, 31, 0.92)",
            "panel_strong": "rgba(14, 24, 40, 0.98)",
            "text": "#e9f2ff",
            "muted": "#8fa6c7",
            "border": "rgba(100, 130, 180, 0.28)",
            "accent": "#4cc3ff",
            "accent_soft": "rgba(76, 195, 255, 0.14)",
            "accent_alt": "#f7b36a",
            "accent_glow": "rgba(76, 195, 255, 0.35)",
            "accent_grad": "linear-gradient(135deg, #1e6bff 0%, #4cc3ff 55%, #f7b36a 120%)",
            "user_bg": "linear-gradient(135deg, #2f7eea 0%, #4cc3ff 100%)",
            "user_text": "#f7fbff",
            "assistant_bg": "rgba(10, 20, 35, 0.85)",
            "assistant_text": "#e9f2ff",
            "input_bg": "rgba(8, 16, 28, 0.95)",
        }
    else:
        colors = {
            "app_bg": (
                "radial-gradient(1200px circle at 15% -30%, "
                "rgba(76, 195, 255, 0.18) 0%, rgba(255, 255, 255, 0.95) 55%, #ffffff 100%)"
            ),
            "panel_bg": "#ffffff",
            "panel_strong": "#f3f7ff",
            "text": "#0b1a2b",
            "muted": "#4d6b8a",
            "border": "#c9d7ea",
            "accent": "#1f7ae0",
            "accent_soft": "rgba(31, 122, 224, 0.12)",
            "accent_alt": "#c9872d",
            "accent_glow": "rgba(31, 122, 224, 0.2)",
            "accent_grad": "linear-gradient(135deg, #1f7ae0 0%, #4cc3ff 60%, #f2b55f 120%)",
            "user_bg": "linear-gradient(135deg, #1f7ae0 0%, #4cc3ff 100%)",
            "user_text": "#ffffff",
            "assistant_bg": "#ffffff",
            "assistant_text": "#0b1a2b",
            "input_bg": "#ffffff",
        }

    css = build_theme_css(colors)
    st.markdown(css, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    """Render the dark mode toggle in the main area (not sidebar)."""
    init_theme_state()
    spacer, toggle_col = st.columns([6, 1], gap="small")
    with toggle_col:
        st.toggle("Modo escuro", key=_DARK_MODE_KEY)
