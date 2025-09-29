import streamlit as st
import pandas as pd

# --- Configuração da Página ---
# Define o título que aparece na aba do navegador e o layout.
st.set_page_config(
    page_title="Histórico de Vendas - 2023 a 2025",
    page_icon="📊",
    layout="wide"
)

# --- Carregamento de Dados ---
@st.cache_data
def carregar_dados():
    """
    Função para carregar os dados da planilha 'vendas.xlsx'.
    Trata a coluna de data para garantir que seja do tipo datetime.
    """
    try:
        df = pd.read_excel("vendas.xlsx")
        # Converte a coluna 'emissao' para o formato de data, tratando possíveis erros.
        df['emissao'] = pd.to_datetime(df['emissao'], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("O arquivo 'vendas.xlsx' não foi encontrado. Por favor, coloque-o na mesma pasta do script.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler a planilha: {e}")
        return None

# Carrega o dataframe.
df = carregar_dados()

# --- Interface do Dashboard ---

if df is not None:
    # --- Barra Lateral com Logo e Nome da Empresa ---
    st.sidebar.title("YANG")
    try:
        # IMPORTANTE: Substitua "sua_logo.png" pelo nome do seu arquivo de imagem.
        # O arquivo da logo deve estar na mesma pasta do script.
        st.sidebar.image("sua_logo.png", use_container_width=True)
    except Exception as e:
        st.sidebar.warning("Logo não encontrada. Verifique se o nome do arquivo está correto e na pasta do projeto.")

    st.sidebar.markdown("---")



    # --- Conteúdo Principal ---
    st.title("📊 Consulta de Vendas - de 2023 a 2025")
    st.markdown("---")

    # --- Lógica de Filtragem ---
    NOME_DA_COLUNA_CLIENTES = 'cliente'

    if NOME_DA_COLUNA_CLIENTES not in df.columns:
        st.error(f"Erro Crítico: A coluna '{NOME_DA_COLUNA_CLIENTES}' não foi encontrada na planilha. Por favor, ajuste o nome da coluna no seu arquivo .xlsx ou no código.")
    else:
        cliente_pesquisado = st.text_input("Nome do Cliente:")

        if cliente_pesquisado:
            compras_cliente = df[df[NOME_DA_COLUNA_CLIENTES].str.contains(cliente_pesquisado, case=False, na=False)]

            if not compras_cliente.empty:
                st.success(f"🔍 Exibindo compras para clientes contendo '{cliente_pesquisado}':")

                colunas_desejadas = [
                    'pedido',
                    NOME_DA_COLUNA_CLIENTES,
                    'emissao',
                    'produto',
                    'quantidade',
                    'vlr_unitario',
                    'vlr_total_produto'
                ]
                
                colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
                
                if len(colunas_existentes) != len(colunas_desejadas):
                    st.warning("Algumas colunas solicitadas não foram encontradas na planilha e não serão exibidas.")

                compras_cliente_display = compras_cliente[colunas_existentes].rename(columns={
                    'pedido': 'Nº Pedido',
                    NOME_DA_COLUNA_CLIENTES: 'Cliente',
                    'emissao': 'Data da Compra',
                    'produto': 'Produto',
                    'quantidade': 'Qtd.',
                    'vlr_unitario': 'Valor Unitário (R$)',
                    'vlr_total_produto': 'Valor Total (R$)'
                })

                compras_cliente_display = compras_cliente_display.copy()
                if 'Data da Compra' in compras_cliente_display.columns:
                    compras_cliente_display['Data da Compra'] = pd.to_datetime(compras_cliente_display['Data da Compra']).dt.strftime('%d/%m/%Y')
                
                st.dataframe(compras_cliente_display, use_container_width=True, hide_index=True)

            else:
                st.warning("Nenhum cliente encontrado com o nome especificado.")
        else:
            st.info("Digite o nome de um cliente no campo acima para iniciar a busca.")




