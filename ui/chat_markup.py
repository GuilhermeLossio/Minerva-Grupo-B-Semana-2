from __future__ import annotations

import html

from ui.brand import get_logo_data_uri
from typing import Any, Dict, List


def build_theme_css(colors: Dict[str, str]) -> str:
    return f"""
    <style>
      :root {{
        --app-bg: {colors["app_bg"]};
        --panel-bg: {colors["panel_bg"]};
        --panel-strong: {colors["panel_strong"]};
        --text: {colors["text"]};
        --muted: {colors["muted"]};
        --border: {colors["border"]};
        --accent: {colors["accent"]};
        --accent-soft: {colors["accent_soft"]};
        --accent-alt: {colors["accent_alt"]};
        --accent-glow: {colors["accent_glow"]};
        --accent-grad: {colors["accent_grad"]};
        --user-bg: {colors["user_bg"]};
        --user-text: {colors["user_text"]};
        --assistant-bg: {colors["assistant_bg"]};
        --assistant-text: {colors["assistant_text"]};
        --input-bg: {colors["input_bg"]};
      }}

      @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

      html, body, [class*="css"] {{
        font-family: "Sora", "Segoe UI", system-ui, sans-serif;
      }}

      h1, h2, h3, .al-header h1 {{
        font-family: "Space Grotesk", "Sora", "Segoe UI", sans-serif;
        letter-spacing: -0.01em;
      }}

      .stApp {{
        background:
          radial-gradient(1px 1px at 15% 25%, rgba(255, 255, 255, 0.15) 0, transparent 60%),
          radial-gradient(1.5px 1.5px at 75% 15%, rgba(255, 255, 255, 0.12) 0, transparent 60%),
          radial-gradient(1px 1px at 65% 75%, rgba(255, 255, 255, 0.1) 0, transparent 60%),
          radial-gradient(380px circle at 85% -10%, rgba(247, 179, 106, 0.18) 0, transparent 55%),
          var(--app-bg);
        background-attachment: fixed;
        color: var(--text);
      }}

      section[data-testid="stSidebar"] > div {{
        background: linear-gradient(
          180deg,
          color-mix(in srgb, var(--panel-bg), #ffffff 6%) 0%,
          var(--panel-bg) 45%,
          color-mix(in srgb, var(--panel-bg), #000000 6%) 100%
        );
        color: var(--text);
        border-right: 1px solid var(--border);
        padding-top: 1.25rem;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
      }}

      section[data-testid="stSidebar"] h2,
      section[data-testid="stSidebar"] h3 {{
        color: var(--text);
      }}

      section[data-testid="stSidebar"] .stTextArea textarea,
      section[data-testid="stSidebar"] input,
      section[data-testid="stSidebar"] select,
      section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: var(--input-bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 10px;
      }}

      section[data-testid="stSidebar"] .stButton > button,
      section[data-testid="stSidebar"] .stDownloadButton > button {{
        border-radius: 10px;
        border: 1px solid var(--border);
        background: var(--panel-strong);
        color: var(--text);
      }}

      .stButton > button,
      .stDownloadButton > button {{
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--panel-strong);
        color: var(--text);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
      }}

      .stButton > button[kind="primary"] {{
        background: var(--accent-grad);
        border: none;
        color: #ffffff;
        font-weight: 600;
        box-shadow: 0 12px 30px var(--accent-glow);
      }}

      .stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 16px 34px var(--accent-glow);
      }}

      .stButton > button:active {{
        transform: translateY(0);
      }}

      div[data-testid="stFileUploader"] {{
        border: 1px dashed var(--border);
        border-radius: 10px;
        padding: 8px;
      }}

      div[data-testid="stChatInput"] {{
        background: var(--panel-bg);
        border-top: 1px solid var(--border);
        padding: 0.75rem 1rem;
      }}

      div[data-testid="stChatInput"] textarea {{
        background-color: var(--input-bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 0.85rem 1rem;
      }}

      textarea,
      input,
      [data-baseweb="textarea"] textarea,
      [data-baseweb="input"] input {{
        background-color: var(--input-bg);
        color: var(--text);
        caret-color: var(--text);
        -webkit-text-fill-color: var(--text);
        border: 1px solid var(--border);
        border-radius: 12px;
      }}

      textarea::placeholder,
      input::placeholder,
      [data-baseweb="textarea"] textarea::placeholder,
      [data-baseweb="input"] input::placeholder {{
        color: var(--muted);
        opacity: 1;
      }}

      @keyframes al-fade {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}

      @keyframes al-float {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}

      .block-container {{
        padding-top: 1.5rem;
        animation: al-fade 0.55s ease-out;
      }}

      .al-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 1rem 1.5rem;
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        position: sticky;
        top: 0.75rem;
        z-index: 5;
        backdrop-filter: blur(8px);
      }}

      .al-brand {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
      }}

      .al-logo {{
        width: 46px;
        height: 46px;
        border-radius: 16px;
        object-fit: cover;
        box-shadow: 0 0 18px rgba(76, 195, 255, 0.28);
        border: 1px solid color-mix(in srgb, var(--accent), transparent 60%);
        background: radial-gradient(circle at 30% 20%, rgba(76, 195, 255, 0.35), transparent 60%);
      }}

      .al-logo-fallback {{
        width: 46px;
        height: 46px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--text);
        background: var(--accent-grad);
        box-shadow: 0 0 18px rgba(76, 195, 255, 0.28);
      }}

      .al-header h1 {{
        font-size: 1.25rem;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.01em;
      }}

      .al-header h1 span {{
        color: var(--accent);
        font-weight: 500;
      }}

      .al-header p {{
        margin: 0.1rem 0 0 0;
        font-size: 0.75rem;
        color: var(--muted);
      }}

      .al-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        border: 1px solid color-mix(in srgb, var(--accent-alt), transparent 55%);
        background: color-mix(in srgb, var(--accent-alt), transparent 85%);
        color: var(--accent-alt);
        font-size: 0.7rem;
        font-weight: 600;
      }}

      .al-chat-body {{
        max-width: 1100px;
        margin: 0.5rem auto 0;
        padding: 1.5rem 1rem 0;
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }}

      .al-chat-row {{
        display: flex;
        width: 100%;
        animation: al-float 0.35s ease;
      }}

      .al-chat-row.user {{
        justify-content: flex-end;
      }}

      .al-chat-bubble {{
        display: flex;
        gap: 0.75rem;
        max-width: 85%;
        align-items: flex-start;
      }}

      .al-chat-bubble.user {{
        flex-direction: row-reverse;
        text-align: right;
      }}

      .al-avatar {{
        width: 32px;
        height: 32px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        flex-shrink: 0;
      }}

      .al-avatar.user {{
        background: var(--user-bg);
        color: var(--user-text);
      }}

      .al-avatar.assistant {{
        background: color-mix(in srgb, var(--panel-bg), var(--border) 35%);
        color: var(--muted);
      }}

      .al-chat-content {{
        padding: 0.9rem 1rem;
        border-radius: 16px;
        font-size: 0.9rem;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
      }}

      .al-chat-bubble.user .al-chat-content {{
        background: var(--user-bg);
        color: var(--user-text);
        border-top-right-radius: 4px;
      }}

      .al-chat-bubble.assistant .al-chat-content {{
        background: var(--assistant-bg);
        color: var(--assistant-text);
        border: 1px solid var(--border);
        border-top-left-radius: 4px;
      }}

      .al-empty {{
        text-align: center;
        padding: 3rem 1rem;
        color: var(--muted);
      }}

      .al-empty-title {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.35rem;
      }}

      .al-banner {{
        margin: 0.75rem auto 0;
        max-width: 1100px;
        padding: 0.6rem 1rem;
        border-top: 1px solid color-mix(in srgb, var(--accent-alt), transparent 65%);
        background: color-mix(in srgb, var(--accent-alt), transparent 88%);
        color: var(--accent-alt);
        font-size: 0.7rem;
        display: flex;
        gap: 0.5rem;
        align-items: center;
      }}

      .al-footer {{
        margin: 0.5rem auto 1.25rem;
        max-width: 1100px;
        text-align: center;
        font-size: 0.65rem;
        color: var(--muted);
      }}

      .al-card {{
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.75rem;
        background: var(--panel-bg);
      }}

      .al-card.success {{
        border-color: rgba(34, 197, 94, 0.35);
        background: rgba(34, 197, 94, 0.08);
        color: #22c55e;
      }}

      .al-card-title {{
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
      }}

      .al-card-row {{
        font-size: 0.75rem;
        color: var(--text);
      }}

      a {{
        color: var(--accent);
      }}
    </style>
    """


