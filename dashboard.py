import streamlit as st
import pandas as pd
import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Vendas - YANG Molduras",
    page_icon="📈",
    layout="wide"
)

# --- Funções Auxiliares ---
def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileira (R$ 1.234,56)."""
    try:
        valor_float = float(valor)
        # Formata o número com separador de milhar e duas casas decimais
        valor_formatado_us = f"{valor_float:,.2f}"
        # Inverte os separadores para o padrão brasileiro
        valor_formatado_br = valor_formatado_us.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_formatado_br}"
    except (ValueError, TypeError):
        return "R$ 0,00"

# --- Carregamento e Cache de Dados ---
@st.cache_data
def carregar_dados():
    """
    Carrega, limpa os dados da planilha e garante a precisão dos cálculos.
    """
    try:
        df = pd.read_excel("vendas.xlsx")
        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        df.dropna(subset=['emissao'], inplace=True)
        
        # --- Limpeza Robusta das Colunas de Valor ---
        colunas_valor = ['quantidade', 'vlr_unitario', 'vlr_final']
        for coluna in colunas_valor:
            if coluna in df.columns:
                # Só executa a limpeza se a coluna não for numérica (for texto/objeto)
                if not pd.api.types.is_numeric_dtype(df[coluna]):
                    # Converte para string para garantir que os métodos de string funcionem
                    df[coluna] = df[coluna].astype(str)
                    # Remove o separador de milhar (ponto) e troca a vírgula decimal por ponto
                    df[coluna] = df[coluna].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                
                # Converte para numérico, tratando erros e preenchendo Nulos com 0
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce').fillna(0)

        # Recalcula a coluna 'vlr_total_produto' para garantir a precisão.
        df['vlr_total_produto'] = df['quantidade'] * df['vlr_unitario']
        
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

    if not todo_periodo:
        if data_inicial > data_final:
            st.sidebar.error("A data inicial não pode ser maior que a data final.")
            st.stop()
        else:
            data_inicial_ts = pd.to_datetime(data_inicial)
            data_final_ts = pd.to_datetime(data_final)
            df_filtrado = df_filtrado[(df_filtrado['emissao'] >= data_inicial_ts) & (df_filtrado['emissao'] <= data_final_ts)]

    if codigo_selecionado != "Todos os Códigos":
        df_filtrado = df_filtrado[df_filtrado['codigo'] == codigo_selecionado]

    # --- Conteúdo Principal ---
    st.title("📈 Dashboard Analítico de Vendas")
    st.markdown("---")

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.subheader("Resumo do Período Filtrado")
        total_vendas = df_filtrado['vlr_total_produto'].sum()
        num_pedidos = df_filtrado['pedido'].nunique()

        col1, col2 = st.columns(2)
        
        col1.metric("Valor Total das Vendas", formatar_moeda(total_vendas))
        col2.metric("Quantidade de Pedidos", f"{num_pedidos}")
        
        st.markdown("---")
        
        st.subheader("Detalhes das Vendas")
        
        colunas_mostrar = ['pedido', 'emissao', 'cliente', 'codigo', 'produto', 'vlr_total_produto']
        colunas_existentes = [col for col in colunas_mostrar if col in df_filtrado.columns]

        df_ordenado = df_filtrado.sort_values(by="emissao", ascending=False)
        
        df_display = df_ordenado[colunas_existentes].rename(columns={
            'pedido': 'Nº Pedido',
            'emissao': 'Data da Venda',
            'cliente': 'Cliente',
            'codigo': 'Código',
            'produto': 'Produto',
            'vlr_total_produto': 'Valor Total'
        })
        
        df_display['Data da Venda'] = df_display['Data da Venda'].dt.strftime('%d/%m/%Y')
        
        df_display['Valor Total'] = df_display['Valor Total'].apply(formatar_moeda)

        st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("\n\n---\n\n")

    st.subheader("Consulta Rápida por Cliente")
    NOME_DA_COLUNA_CLIENTES = 'cliente'

    if NOME_DA_COLUNA_CLIENTES in df_original.columns:
        cliente_pesquisado = st.text_input("Digite o nome do cliente para uma busca rápida:")

        if cliente_pesquisado:
            compras_cliente = df_original[df_original[NOME_DA_COLUNA_CLIENTES].str.contains(cliente_pesquisado, case=False, na=False)]

            if not compras_cliente.empty:
                st.success(f"🔍 Exibindo compras para clientes contendo '{cliente_pesquisado}':")
                # Vamos formatar a coluna de valor aqui também para consistência
                compras_cliente_display = compras_cliente.copy()
                compras_cliente_display['vlr_total_produto'] = compras_cliente_display['vlr_total_produto'].apply(formatar_moeda)
                st.dataframe(compras_cliente_display, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum cliente encontrado com este nome.")
    else:
        st.error(f"A coluna '{NOME_DA_COLUNA_CLIENTES}' não foi encontrada na planilha.")

