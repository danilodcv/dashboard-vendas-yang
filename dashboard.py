import streamlit as st
import pandas as pd
import datetime
import math
import re
from babel.numbers import format_currency
import locale

# --- Configuração de Localização para Português-Brasil ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    pass

# --- Configuração da Página ---
st.set_page_config(
    page_title="YANG Molduras - Vendas",
    page_icon="icone_yang.png",
    layout="wide"
)

# --- Funções Auxiliares ---
def formatar_moeda(valor):
    """Formata um número para o padrão de moeda brasileira (R$ 1.234,56) usando Babel."""
    if not isinstance(valor, (int, float)) or pd.isna(valor):
        return format_currency(0, "BRL", locale="pt_BR")
    return format_currency(valor, "BRL", locale="pt_BR")

def parse_ptbr(x):
    """
    Converte uma string pt-BR, americana ou um número para float de forma robusta.
    Retorna None em caso de falha para não mascarar erros.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    
    s = str(x).strip()
    if not s:
        return None
    
    # Remove símbolos de moeda, unidades e espaços, mantendo dígitos, vírgula, ponto e sinal
    s = re.sub(r'[^\d,\.-]', '', s)
    
    if not s:
        return None

    # Detecta o formato baseado na posição dos separadores
    if ',' in s and '.' in s:
        pos_comma = s.rfind(',')
        pos_dot = s.rfind('.')
        if pos_comma > pos_dot:
            # Formato brasileiro: 1.234,56 -> 1234.56
            s = s.replace('.', '').replace(',', '.')
        else:
            # Formato americano: 1,234.56 -> 1234.56
            s = s.replace(',', '')
    elif ',' in s:
        # Apenas vírgula: provavelmente decimal brasileiro
        s = s.replace(',', '.')

    try:
        return float(s)
    except (ValueError, TypeError):
        return None

# --- Carregamento e Cache de Dados ---
@st.cache_data
def carregar_dados():
    """
    Carrega e processa os dados da planilha usando 'converters' para robustez.
    """
    try:
        df = pd.read_excel(
            "vendas.xlsx",
            converters={
                'quantidade': parse_ptbr,
                'vlr_unitario': parse_ptbr,
                'vlr_final': parse_ptbr,
                'vlr_total_produto': parse_ptbr, # Garante a leitura correta da coluna de total
            }
        )

        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        df.dropna(subset=['emissao'], inplace=True)

        # Preenche apenas valores None/NaN com 0 após a conversão
        for col in ['quantidade', 'vlr_unitario', 'vlr_final', 'vlr_total_produto']:
             if col in df.columns:
                 df[col].fillna(0.0, inplace=True)
        
        df['codigo'] = df.get('codigo', '').astype(str)
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
    # --- Cabeçalho Principal com Logo e Título ---
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        try:
            st.image("sua_logo.png", width=240)
        except Exception:
            pass

    with col_titulo:
        st.title("YANG Molduras")
        st.subheader("Dashboard de Vendas - 2023 a 2025")
    
    st.markdown("---")

    # --- Filtros no Corpo Principal ---
    st.subheader("Filtros de Vendas")
    
    min_date = df_original['emissao'].min().date()
    max_date = df_original['emissao'].max().date()
    
    lista_codigos = sorted(df_original['codigo'].unique())
    if "Todos os Códigos" not in lista_codigos:
        lista_codigos.insert(0, "Todos os Códigos")

    filt_col1, filt_col2 = st.columns([2, 1])

    with filt_col1:
        date_col1, date_col2 = st.columns(2)
        todo_periodo = st.checkbox("Analisar todo o período", value=True)
        
        if todo_periodo:
            data_inicial = min_date
            data_final = max_date
            date_col1.date_input("Data Inicial", min_date, disabled=True)
            date_col2.date_input("Data Final", max_date, disabled=True)
        else:
            data_inicial = date_col1.date_input("Data Inicial", min_date, min_value=min_date, max_value=max_date)
            data_final = date_col2.date_input("Data Final", max_date, min_value=min_date, max_value=max_date)

    with filt_col2:
        codigo_selecionado = st.selectbox("Código do Produto:", options=lista_codigos)
    
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
                "Data da Venda": st.column_config.DateColumn("Data da Venda", format="DD/MM/YYYY"),
                "Valor Total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f")
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
                    "vlr_total_produto": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"),
                    "vlr_unitario": st.column_config.NumberColumn("Valor Unitário (R$)", format="R$ %.2f"),
                    "vlr_final": st.column_config.NumberColumn("Valor Final (R$)", format="R$ %.2f")
                }
            )
        else:
            st.warning("Nenhum cliente encontrado com este nome.")

