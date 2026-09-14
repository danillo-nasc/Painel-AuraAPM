import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. Configuração da Página
st.set_page_config(
    page_title="AuraAPM | Central de Governança & SRE Locaweb",
    page_icon="🛡️",
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
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 1.7rem;
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

# 3. Massa de Dados de Contingência (Mock)
MOCK_INCIDENTES = [
    {
        "cluster_id": "CL-a8f3b1", "prioridade": "alta", "servico": "mysql-primary",
        "ocorrencias": 840, "hosts_afetados": 6, "duracao_media_s": 1950.0,
        "ola_limite_s": 1800, "consumo_ola_pct": 108.3, "ola_violado": True,
        "score_risco_preditivo": 95.0, "status_governanca": "VIOLADO",
        "padrao_falha": "MySQL Connection Timeout during failover sync",
        "diagnostico_ia": "Saturação de pool de conexões com deadlock cascata em réplicas de leitura."
    },
    {
        "cluster_id": "CL-3c4d12", "prioridade": "alta", "servico": "dns-authoritative",
        "ocorrencias": 320, "hosts_afetados": 2, "duracao_media_s": 1350.0,
        "ola_limite_s": 1800, "consumo_ola_pct": 75.0, "ola_violado": False,
        "score_risco_preditivo": 78.5, "status_governanca": "CRÍTICO",
        "padrao_falha": "ICMP/DNS resolution dropped packets",
        "diagnostico_ia": "Queda intermitente em links de borda atingindo 75% da janela limite de OLA."
    },
    {
        "cluster_id": "CL-7b89f0", "prioridade": "media", "servico": "letsencrypt-auto",
        "ocorrencias": 190, "hosts_afetados": 1, "duracao_media_s": 4200.0,
        "ola_limite_s": 14400, "consumo_ola_pct": 29.2, "ola_violado": False,
        "score_risco_preditivo": 42.0, "status_governanca": "CONTROLADO",
        "padrao_falha": "Rate limit exceeded on SSL certificate renewal",
        "diagnostico_ia": "Renovação agendada em fila única; impacto restrito e OLA sob controle."
    },
    {
        "cluster_id": "CL-0e1f3a", "prioridade": "baixa", "servico": "bacula-backup",
        "ocorrencias": 70, "hosts_afetados": 4, "duracao_media_s": 12000.0,
        "ola_limite_s": 86400, "consumo_ola_pct": 13.9, "ola_violado": False,
        "score_risco_preditivo": 22.0, "status_governanca": "CONTROLADO",
        "padrao_falha": "I/O wait threshold elevated during nightly tape dump",
        "diagnostico_ia": "Rotina batch dentro do limiar de dispersão esperado."
    }
]

# 4. Conexão Resiliente com Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1n5eYSf_Nt0Vs-qZ2yHeyqWuyJjl6SceYevAocJLmxTw/export?format=csv"

@st.cache_data(ttl=10)
def carregar_dados(url):
    try:
        df_raw = pd.read_csv(url)
        if df_raw.empty or len(df_raw.columns) < 3:
            return pd.DataFrame(MOCK_INCIDENTES), True, df_raw
        return df_raw, False, df_raw
    except Exception:
        return pd.DataFrame(MOCK_INCIDENTES), True, pd.DataFrame()

df_incidentes, is_mock, df_sheets_raw = carregar_dados(SHEET_URL)

# 5. Barra Lateral (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/server.png", width=54)
    st.title("AuraAPM")
    st.caption("AIOps & Governança SRE")
    st.markdown("---")
    
    st.subheader("📡 Status da Operação")
    if is_mock:
        st.warning("⚠️ Modo Simulado Ativo")
        st.caption("Apresentando dados estruturados de contingência.")
    else:
        st.success("● Conectado ao DB_AuraAPM")
        st.caption(f"Registros ativos: {len(df_incidentes)}")
        
    st.info("🔄 Polling: 15s")
    st.markdown("---")
    filtro_servico = st.multiselect("Filtrar por Serviço:", options=df_incidentes["servico"].unique(), default=[])

if filtro_servico:
    df_incidentes = df_incidentes[df_incidentes["servico"].isin(filtro_servico)]

# 6. Cabeçalho Principal
st.title("🛡️ AuraAPM — Central de Governança e Inteligência SRE")
st.markdown("Monitoramento automatizado com **IA Generativa**, **Deduplicação Determinística** e **Controle de OLA**.")

# 7. Cálculo das Métricas de Topo (Alinhadas aos 4 Desafios Locaweb)
total_logs_brutos = int(df_incidentes["ocorrencias"].sum()) if "ocorrencias" in df_incidentes.columns else 1420
clusters_count = len(df_incidentes)
ruido_pct = round(((total_logs_brutos - clusters_count) / total_logs_brutos) * 100, 1) if total_logs_brutos > 0 else 99.0

total_violados = int((df_incidentes["status_governanca"] == "VIOLADO").sum()) if "status_governanca" in df_incidentes.columns else 0
conformidade_ola = round(((clusters_count - total_violados) / clusters_count) * 100, 1) if clusters_count > 0 else 100.0

criticos_count = int((df_incidentes["status_governanca"] == "CRÍTICO").sum()) if "status_governanca" in df_incidentes.columns else 0
tokens_poupados = (total_logs_brutos - clusters_count) * 25  # Estimativa de tokens economizados

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Fadiga de Alertas (Redução)</div>
        <div class="metric-value">{ruido_pct}%</div>
        <span class="metric-badge badge-green">-{total_logs_brutos - clusters_count} ruídos filtrados</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    badge_ola = "badge-green" if conformidade_ola >= 90 else ("badge-yellow" if conformidade_ola >= 75 else "badge-red")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Taxa Conformidade OLA</div>
        <div class="metric-value">{conformidade_ola}%</div>
        <span class="metric-badge {badge_ola}">{total_violados} violações ativas</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Risco Preditivo Crítico</div>
        <div class="metric-value">{criticos_count}</div>
        <span class="metric-badge badge-yellow">Requer atenção imediata</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">FinOps (Tokens Poupados)</div>
        <div class="metric-value">{tokens_poupados:,}</div>
        <span class="metric-badge badge-blue">Custo evitado na LLM</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 8. Abas Operacionais
tab_war_room, tab_governanca, tab_finops, tab_diagnosticos = st.tabs([
    "🚨 War Room (Triagem Rápida)",
    "📈 Governança Preditiva de OLA",
    "⚡ FinOps de IA & Eficiência",
    "📝 Diagnósticos dos Agentes"
])

# ABA 1: WAR ROOM
with tab_war_room:
    st.subheader("Filtragem de Incidentes Prioritários")
    
    violados = df_incidentes[df_incidentes["status_governanca"] == "VIOLADO"] if "status_governanca" in df_incidentes.columns else pd.DataFrame()
    criticos = df_incidentes[df_incidentes["status_governanca"] == "CRÍTICO"] if "status_governanca" in df_incidentes.columns else pd.DataFrame()
    
    if not violados.empty:
        for _, row in violados.iterrows():
            st.error(f"⚠️ **[VIOLAÇÃO ATIVA] {row['cluster_id']} - {row['servico']}**: Consumo de {row['consumo_ola_pct']}% do OLA. {row.get('diagnostico_ia', '')}")
            
    if not criticos.empty:
        for _, row in criticos.iterrows():
            st.warning(f"⚡ **[RISCO PREDITIVO ELEVADO] {row['cluster_id']} - {row['servico']}**: Score {row['score_risco_preditivo']}/100. Consumo de {row['consumo_ola_pct']}% do OLA.")

    st.markdown("### Matriz Operacional Consolidada")
    colunas_tabela = [c for c in [
        "cluster_id", "prioridade", "servico", "ocorrencias", 
        "hosts_afetados", "consumo_ola_pct", "score_risco_preditivo", "status_governanca"
    ] if c in df_incidentes.columns]
    
    st.dataframe(df_incidentes[colunas_tabela], use_container_width=True, hide_index=True)

# ABA 2: GOVERNANÇA PREDITIVA
with tab_governanca:
    st.subheader("Previsibilidade de Violação e Dispersão de Falhas")
    g1, g2 = st.columns(2)
    
    with g1:
        if "consumo_ola_pct" in df_incidentes.columns and "score_risco_preditivo" in df_incidentes.columns:
            fig_scatter = px.scatter(
                df_incidentes,
                x="consumo_ola_pct",
                y="score_risco_preditivo",
                size="ocorrencias",
                color="status_governanca",
                color_discrete_map={"VIOLADO": "#E74C3C", "CRÍTICO": "#F39C12", "CONTROLADO": "#2ECC71"},
                hover_name="servico",
                labels={"consumo_ola_pct": "Consumo de OLA (%)", "score_risco_preditivo": "Score de Risco Preditivo"},
                title="Matriz: Consumo de Acordo vs. Probabilidade de Colapso"
            )
            fig_scatter.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="Limite OLA")
            fig_scatter.update_layout(template="plotly_dark", height=380)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
    with g2:
        if "servico" in df_incidentes.columns and "duracao_media_s" in df_incidentes.columns:
            fig_bar = px.bar(
                df_incidentes,
                x="servico",
                y="duracao_media_s",
                color="prioridade",
                title="Duração Média dos Incidentes por Serviço (s)",
                labels={"duracao_media_s": "Duração Média (segundos)", "servico": "Componente"}
            )
            fig_bar.update_layout(template="plotly_dark", height=380)
            st.plotly_chart(fig_bar, use_container_width=True)

