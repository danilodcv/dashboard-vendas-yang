import streamlit as st
import pandas as pd
import datetime
from babel.numbers import format_currency

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
    Carrega os dados da planilha, aplicando as melhores práticas de conversão de tipos
    para garantir a integridade dos dados desde o início.
    """
    try:
        # Lê o Excel já tratando os formatos numéricos brasileiros
        df = pd.read_excel(
            "vendas.xlsx",
            decimal=',',
            thousands='.'
        )
        
        # Converte a coluna de data, tratando o formato brasileiro
        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        df.dropna(subset=['emissao'], inplace=True)
        
        # Garante que as colunas de valor sejam numéricas, preenchendo erros/nulos com 0
        colunas_valor = ['quantidade', 'vlr_unitario', 'vlr_final']
        for coluna in colunas_valor:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce').fillna(0)

        # Recalcula o valor total para garantir consistência
        if 'quantidade' in df.columns and 'vlr_unitario' in df.columns:
            df['vlr_total_produto'] = df['quantidade'] * df['vlr_unitario']
        else:
            # Fallback caso uma das colunas não exista, evita que o app quebre
            df['vlr_total_produto'] = 0
            
        df['codigo'] = df['codigo'].astype(str)
        return df
    except FileNotFoundError:
        st.error("Arquivo 'vendas.xlsx' não encontrado. Verifique se ele está na pasta do projeto.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar a planilha: {e}")
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
    
    # Aplica filtro de data de forma mais robusta
    if not todo_periodo:
        if data_inicial > data_final:
            st.sidebar.error("A data inicial não pode ser maior que a data final.")
            st.stop()
        else:
            data_inicial_ts = pd.to_datetime(data_inicial)
            # Adiciona um dia à data final para incluir todas as horas do último dia
            data_final_ts = pd.to_datetime(data_final) + datetime.timedelta(days=1)
            df_filtrado = df_filtrado[df_filtrado['emissao'].between(data_inicial_ts, data_final_ts, inclusive='left')]

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
        
        # Usando Babel para formatação de moeda confiável
        col1.metric("Valor Total das Vendas", format_currency(total_vendas, 'BRL', locale='pt_BR'))
        col2.metric("Quantidade de Pedidos", f"{num_pedidos}")
        
        st.markdown("---")
        
        st.subheader("Detalhes das Vendas")
        
        colunas_mostrar = ['pedido', 'emissao', 'cliente', 'codigo', 'produto', 'vlr_total_produto']
        df_display = df_filtrado[colunas_mostrar].rename(columns={
            'pedido': 'Nº Pedido',
            'emissao': 'Data da Venda',
            'cliente': 'Cliente',
            'codigo': 'Código',
            'produto': 'Produto',
            'vlr_total_produto': 'Valor Total'
        }).sort_values(by="Data da Venda", ascending=False)

        # Formatação profissional via st.column_config
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Data da Venda": st.column_config.DateColumn(
                    "Data da Venda",
                    format="DD/MM/YYYY"
                ),
                "Valor Total": st.column_config.NumberColumn(
                    "Valor Total (R$)",
                    format="%.2f"
                )
            }
        )

    st.markdown("\n\n---\n\n")

    st.subheader("Consulta Rápida por Cliente")
    cliente_pesquisado = st.text_input("Digite o nome do cliente para uma busca rápida:")

    if cliente_pesquisado:
        # Busca por cliente mais segura com regex=False
        compras_cliente = df_original[df_original['cliente'].str.contains(cliente_pesquisado, case=False, na=False, regex=False)]

        if not compras_cliente.empty:
            st.success(f"🔍 Exibindo compras para clientes contendo '{cliente_pesquisado}':")
            compras_cliente_display = compras_cliente.copy()
            st.dataframe(
                compras_cliente_display,
                use_container_width=True,
                hide_index=True,
                 column_config={
                    "emissao": st.column_config.DateColumn("Data da Venda", format="DD/MM/YYYY"),
                    "vlr_total_produto": st.column_config.NumberColumn("Valor Total (R$)", format="%.2f")
                }
            )
        else:
            st.warning("Nenhum cliente encontrado com este nome.")

