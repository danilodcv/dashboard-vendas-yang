import streamlit as st
import pandas as pd

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
    Trata a coluna de data para garantir que seja do tipo datetime.
    """
    try:
        df = pd.read_excel("vendas.xlsx")
        # Mantém a coluna original para diagnóstico
        df['emissao_original'] = df['emissao']
        # Converte a coluna 'emissao' para o formato de data, tratando possíveis erros.
        df['emissao'] = pd.to_datetime(df['emissao'], errors='coerce')
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

    # --- NOVO: Ferramenta de Diagnóstico de Datas ---
    st.sidebar.markdown("### Ferramentas de Análise")
    with st.sidebar.expander("Clique para Diagnóstico de Datas"):
        st.info("Esta seção ajuda a encontrar linhas com datas inválidas na sua planilha.")
        # Identifica as linhas onde a conversão de data falhou (resultou em NaT)
        linhas_com_erro = df[df['emissao'].isnull()]
        
        if not linhas_com_erro.empty:
            st.warning(f"Encontramos {len(linhas_com_erro)} linhas com datas em branco ou em formato incorreto.")
            st.write("Abaixo estão as linhas problemáticas. Corrija-as no seu arquivo `vendas.xlsx`:")
            # Mostra as colunas relevantes das linhas com erro
            st.dataframe(linhas_com_erro[['pedido', 'cliente', 'emissao_original']].rename(columns={
                'pedido': 'Nº Pedido',
                'cliente': 'Cliente',
                'emissao_original': 'Valor da Data com Erro'
            }))
        else:
            st.success("Ótima notícia! Nenhuma data inválida foi encontrada na planilha.")


    # --- Lógica de Filtragem ---
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
                    'pedido', NOME_DA_COLUNA_CLIENTES, 'emissao', 'produto',
                    'quantidade', 'vlr_unitario', 'vlr_total_produto'
                ]
                
                colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
                
                compras_cliente_display = compras_cliente[colunas_existentes].rename(columns={
                    'pedido': 'Nº Pedido',
                    NOME_DA_COLUNA_CLIENTES: 'Cliente',
                    'emissao': 'Data da Compra',
                    'produto': 'Produto',
                    'quantidade': 'Qtd.',
                    'vlr_unitario': 'Valor Unitário (R$)',
                    'vlr_total_produto': 'Valor Total (R$)'
                })
                
                # --- Tratamento Robusto de Datas Inválidas ---
                compras_cliente_display = compras_cliente_display.copy()
                if 'Data da Compra' in compras_cliente_display.columns:
                    datas_invalidas = compras_cliente_display['Data da Compra'].isnull().sum()
                    
                    if datas_invalidas > 0:
                        st.warning(f"Atenção: {datas_invalidas} registro(s) de compra foram ocultados da tabela abaixo por terem datas inválidas ou em branco.")
                        compras_cliente_display.dropna(subset=['Data da Compra'], inplace=True)

                    if not compras_cliente_display.empty:
                        compras_cliente_display['Data da Compra'] = compras_cliente_display['Data da Compra'].dt.strftime('%d/%m/%Y')
                
                st.dataframe(compras_cliente_display, use_container_width=True, hide_index=True)

            else:
                st.warning("Nenhum cliente encontrado com o nome especificado.")
        else:
            st.info("Digite o nome de um cliente no campo acima para iniciar a busca.")

