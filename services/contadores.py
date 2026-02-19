import json
from collections import defaultdict
import datetime
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_connection

# ====== FUNÇÕES PARA OBTER DADOS DOS USUÁRIOS ======

def get_user_info(user_id):
    """
    Retorna informações do usuário pelo ID.
   
    Args:
        user_id: ID do usuário
       
    Returns:
        dict com 'id', 'nome', 'email' e 'setor', ou None se não encontrado
    """
    conn = get_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, setor FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
   
    if user:
        return {
            "id": user[0],
            "nome": user[1],
            "email": user[2],
            "setor": user[3]
        }
    return None




def get_all_users():
    """
    Retorna todos os usuários do banco de dados.
   
    Returns:
        Lista de dicts com 'id', 'nome' (email) e 'setor'
    """
    conn = get_connection()
    if not conn:
        return []
        
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, setor FROM users")
    users = cursor.fetchall()
    conn.close()
   
    return [
        {"id": u[0], "nome": u[1], "email": u[2], "setor": u[3]} for u in users
    ]


def get_users_name_sector_email():
    """
    Retorna apenas nome, setor e email dos usuarios.

    Returns:
        Lista de dicts com 'nome', 'setor' e 'email'
    """
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT nome, setor, email FROM users")
    users = cursor.fetchall()
    conn.close()

    return [{"nome": u[0], "setor": u[1], "email": u[2]} for u in users]


#--------------------------------------------------------------------------------------------------------------------------
# Rankeando os setores com mais usuários da Alea-Lumen
# Vamos mostar em uma tabela os setores com mais usuários da Alea-Lumen


def get_users_by_sector_ranking():
    """
    Retorna ranking dos setores com mais usuários.
   
    Returns:
        Lista de dicts com 'setor', 'total_usuarios' e 'ranking'
    """
    users = get_users_name_sector_email()
    if not users:
        return []

    sector_counts = {}
    for user in users:
        setor = user.get("setor")
        if setor:
            sector_counts[setor] = sector_counts.get(setor, 0) + 1

    sectors = sorted(sector_counts.items(), key=lambda item: item[1], reverse=True)

    return [
        {
            "ranking": idx + 1,
            "setor": setor,
            "total_usuarios": total
        }
        for idx, (setor, total) in enumerate(sectors)
    ]




def show_sector_users_table():
    """
    Exibe tabela formatada dos setores com mais usuários.
    """
    ranking = get_users_by_sector_ranking()
   
    print("\n" + "=" * 70)
    print("RANKING DE USUÁRIOS POR SETOR")
    print("=" * 70)
    print(f"{'RANKING':<10} {'SETOR':<30} {'TOTAL DE USUÁRIOS':<20}")
    print("-" * 70)
   
    for item in ranking:
        print(f"{item['ranking']:<10} {item['setor']:<30} {item['total_usuarios']:<20}")
   
    print("=" * 70)
    print("=" * 70 + "\n")
   
    return ranking

#--------------------------------------------------------------------------------------------------------------------------------
#Total de usuários da Alea-Lumen

def show_total_users_table():
    """
    Exibe tabela com o total de usuarios.
    """
    users = get_users_name_sector_email()
    total_users = len(users)

    print("=" * 40)
    print("TOTAL DE USUARIOS")
    print("=" * 40)
    print(f"{'TOTAL':<10} {'USUARIOS':<20}")
    print("-" * 40)
    print(f"{'':<10} {total_users:<20}")
    print("=" * 40 + "\n")
#----------------------------------------------------------------------------------------------------------------------------

# ====== SISTEMA DE AUDITORIA E ANALYTICS ======


#Aqui nesse arquivo está sendo criado o banco de dados, ao qual as informações
#para a auditoria estão sendo gravados.

#----------------------------------------------------------------------------------------------------------------------------


def log_interaction(user_id=None, context=None, response=None, attachments=None):
    """
    Registra os dados de interação para fins de observabilidade.
    """


    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id, #Usuário que está usando
        "context_summary": context[:100] if context else "", # Contexto do usuário
        "full_context": context,           # Para investigação
        "attachments": attachments or [],
        "flagged_inappropriate": False
    }
    # Banco de dados
   
    return log_entry
#-----------------------------------------------------------------------------------------------------------------

