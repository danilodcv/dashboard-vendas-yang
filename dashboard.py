import streamlit as st
import pandas as pd
import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Vendas - YANG Molduras",
    page_icon="📈",
    layout="wide"
)

# --- Carregamento e Cache de Dados ---
@st.cache_data
def carregar_dados():
    """
    Carrega e prepara os dados da planilha.
    Esta função é executada apenas uma vez e o resultado fica em cache.
    """
    try:
        df = pd.read_excel("vendas.xlsx")
        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        # Garante que a coluna de valor seja numérica, tratando erros e preenchendo Nulos com 0
        df['vlr_total_produto'] = pd.to_numeric(df['vlr_total_produto'], errors='coerce').fillna(0)
        df.dropna(subset=['emissao'], inplace=True)
        df['codigo'] = df['codigo'].astype(str)
        return df
    except FileNotFoundError:
        st.error("Arquivo 'vendas.xlsx' não encontrado. Verifique se ele está na pasta do projeto.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return None

df_original = carregar_dados()

# --- Interface Principal ---
if df_original is not None:
    # --- Barra Lateral com Logo e Filtros Unificados ---
    st.sidebar.title("YANG Molduras")
    try:
        st.sidebar.image("sua_logo.png", use_container_width=True)
    except Exception:
        st.sidebar.warning("Logo não encontrada.")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Filtros de Vendas")

    # --- Filtro de Período ---
    todo_periodo = st.sidebar.checkbox("Analisar todo o período", value=True)
    
    min_date = df_original['emissao'].min().date()
    max_date = df_original['emissao'].max().date()

    if todo_periodo:
        data_inicial = min_date
        data_final = max_date
    else:
        data_inicial = st.sidebar.date_input("Data Inicial", min_date, min_value=min_date, max_value=max_date)
        data_final = st.sidebar.date_input("Data Final", max_date, min_value=min_date, max_value=max_date)

    # --- Filtro de Código do Produto ---
    lista_codigos = sorted(df_original['codigo'].unique())
    lista_codigos.insert(0, "Todos os Códigos")
    codigo_selecionado = st.sidebar.selectbox("Código do Produto:", options=lista_codigos)

    # --- Aplicação dos Filtros ---
    df_filtrado = df_original.copy()

    # Aplica filtro de data se não for "todo o período"
    if not todo_periodo:
        if data_inicial > data_final:
            st.sidebar.error("A data inicial não pode ser maior que a data final.")
            st.stop() # Interrompe a execução se as datas forem inválidas
        else:
            data_inicial_ts = pd.to_datetime(data_inicial)
            data_final_ts = pd.to_datetime(data_final)
            df_filtrado = df_filtrado[(df_filtrado['emissao'] >= data_inicial_ts) & (df_filtrado['emissao'] <= data_final_ts)]

    # Aplica filtro de código se não for "Todos os Códigos"
    if codigo_selecionado != "Todos os Códigos":
        df_filtrado = df_filtrado[df_filtrado['codigo'] == codigo_selecionado]

    # --- Conteúdo Principal ---
    st.title("📈 Dashboard Analítico de Vendas")
    st.markdown("---")

    # --- Exibição dos Resultados ---
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # --- Quadro de Resumo (Métricas) ---
        st.subheader("Resumo do Período Filtrado")
        total_vendas = df_filtrado['vlr_total_produto'].sum()
        num_pedidos = df_filtrado['pedido'].nunique() # Conta pedidos únicos

        col1, col2 = st.columns(2)
        # CORREÇÃO: Lógica de formatação mais robusta para moeda brasileira.
        valor_formatado = f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col1.metric("Valor Total das Vendas", valor_formatado)
        col2.metric("Quantidade de Pedidos", f"{num_pedidos}")
        
        st.markdown("---")
        
        # --- Tabela de Detalhes ---
        st.subheader("Detalhes das Vendas")
        
        colunas_mostrar = ['pedido', 'emissao', 'cliente', 'codigo', 'produto', 'vlr_total_produto']
        colunas_existentes = [col for col in colunas_mostrar if col in df_filtrado.columns]

        df_display = df_filtrado[colunas_existentes].rename(columns={
            'pedido': 'Nº Pedido',
            'emissao': 'Data da Venda',
            'cliente': 'Cliente',
            'codigo': 'Código',
            'produto': 'Produto',
            'vlr_total_produto': 'Valor Total (R$)'
        })
        
        df_display['Data da Venda'] = df_display['Data da Venda'].dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_display.sort_values(by="Data da Venda", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("\n\n---\n\n")

    # --- Consulta por Cliente (mantida como funcionalidade separada) ---
    st.subheader("Consulta Rápida por Cliente")
    NOME_DA_COLUNA_CLIENTES = 'cliente'

    if NOME_DA_COLUNA_CLIENTES in df_original.columns:
        cliente_pesquisado = st.text_input("Digite o nome do cliente para uma busca rápida:")

        if cliente_pesquisado:
            compras_cliente = df_original[df_original[NOME_DA_COLUNA_CLIENTES].str.contains(cliente_pesquisado, case=False, na=False)]

            if not compras_cliente.empty:
                st.success(f"🔍 Exibindo compras para clientes contendo '{cliente_pesquisado}':")
                # ... (código da consulta por cliente, se desejar manter)
                st.dataframe(compras_cliente, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum cliente encontrado com este nome.")
    else:
        st.error(f"A coluna '{NOME_DA_COLUNA_CLIENTES}' não foi encontrada na planilha.")