# ABA 3: FINOPS & EFICIÊNCIA
with tab_finops:
    st.subheader("Otimização Computacional e Combate à Fadiga de Alertas")
    c_gauge, c_desc = st.columns([1, 2])
    
    with c_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ruido_pct,
            title={'text': "Taxa de Compressão de Ruído (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#27AE60"},
                'steps': [
                    {'range': [0, 50], 'color': "#5c2b29"},
                    {'range': [50, 85], 'color': "#63501a"},
                    {'range': [85, 100], 'color': "#1a4d2e"}
                ]
            }
        ))
        fig_gauge.update_layout(template="plotly_dark", height=320, margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with c_desc:
        st.markdown("#### Impacto da Camada Determinística (Python)")
        st.write(
            f"O algoritmo de deduplicação processou **{total_logs_brutos} eventos de log brutos**, "
            f"eliminando redundâncias de stack trace e convertendo o volume em apenas **{clusters_count} clusters acionáveis**."
        )
        st.markdown(
            f"- **Volume bruto evitado no Gemini:** Redução de ~{tokens_poupados:,} tokens por execução.\n"
            f"- **Tempo de inferência reduzido:** O Gemini recebe apenas o JSON pré-estruturado, acelerando o retorno no Telegram."
        )

# ABA 4: DIAGNÓSTICOS DOS AGENTES
with tab_diagnosticos:
    st.subheader("Histórico de Análises Geradas pela IA")
    for idx, row in df_incidentes.iterrows():
        with st.expander(f"📌 {row.get('cluster_id', 'Cluster')} - {row.get('servico', 'Serviço')} (Status: {row.get('status_governanca', 'N/A')})"):
            st.markdown(f"**Padrão de Falha Identificado:** `{row.get('padrao_falha', 'N/A')}`")
            st.markdown(f"**Diagnóstico Preditivo:** {row.get('diagnostico_ia', 'Sem análise textual registrada.')}")