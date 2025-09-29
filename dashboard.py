import streamlit as st
import pandas as pd
import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Histórico de Vendas - YANG Molduras",
    page_icon="📊",
    layout="wide"
)

# --- Carregamento de Dados ---
@st.cache_data
def carregar_dados():
    """
    Função para carregar os dados da planilha 'vendas.xlsx'.
    Trata a coluna de data para garantir que seja do tipo datetime,
    interpretando o formato brasileiro (dia/mês/ano).
    """
    try:
        df = pd.read_excel("vendas.xlsx")
        # Converte a coluna 'emissao' para o formato de data, tratando possíveis erros.
        df['emissao'] = pd.to_datetime(df['emissao'], dayfirst=True, errors='coerce')
        # Remove linhas onde a data não pôde ser convertida
        df.dropna(subset=['emissao'], inplace=True)
        return df
    except FileNotFoundError:
        st.error("O arquivo 'vendas.xlsx' não foi encontrado. Por favor, coloque-o na mesma pasta do script.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler a planilha: {e}")
        return None

df = carregar_dados()

# --- Interface do Dashboard ---
if df is not None:
    # --- Barra Lateral ---
    st.sidebar.title("YANG Molduras")
    try:
        st.sidebar.image("sua_logo.png", use_container_width=True)
    except Exception as e:
        st.sidebar.warning("Logo não encontrada.")

    st.sidebar.markdown("---")

    # --- Conteúdo Principal ---
    st.title("📊 Consulta de Vendas - YANG Molduras")
    st.markdown("---")

    # --- 1) Lógica de Filtragem por Cliente ---
    st.subheader("Consulta por Cliente")
    NOME_DA_COLUNA_CLIENTES = 'cliente'

    if NOME_DA_COLUNA_CLIENTES not in df.columns:
        st.error(f"Erro Crítico: A coluna '{NOME_DA_COLUNA_CLIENTES}' não foi encontrada na planilha.")
    else:
        cliente_pesquisado = st.text_input("Digite o nome do cliente para consultar:")

        if cliente_pesquisado:
            compras_cliente = df[df[NOME_DA_COLUNA_CLIENTES].str.contains(cliente_pesquisado, case=False, na=False)]

            if not compras_cliente.empty:
                st.success(f"🔍 Exibindo compras para clientes contendo '{cliente_pesquisado}':")

                colunas_desejadas = [
                    'pedido', NOME_DA_COLUNA_CLIENTES, 'codigo', 'emissao', 'produto',
                    'quantidade', 'vlr_unitario', 'vlr_total_produto'
                ]
                
                colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
                
                compras_cliente_display = compras_cliente[colunas_existentes].rename(columns={
                    'pedido': 'Nº Pedido',
                    NOME_DA_COLUNA_CLIENTES: 'Cliente',
                    'codigo': 'Código',
                    'emissao': 'Data da Compra',
                    'produto': 'Produto',
                    'quantidade': 'Qtd.',
                    'vlr_unitario': 'Valor Unitário (R$)',
                    'vlr_total_produto': 'Valor Total (R$)'
                })
                
                compras_cliente_display['Data da Compra'] = compras_cliente_display['Data da Compra'].dt.strftime('%d/%m/%Y')
                st.dataframe(compras_cliente_display, use_container_width=True, hide_index=True)

            else:
                st.warning("Nenhum cliente encontrado com o nome especificado.")
        else:
            st.info("Digite o nome de um cliente no campo acima para iniciar a busca.")

    st.markdown("\n\n---\n\n")

    # --- 2) Filtro por Período ---
    st.subheader("Consulta por Período")
    col1, col2 = st.columns(2)
    
    # Define as datas mínima e máxima com base nos dados da planilha
    min_date = df['emissao'].min().date()
    max_date = df['emissao'].max().date()

    with col1:
        data_inicial = st.date_input("Data Inicial", min_date, min_value=min_date, max_value=max_date)
    with col2:
        data_final = st.date_input("Data Final", max_date, min_value=min_date, max_value=max_date)

    if data_inicial and data_final:
        if data_inicial > data_final:
            st.error("A data inicial não pode ser posterior à data final.")
        else:
            # Converte as datas de input para o formato datetime para comparação
            data_inicial_ts = pd.to_datetime(data_inicial)
            data_final_ts = pd.to_datetime(data_final) + pd.Timedelta(days=1) # Adiciona 1 dia para incluir o dia final

            vendas_periodo = df[(df['emissao'] >= data_inicial_ts) & (df['emissao'] < data_final_ts)]
            
            if not vendas_periodo.empty:
                st.success(f"Exibindo {len(vendas_periodo)} vendas de {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}")
                
                colunas_periodo = ['pedido', 'cliente', 'codigo', 'produto', 'vlr_total_produto']
                colunas_periodo_existentes = [col for col in colunas_periodo if col in vendas_periodo.columns]
                
                vendas_periodo_display = vendas_periodo[colunas_periodo_existentes].rename(columns={
                    'pedido': 'Nº Pedido',
                    'cliente': 'Cliente',
                    'codigo': 'Código',
                    'produto': 'Produto',
                    'vlr_total_produto': 'Valor Total (R$)'
                })
                st.dataframe(vendas_periodo_display, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma venda encontrada no período selecionado.")

    st.markdown("\n\n---\n\n")

    # --- 3) Filtro por Código de Produto ---
    st.subheader("Consulta por Código do Produto")
    
    # Garante que a coluna 'codigo' seja tratada como string para a busca
    df['codigo'] = df['codigo'].astype(str)
    
    lista_codigos = sorted(df['codigo'].unique())
    codigo_pesquisado = st.selectbox("Selecione ou digite o código do produto:", options=lista_codigos, index=None, placeholder="Escolha um código...")

    if codigo_pesquisado:
        vendas_produto = df[df['codigo'] == codigo_pesquisado]

        if not vendas_produto.empty:
            st.success(f"Exibindo {len(vendas_produto)} vendas para o produto com código '{codigo_pesquisado}'")
            
            colunas_produto = ['emissao', 'quantidade']
            vendas_produto_display = vendas_produto[colunas_produto].rename(columns={
                'emissao': 'Data da Venda',
                'quantidade': 'Quantidade Vendida'
            })
            
            vendas_produto_display['Data da Venda'] = vendas_produto_display['Data da Venda'].dt.strftime('%d/%m/%Y')
            
            # Ordena pela data mais recente
            vendas_produto_display = vendas_produto_display.sort_values(by='Data da Venda', ascending=False)
            
            st.dataframe(vendas_produto_display, use_container_width=True, hide_index=True)
        else:
            # Esta mensagem raramente aparecerá por causa do selectbox, mas é uma boa prática
            st.info("Nenhuma venda encontrada para o código selecionado.")


