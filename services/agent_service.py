from __future__ import annotations

import json
import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

AGENTS_FILE = Path("agents_config.json")
DEFAULT_AGENTS: dict[str, dict[str, Any]] = {
    "default": {
        "name": "Generalista",
        "role": "Assistente Corporativo",
        "system_prompt": "Voce e um assistente util e prestativo da empresa.",
        "collection_name": "corporate_docs",
    }
}


def _agents_cache_key() -> tuple[str, float]:
    if not AGENTS_FILE.exists():
        return str(AGENTS_FILE), -1.0
    return str(AGENTS_FILE), AGENTS_FILE.stat().st_mtime


@lru_cache(maxsize=8)
def _load_agents_cached(cache_key: tuple[str, float]) -> dict[str, dict[str, Any]]:
    _ = cache_key
    try:
        with AGENTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
    except Exception:
        return {}
    return {}


def _ensure_default_agents_file() -> None:
    if AGENTS_FILE.exists():
        return
    save_agents(DEFAULT_AGENTS)


def load_agents() -> dict[str, dict[str, Any]]:
    """Carrega a lista de agentes com cache leve por mtime de arquivo."""
    _ensure_default_agents_file()
    key = _agents_cache_key()
    data = _load_agents_cached(key)
    if data:
        return data
    return copy.deepcopy(DEFAULT_AGENTS)


def save_agents(agents_data: dict[str, dict[str, Any]]) -> None:
    """Salva os agentes no JSON e invalida cache local."""
    AGENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AGENTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(agents_data, file, indent=4, ensure_ascii=False)
    _load_agents_cached.cache_clear()


def create_agent(agent_id: str, name: str, role: str, system_prompt: str) -> bool:
    """Cria um novo agente e salva no arquivo."""
    agents = load_agents()
    collection_name = f"collection_{agent_id}"
    agents[agent_id] = {
        "name": name,
        "role": role,
        "system_prompt": system_prompt,
        "collection_name": collection_name,
    }
    save_agents(agents)
    return True


def delete_agent(agent_id: str) -> bool:
    """Remove um agente da lista."""
    agents = load_agents()
    if agent_id not in agents:
        return False
    del agents[agent_id]
    save_agents(agents)
    return True