#Integrando a document_service com o sistema de analytics de contexto
#Aqui estámos contabilizando os contextos acessados sem armazenar dados dos usuários
#Estamos puxando os dados de llm_service.py para registrar as interações


'''
class ContextAnalytics:
    """
    Sistema de análise de contextos sem divulgar dados dos usuários.
    Contabiliza quantas vezes cada contexto foi acessado.
    """
   
    def __init__(self, storage_file="context_analytics.json"):
        """
        Inicializa o sistema de analytics.
       
        Args:
            storage_file: Arquivo onde os dados de contabilização serão armazenados
        """
        self.storage_file = storage_file
        self.context_access_count = defaultdict(int)
        self.load_from_file()
   
    def load_from_file(self):
        """Carrega os dados de contabilização do arquivo."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.context_access_count = defaultdict(int, data)
            except (json.JSONDecodeError, IOError):
                self.context_access_count = defaultdict(int)
        else:
            self.context_access_count = defaultdict(int)
   
    def save_to_file(self):
        """Salva os dados de contabilização no arquivo."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.context_access_count), f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Erro ao salvar dados de analytics: {e}")
   
    def record_context_access(self, context, user_id=None, response=None, attachments=None):
        """
        Registra um acesso a um contexto (sem armazenar dados do usuário).
       
        Args:
            context: O contexto que foi acessado
            user_id: ID do usuário (será registrado apenas no log_interaction, não aqui)
            response: Resposta fornecida
            attachments: Anexos associados
           
        Returns:
            dict com o registro de contabilização
        """
       
        # Registra no sistema de logging (com dados do usuário)
        log_entry = log_interaction(
            user_id=user_id,
            context=context,
            response=response,
            attachments=attachments
        )
       
        # Contabiliza acesso ao contexto (SEM dados do usuário)
        context_key = context[:50] if context else "contexto_vazio"  # Resumo do contexto
        self.context_access_count[context_key] += 1
       
        # Salva os dados
        self.save_to_file()
       
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "context_summary": context_key,
            "total_accesses": self.context_access_count[context_key],
            "log_entry": log_entry
        }
   
    def get_context_statistics(self):
        """
        Retorna estatísticas de acesso aos contextos (sem divulgar dados dos usuários).
       
        Returns:
            dict com contextos e seus respectivos números de acessos, ordenado por acessos
        """
        sorted_contexts = sorted(
            self.context_access_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
       
        return {
            "total_unique_contexts": len(self.context_access_count),
            "total_accesses": sum(self.context_access_count.values()),
            "contexts": [
                {
                    "contexto": ctx,
                    "acessos": count
                }
                for ctx, count in sorted_contexts
            ]
        }
   
    def get_top_contexts(self, limit=10):
        """
        Retorna os N contextos mais acessados.
       
        Args:
            limit: Número de contextos a retornar
           
        Returns:
            Lista com os top contextos
        """
        stats = self.get_context_statistics()
        return stats["contexts"][:limit]
   
    def reset_statistics(self):
        """Reseta todas as estatísticas (use com cuidado!)."""
        self.context_access_count = defaultdict(int)
        self.save_to_file()
        print("Estatísticas resetadas com sucesso!")



# Instância global para uso em toda a aplicação
analytics = ContextAnalytics()




def track_context(context, user_id=None, response=None, attachments=None):
    """
    Função de conveniência para registrar acesso a um contexto.
   
    Exemplo de uso:
        from doc import track_context
        track_context("contexto A", user_id="user123")
    """
    return analytics.record_context_access(context, user_id, response, attachments)



def show_context_report():
    """Exibe um relatório formatado dos contextos mais acessados."""
    stats = analytics.get_context_statistics()
   
    print("\n" + "="*60)
    print("RELATÓRIO DE ACESSOS A CONTEXTOS")
    print("="*60)
    print(f"Total de contextos únicos: {stats['total_unique_contexts']}")
    print(f"Total de acessos: {stats['total_accesses']}")
    print("-"*60)
   
    for item in stats['contexts']:
        print(f"Contexto: {item['contexto'][:40]:<40} | Acessos: {item['acessos']:>5}")
   
    print("="*60 + "\n")
    
    return stats
'''


if __name__ == "__main__":
    show_sector_users_table()
    show_total_users_table()