"""Theme helpers shared across pages."""

from __future__ import annotations

import streamlit as st

from ui.chat_markup import build_theme_css


_DARK_MODE_KEY = "dark_mode"


def init_theme_state() -> None:
    """Force dark mode in session state."""
    st.session_state[_DARK_MODE_KEY] = True


def apply_theme() -> None:
    """Render only the dark theme CSS with improved consistency."""
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

    # Foundation styles for better consistency
    foundation_css = """
    <style>
      /* Typography improvements */
      body, p, span, label {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }
      
      /* Improve focus states for accessibility */
      button:focus-visible,
      input:focus-visible,
      textarea:focus-visible,
      select:focus-visible {
        outline: 2px solid rgba(76, 195, 255, 0.5);
        outline-offset: 2px;
      }
      
      /* Reduce motion for users who prefer it */
      @media (prefers-reduced-motion: reduce) {
        * {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      }
    </style>
    """

    theme_css = build_theme_css(colors)
    st.markdown(foundation_css + theme_css, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    """Kept for compatibility; white mode has been removed."""
    init_theme_state()
