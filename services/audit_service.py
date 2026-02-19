
import pandas as pd

##Precisa importar os arquivos de dados dos tokens

#Nesse arquivo estamos auth_service.py estamos criando as contabilizações de uso - Tokens - por setores
# Estamos contabilizando os dados totais e rankeando o setor que possui maior gasto com tokens para o menor 



def gerar_tabela_ranking_custos(dados_uso):
    """
    Gera uma tabela consolidada de custos por setor, 
    ordenada do maior para o menor gasto.
    """
    
    
    # --- PARTE PARA SUBSTITUIR OS PREÇOS (MANUALMENTE) ---
    # Altere o valor abaixo conforme o custo real da sua API

    #-----------------------------------------------------------------------------------------------------------------
    # Localizar o preço atual com o Irlan dentro do código e substituir aqui 
    PRECO_POR_1K_TOKENS = 52.00  # Exemplo: R$ 52,00 por 1000 tokens
    # -----------------------------------------------------------------------------------------------------------------


    # 1. Transformar dados brutos em DataFrame
    df = pd.DataFrame(dados_uso)    

    # Verificação de segurança: garante que as colunas essenciais existem
    # Aqui contabilizamos setor, usuário e tokens gastos para cada interação

    colunas_necessarias = ['setor', 'usuario', 'tokens_gastos']
    for col in colunas_necessarias:
        if col not in df.columns:
            raise ValueError(f"A coluna '{col}' é obrigatória nos dados de entrada.")
        

    # 2. Agrupamentos por setor e soma dos tokens gastos 
    # Dados     

    tabela_setores = df.groupby('setor').agg(
        total_usuarios=('usuario', 'nunique'),    # Pessoas únicas e contabiliza quantas vezes essas pessoas unicas usaram o sistema 
        total_interacoes=('usuario', 'count'),    # Total de vezes que usaram
        tokens_acumulados=('tokens_gastos', 'sum') # Soma dos tokens
    ).reset_index()

    # 3. Criando coluna de custos total por setor
    # Cálculo: (Soma de Tokens / 1000) * Preço - Estamos contabilizando o custo por tokens a cada 1000 tokens
    tabela_setores['custo_financeiro'] = (tabela_setores['tokens_acumulados'] / 1000) * PRECO_POR_1K_TOKENS

    # 4. Ordenar do maior para o menor gasto
    tabela_ranking = tabela_setores.sort_values(by='custo_financeiro', ascending=False)

    # 5. Exibir a tabela final

    print("\n" + "="*80)
    print("RANKING DE CUSTOS POR SETOR")
    print("="*80)
    print(tabela_ranking.to_string(index=False))
    print("="*80 + "\n")

    return tabela_ranking
#oioioi
