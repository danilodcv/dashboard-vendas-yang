import streamlit as st
import pandas as pd
import datetime
import math
import re
from babel.numbers import format_currency

# --- Configuração da Página ---
st.set_page_config(
    page_title="YANG Molduras - Vendas 2023 a 2025",
    page_icon="🔎",
    layout="wide"
)

# --- Funções Auxiliares ---
def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileira (R$ 1.234,56) usando Babel."""
    if valor is None or math.isnan(valor):
        return format_currency(0, 'BRL', locale='pt_BR')
    return format_currency(valor, 'BRL', locale='pt_BR')

def parse_ptbr(x):
    """
    Converte um valor (possivelmente string no formato pt-BR com símbolos) para float.
    Retorna None em caso de falha para não mascarar erros.
    """
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    
    s = str(x).strip()
    if not s:
        return None
    
    # Remove tudo que não for dígito, vírgula ou sinal de menos
    s = re.sub(r'[^\d,-]', '', s)
    # Normaliza separadores: remove milhares '.' e troca ',' por '.'
    s = s.replace(".", "").replace(",", ".")
    
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

# --- Carregamento e Cache de Dados ---
@st.cache_data
def carregar_dados():
    """
    Carrega os dados da planilha usando 'converters' para tratar corretamente os formatos
    numéricos brasileiros diretamente na leitura, que é a abordagem mais robusta.
    """
    try:
        df = pd.read_excel(
            "vendas.xlsx",
            converters={
                'quantidade': parse_ptbr,
                'vlr_unitario': parse_ptbr,
                'vlr_final': parse_ptbr,
            }
        )

        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        df.dropna(subset=['emissao'], inplace=True)

        for col in ['quantidade', 'vlr_unitario', 'vlr_final']:
             if col in df.columns:
                 df[col].fillna(0, inplace=True)

        df['vlr_total_produto'] = df.get('quantidade', 0) * df.get('vlr_unitario', 0)
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
    # --- Barra Lateral (agora apenas para logo e título) ---
    st.sidebar.title("YANG Molduras")
    try:
        st.sidebar.image("sua_logo.png", use_container_width=True)
    except Exception:
        st.sidebar.warning("Logo não encontrada.")
    
    # --- Conteúdo Principal ---
    st.title("📈 Dashboard Analítico de Vendas")
    st.markdown("---")

    # --- Filtros no Corpo Principal ---
    st.subheader("Filtros de Vendas")
    
    min_date = df_original['emissao'].min().date()
    max_date = df_original['emissao'].max().date()
    lista_codigos = sorted(df_original['codigo'].unique())
    lista_codigos.insert(0, "Todos os Códigos")

    filt_col1, filt_col2 = st.columns([2, 1])

    with filt_col1:
        todo_periodo = st.checkbox("Analisar todo o período", value=True)
        
        d1, d2 = st.columns(2)
        data_inicial_input = d1.date_input("Data Inicial", min_date, min_value=min_date, max_value=max_date, disabled=todo_periodo)
        data_final_input = d2.date_input("Data Final", max_date, min_value=min_date, max_value=max_date, disabled=todo_periodo)
    
    with filt_col2:
        codigo_selecionado = st.selectbox("Código do Produto:", options=lista_codigos, label_visibility="collapsed", key="codigo_select")
        st.write("Código do Produto:") # Adiciona um label manual acima do selectbox

    if todo_periodo:
        data_inicial = min_date
        data_final = max_date
    else:
        data_inicial = data_inicial_input
        data_final = data_final_input

    # --- Aplicação dos Filtros ---
    df_filtrado = df_original.copy()
    
    if not todo_periodo:
        if data_inicial > data_final:
            st.error("A data inicial não pode ser maior que a data final.")
            st.stop()
        else:
            df_filtrado = df_filtrado[df_filtrado['emissao'].dt.date.between(data_inicial, data_final, inclusive='both')]

    if codigo_selecionado != "Todos os Códigos":
        df_filtrado = df_filtrado[df_filtrado['codigo'] == codigo_selecionado]

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

