"""Helpers to limit Streamlit reruns to one per run."""

from __future__ import annotations

import streamlit as st


_RERUN_FLAG = "_rerun_pending"


def reset_rerun_guard() -> None:
    """Reset the rerun guard for the current execution."""
    st.session_state[_RERUN_FLAG] = False


def safe_rerun() -> bool:
    """Trigger a rerun once per execution. Returns True if requested."""
    if st.session_state.get(_RERUN_FLAG):
        return False
    st.session_state[_RERUN_FLAG] = True
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
    return True
