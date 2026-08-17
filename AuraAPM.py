import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. Configuração da Página
st.set_page_config(
    page_title="AuraAPM | Painel de Inteligência Preditiva",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Atualização automática a cada 15 segundos
st_autorefresh(interval=15 * 1000, key="auraapm_refresh")

# 2. Estilização CSS Moderna (Dark Theme)
st.markdown("""
<style>
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title {
        color: #8b949e;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .badge-green { background-color: #238636; color: #ffffff; }
    .badge-yellow { background-color: #9e6a03; color: #ffffff; }
    .badge-red { background-color: #da3633; color: #ffffff; }
    .badge-blue { background-color: #1f6feb; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# 3. URL da Planilha Google Sheets (CSV Público)
# Certifique-se de substituir pelo seu link de exportação CSV público
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT5K760U3Q0h3k4F2B-bIqYQeS3B2E9mD0oW0eX7Z9/pub?output=csv"

@st.cache_data(ttl=10)
def carregar_dados(url):
    try:
        df = pd.read_csv(url)
        # Limpeza e conversão segura de datas
        if "DATA" in df.columns:
            df["DATA_DT"] = pd.to_datetime(df["DATA"], errors="coerce")
            df = df.sort_values(by="DATA_DT", ascending=True)

        # Conversão de colunas numéricas
        numeric_cols = [
            "TOTAL_INCIDENTES", "PREV_D1", "PREV_D7", 
            "ELEGIVEIS_KPI", "P2_VIOLADOS", "P3_VIOLADOS", "RUIDO_MONITORAMENTO"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
        return pd.DataFrame()

df = carregar_dados(SHEET_URL)

# 4. Barra Lateral (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/server.png", width=64)
    st.title("AuraAPM")
    st.caption("AIOps & Governança Preditiva")
    st.markdown("---")
    
    st.subheader("🔍 Filtros")
    filtro_palavra = st.text_input("Buscar nas Análises:", "")
    
    st.markdown("---")
    st.subheader("📡 Status da Operação")
    st.success("● Agente Operacional")
    st.info("🔄 Polling: 15s")
    
    if not df.empty and "DATA_DT" in df.columns and df["DATA_DT"].notna().any():
        ultimo_sync = df["DATA_DT"].dropna().iloc[-1].strftime("%d/%m/%Y %H:%M:%S")
        st.caption(f"Última Carga: {ultimo_sync}")

# 5. Cabeçalho Principal
st.title("🔮 AuraAPM | Painel Preditivo de Incidentes")
st.markdown("Monitoramento automatizado com **IA Generativa**, **AIOps** e **Governança de OLA**.")

if df.empty:
    st.warning("⚠️ Nenhum dado registrado na base. Envie um arquivo de logs no Telegram para iniciar as análises.")
    st.stop()

# Captura do registro mais recente
latest = df.iloc[-1]

# 6. Cards de Métricas Principais (KPIs & Predição)
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Incidentes Atuais</div>
        <div class="metric-value">{int(latest.get('TOTAL_INCIDENTES', 0))}</div>
        <span class="metric-badge badge-blue">Elegíveis: {int(latest.get('ELEGIVEIS_KPI', 0))}</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    prev_d1 = int(latest.get('PREV_D1', 0))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Projeção D+1</div>
        <div class="metric-value">{prev_d1}</div>
        <span class="metric-badge badge-blue">Próximo Dia</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    prev_d7 = int(latest.get('PREV_D7', 0))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Projeção D+7</div>
        <div class="metric-value">{prev_d7}</div>
        <span class="metric-badge badge-blue">Próx. 7 Dias</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    p2_ating = str(latest.get('P2_ATINGIMENTO', 'N/A'))
    p2_viol = int(latest.get('P2_VIOLADOS', 0))
    badge_cor = "badge-green" if "150%" in p2_ating or "125%" in p2_ating else ("badge-yellow" if "100%" in p2_ating else "badge-red")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Meta OLA P2 (Alta)</div>
        <div class="metric-value">{p2_viol} <span style="font-size:1rem;color:#8b949e;">quebras</span></div>
        <span class="metric-badge {badge_cor}">Atingimento: {p2_ating}</span>
    </div>
    """, unsafe_allow_html=True)

with c5:
    p3_ating = str(latest.get('P3_ATINGIMENTO', 'N/A'))
    p3_viol = int(latest.get('P3_VIOLADOS', 0))
    badge_cor_p3 = "badge-green" if "150%" in p3_ating or "125%" in p3_ating else ("badge-yellow" if "100%" in p3_ating else "badge-red")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Meta OLA P3 (Média)</div>
        <div class="metric-value">{p3_viol} <span style="font-size:1rem;color:#8b949e;">quebras</span></div>
        <span class="metric-badge {badge_cor_p3}">Atingimento: {p3_ating}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 7. Abas de Visualização
tab_pred, tab_relatorios, tab_dados = st.tabs([
    "📈 Visão Preditiva & OLA",
    "📝 Diagnósticos & Decisão Operacional",
    "📋 Tabela Completa"
])

# ABA 1: GRÁFICOS E TENDÊNCIAS
with tab_pred:
    g1, g2 = st.columns(2)
    
    with g1:
        # Gráfico Histórico de Volume vs Projeções
        fig_vol = go.Figure()
        if "DATA_DT" in df.columns:
            fig_vol.add_trace(go.Bar(
                x=df["DATA_DT"].dt.strftime("%d/%m %H:%M"),
                y=df["TOTAL_INCIDENTES"],
                name="Volume Real",
                marker_color="#1f6feb"
            ))
            fig_vol.add_trace(go.Scatter(
                x=df["DATA_DT"].dt.strftime("%d/%m %H:%M"),
                y=df["PREV_D1"],
                name="Previsão D+1",
                mode="lines+markers",
                line=dict(color="#2ea043", width=2, dash="dot")
            ))
        fig_vol.update_layout(
            title="Evolução de Volume Processado vs Previsão D+1",
            template="plotly_dark",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    with g2:
        # Gráfico de Quebras de OLA e Ruído de Monitoramento
        fig_ola = go.Figure()
        if "DATA_DT" in df.columns:
            fig_ola.add_trace(go.Bar(
                x=df["DATA_DT"].dt.strftime("%d/%m %H:%M"),
                y=df["P2_VIOLADOS"],
                name="P2 Violados (>4h)",
                marker_color="#da3633"
            ))
            fig_ola.add_trace(go.Bar(
                x=df["DATA_DT"].dt.strftime("%d/%m %H:%M"),
                y=df["P3_VIOLADOS"],
                name="P3 Violados (>12h)",
                marker_color="#d29922"
            ))
            fig_ola.add_trace(go.Scatter(
                x=df["DATA_DT"].dt.strftime("%d/%m %H:%M"),
                y=df["RUIDO_MONITORAMENTO"],
                name="Ruído (Sem Intervenção)",
                mode="lines+markers",
                line=dict(color="#a371f7", width=2)
            ))
        fig_ola.update_layout(
            title="Incidentes Fora da OLA & Ruído de Monitoramento",
            template="plotly_dark",
            barmode="stack",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ola, use_container_width=True)

# ABA 2: RELATÓRIOS SANFONADOS
with tab_relatorios:
    st.subheader("📋 Diagnósticos dos Agentes de IA")
    
    # Aplica filtro de busca se informado
    df_exibicao = df.copy()
    if filtro_palavra:
        df_exibicao = df_exibicao[df_exibicao["ANALISE"].astype(str).str.contains(filtro_palavra, case=False, na=False)]

    for idx, row in df_exibicao.iloc[::-1].iterrows():
        data_str = pd.to_datetime(row.get('DATA', '')).strftime('%d/%m/%Y às %H:%M:%S') if pd.notna(row.get('DATA')) else "Data N/A"
        
        with st.expander(f"📌 Relatório Executivo - {data_str} (Volume: {int(row.get('TOTAL_INCIDENTES', 0))} | D+1: {int(row.get('PREV_D1', 0))})"):
            st.markdown("### 📝 Resumo Operacional")
            st.info(row.get("RESUMO", "Sem resumo informado."))
            
            st.markdown("### 🔍 Diagnóstico AIOps & Ações Preventivas")
            st.markdown(row.get("ANALISE", "Sem análise detalhada registrada."))

# ABA 3: TABELA COMPLETA
with tab_dados:
    st.subheader("Base de Dados Completa")
    colunas_visiveis = [
        "DATA", "TOTAL_INCIDENTES", "PREV_D1", "PREV_D7", 
        "P2_VIOLADOS", "P2_ATINGIMENTO", "P3_VIOLADOS", "P3_ATINGIMENTO", 
        "RUIDO_MONITORAMENTO", "RESUMO"
    ]
    st.dataframe(df[[c for c in colunas_visiveis if c in df.columns]], use_container_width=True)