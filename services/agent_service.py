import json
import os

AGENTS_FILE = "agents_config.json"

def load_agents():
    """Carrega a lista de agentes do arquivo JSON."""
    if not os.path.exists(AGENTS_FILE):
        # Cria um agente padrão se não existir nenhum
        default_agents = {
            "default": {
                "name": "Generalista",
                "role": "Assistente Corporativo",
                "system_prompt": "Você é um assistente útil e prestativo da empresa.",
                "collection_name": "corporate_docs" # Coleção padrão antiga
            }
        }
        save_agents(default_agents)
        return default_agents
    
    try:
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler arquivo de agentes: {e}")
        return {}

def save_agents(agents_data):
    """Salva os agentes no JSON."""
    with open(AGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(agents_data, f, indent=4, ensure_ascii=False)

def create_agent(agent_id, name, role, system_prompt):
    """
    Cria um novo agente e salva no arquivo.
    """
    agents = load_agents()
    
    # O nome da coleção no banco será baseado no ID do agente para garantir unicidade
    # Ex: se o ID for 'rh', a coleção será 'collection_rh'
    collection_name = f"collection_{agent_id}"
    
    agents[agent_id] = {
        "name": name,
        "role": role,
        "system_prompt": system_prompt,
        "collection_name": collection_name
    }
    
    save_agents(agents)
    print(f"✅ Agente '{name}' criado com sucesso!")
    return True

def delete_agent(agent_id):
    """Remove um agente da lista."""
    agents = load_agents()
    if agent_id in agents:
        del agents[agent_id]
        save_agents(agents)
        return True
    return False