def header_html(meta: Dict[str, Any]) -> str:
    logo_uri = get_logo_data_uri()
    logo_html = (
        f'<img class="al-logo" src="{logo_uri}" alt="Alea Lumen logo" />'
        if logo_uri
        else '<div class="al-logo-fallback">AL</div>'
    )
    pill_html = ""
    if meta:
        pill_html = f'<div class="al-pill">{meta.get("rows", 0)} linhas ativas</div>'

    return f"""
        <div class="al-header">
          <div class="al-brand">
            {logo_html}
            <div>
              <h1>Alea Lumen <span>Chat</span></h1>
              <p>Inteligencia corporativa com contexto seguro.</p>
            </div>
          </div>
          {pill_html}
        </div>
        """


def empty_state_html() -> str:
    return """
        <div class="al-empty">
          <div class="al-empty-title">Bem-vindo ao Alea Lumen</div>
          <div>Suba um arquivo CSV para comecar a explorar seus dados.</div>
        </div>
        """


def messages_html(messages: List[Dict[str, Any]], is_loading: bool = False) -> str:
    parts = ['<div class="al-chat-body">']
    for message in messages:
        role = message.get("role", "assistant")
        role_class = "user" if role == "user" else "assistant"
        avatar = "U" if role_class == "user" else "A"
        safe_content = html.escape(str(message.get("content", ""))).replace("\n", "<br>")
        parts.append(
            f"""
            <div class="al-chat-row {role_class}">
              <div class="al-chat-bubble {role_class}">
                <div class="al-avatar {role_class}">{avatar}</div>
                <div class="al-chat-content">{safe_content}</div>
              </div>
            </div>
            """
        )

    if is_loading:
        parts.append(
            """
            <div class="al-chat-row assistant">
              <div class="al-chat-bubble assistant">
                <div class="al-avatar assistant">A</div>
                <div class="al-chat-content">Pensando...</div>
              </div>
            </div>
            """
        )

    parts.append("</div>")
    return "\n".join(parts)


def info_banner_html() -> str:
    return """
        <div class="al-banner">
          Nenhum CSV carregado. O chat esta operando sem contexto de dados.
        </div>
        """


def footer_html() -> str:
    return """
        <div class="al-footer">
          A IA pode cometer erros em calculos e interpretacoes. Verifique os dados.
        </div>
        """


def csv_loaded_card_html(row_count: int, column_count: int) -> str:
    return f"""
            <div class="al-card success">
              <div class="al-card-title">Carregado</div>
              <div class="al-card-row">Linhas: {row_count}</div>
              <div class="al-card-row">Colunas: {column_count}</div>
            </div>
            """
