import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# 1. Configuração da página do Streamlit
st.set_page_config(
    page_title="Dashboard AuraAPM",
    page_icon="📊",
    layout="wide"
)

# 2. Atualização automática da tela a cada 10 segundos (10.000 ms)
st_autorefresh(interval=10000, key="datarefresh")

# 3. URL da sua planilha do Google Sheets já no formato CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1n5eYSf_Nt0Vs-qZ2yHeyqWuyJjl6SceYevAocJLmxTw/export?format=csv"

# Função com cache rápido de 5s para ler os dados do Google Sheets
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        df = pd.read_csv(SHEET_URL)
        # ⚠️ TRATAMENTO DE ERRO: 'errors="coerce"' converte #ERROR! em nulo (NaT) sem derrubar a aplicação
        if "DATA" in df.columns:
            df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return pd.DataFrame()

# --- HEADER PRINCIPAL ---
st.title("📊 Painel de Análises em Tempo Real - AuraAPM")
st.caption("Alimentado automaticamente via n8n & Telegram")

df = carregar_dados()

if not df.empty:
    # --- 1. BLOCO DE KPIs (CARDS MÉTRICOS) ---
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Total de Análises Processadas", len(df))
    
    # Busca a última data ignorando valores inválidos/nulos
    datas_validas = df["DATA"].dropna() if "DATA" in df.columns else pd.Series()
    if not datas_validas.empty:
        ultima_data = datas_validas.max().strftime("%d/%m/%Y %H:%M:%S")
    else:
        ultima_data = "N/A"
        
    col2.metric("Último Registro", ultima_data)
    col3.metric("Status do Agente", "🟢 Operacional")

    st.divider()

    # --- 2. BARRA LATERAL (FILTROS INTERATIVOS) ---
    st.sidebar.header("🔍 Filtros do Painel")
    busca = st.sidebar.text_input("Buscar palavra-chave nos relatórios:")
    
    df_filtrado = df.copy()
    if busca:
        df_filtrado = df_filtrado[
            df_filtrado["ANALISE"].astype(str).str.contains(busca, case=False, na=False) |
            df_filtrado["RESUMO"].astype(str).str.contains(busca, case=False, na=False)
        ]

    # --- 3. ABAS DE EXIBIÇÃO ---
    tab1, tab2 = st.tabs(["📌 Relatórios dos Agentes", "📈 Visão em Tabela & Gráficos"])

    with tab1:
        st.subheader("Análises Mais Recentes")
        
        # Exibe os relatórios do mais recente para o mais antigo (ordem inversa)
        for idx, row in df_filtrado.iloc[::-1].iterrows():
            data_formatada = row["DATA"].strftime("%d/%m/%Y às %H:%M:%S") if pd.notnull(row["DATA"]) else "Data não identificada"
            
            with st.expander(f"📄 Relatório de {data_formatada}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("#### 📝 Resumo do Agente 1")
                    st.info(row.get("RESUMO", "Sem resumo registrado."))
                
                with col_b:
                    st.markdown("#### 🔍 Análise Detalhada (Agente 2)")
                    st.write(row.get("ANALISE", "Sem análise aprofundada."))

    with tab2:
        st.subheader("Base de Dados Completa")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Gráfico de volume por dia considerando apenas datas válidas
        df_grafico_dados = df_filtrado.dropna(subset=["DATA"]) if "DATA" in df_filtrado.columns else pd.DataFrame()
        if not df_grafico_dados.empty:
            st.subheader("Volume de Análises por Dia")
            df_grafico = df_grafico_dados.groupby(df_grafico_dados["DATA"].dt.date).size().reset_index(name="Análises")
            fig = px.bar(df_grafico, x="DATA", y="Análises", title="Quantidade de Relatórios Gerados")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Nenhum dado encontrado na planilha ainda. Envie um arquivo pelo Telegram para iniciar o processamento!")
