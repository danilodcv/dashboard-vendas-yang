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
    Converte string pt-BR, americana ou número para float de forma inteligente.
    Detecta o formato antes de normalizar separadores.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    
    s = str(x).strip()
    if not s:
        return None
    
    # Remove símbolos de moeda, unidades e espaços
    s = re.sub(r'[R$\s]', '', s)
    s = re.sub(r'[A-Za-z]', '', s)
    
    if not s:
        return None
    
    # Detecta o formato baseado na posição dos separadores
    if ',' in s and '.' in s:
        # Dois separadores: determina qual é milhar e qual é decimal
        pos_comma = s.rfind(',')  # última vírgula
        pos_dot = s.rfind('.')    # último ponto
        
        if pos_comma > pos_dot:
            # Formato brasileiro: 1.234.567,89
            s = s.replace('.', '').replace(',', '.')
        else:
            # Formato americano: 1,234,567.89
            s = s.replace(',', '')
    
    elif ',' in s:
        # Só vírgula: pode ser decimal BR ou separador de milhar americano
        parts = s.split(',')
        if len(parts[-1]) <= 2 and len(parts[-1]) > 0:
            # Última parte tem 1-2 dígitos: provavelmente decimal brasileiro
            s = s.replace(',', '.')
        else:
            # Mais de 2 dígitos após vírgula: provavelmente separador de milhar
            s = s.replace(',', '')
    
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
            }
        )

        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        df.dropna(subset=['emissao'], inplace=True)

        # REMOVIDO: não precisa mais do pd.to_numeric após converters
        # As colunas já vêm como float do parse_ptbr
        
        # Preenche apenas valores None/NaN com 0
        for col in ['quantidade', 'vlr_final']:
            if col in df.columns:
                df[col] = df[col].fillna(0.0)

        # Calcula o valor total
        df['vlr_total_produto'] = (df['quantidade'] * df['vlr_final']).round(2)
        
        df['codigo'] = df.get('codigo', '').astype(str)
        
        # DEBUG: Mostra algumas linhas para verificar os valores
        st.sidebar.write("🔍 DEBUG - Primeiras 5 linhas:")
        debug_cols = ['quantidade', 'vlr_final', 'vlr_total_produto']
        st.sidebar.dataframe(df[debug_cols].head())
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'vendas.xlsx' não encontrado. Verifique se ele está na pasta do projeto.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar a planilha: {e}")
        return None

df_original = carregar_dados()

# Resto do código permanece igual...
