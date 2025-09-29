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

# --- Funções Auxiliares ---
def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileira (R$ 1.234,56) usando Babel."""
    return format_currency(valor, 'BRL', locale='pt_BR')

def converter_para_float(valor):
    """Converte um valor (possivelmente string no formato pt-BR) para float de forma segura."""
    if isinstance(valor, str):
        # Remove pontos de milhar, substitui vírgula decimal por ponto
        valor_limpo = valor.replace('.', '').replace(',', '.')
        try:
            return float(valor_limpo)
        except (ValueError, TypeError):
            return 0.0  # Retorna 0 se a conversão falhar
    elif isinstance(valor, (int, float)):
        return float(valor)  # Retorna o valor se já for numérico
    return 0.0  # Retorna 0 para outros tipos inesperados

# --- Carregamento e Cache de Dados ---
@st.cache_data
def carregar_dados():
    """
    Carrega os dados da planilha usando 'converters' para tratar corretamente os formatos
    numéricos brasileiros diretamente na leitura.
    """
    try:
        colunas_para_converter = {
            'quantidade': converter_para_float,
            'vlr_unitario': converter_para_float,
            'vlr_final': converter_para_float
        }
        
        df = pd.read_excel(
            "vendas.xlsx",
            converters=colunas_para_converter
        )
        
        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        df.dropna(subset=['emissao'], inplace=True)
        
        # Garante que as colunas de valor que não foram convertidas sejam numéricas
        for col in ['quantidade', 'vlr_unitario', 'vlr_final']:
             if col not in colunas_para_converter and col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Recalcula o valor total para garantir consistência
        df['vlr_total_produto'] = df['quantidade'] * df['vlr_unitario']
            
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
    
    if not todo_periodo:
        if data_inicial > data_final:
            st.sidebar.error("A data inicial não pode ser maior que a data final.")
            st.stop()
        else:
            data_inicial_ts = pd.to_datetime(data_inicial)
            data_final_ts = pd.to_datetime(data_final)
            df_filtrado = df_filtrado[df_filtrado['emissao'].dt.date.between(data_inicial, data_final, inclusive='both')]


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
            st.dataframe(
                compras_cliente,
                use_container_width=True,
                hide_index=True,
                 column_config={
                    "emissao": st.column_config.DateColumn("Data da Venda", format="DD/MM/YYYY"),
                    "vlr_total_produto": st.column_config.NumberColumn("Valor Total (R$)", format="%.2f"),
                    "vlr_unitario": st.column_config.NumberColumn("Valor Unitário (R$)", format="%.2f"),
                    "vlr_final": st.column_config.NumberColumn("Valor Final (R$)", format="%.2f")
                }
            )
        else:
            st.warning("Nenhum cliente encontrado com este nome.")

