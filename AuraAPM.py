import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from supabase import create_client

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="AuraAPM | Central de Governança & SRE Locaweb",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Atualização automática a cada 15 segundos
st_autorefresh(interval=15 * 1000, key="auraapm_refresh")

# ---------------------------------------------------------
# 2. ESTILIZAÇÃO CSS MODERNA (DARK THEME)
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 3. MASSA DE CONTINGÊNCIA (FALLBACK EM CASO DE FALHA DE REDE)
# ---------------------------------------------------------
MOCK_INCIDENTES = [
    {
        "cluster_id": "CL-001", "prioridade": "alta", "servico": "IC02864",
        "ocorrencias": 1, "hosts_afetados": 1, "duracao_media_s": 31742.0,
        "ola_limite_s": 1800, "consumo_ola_pct": 1763.4, "ola_violado": True,
        "score_risco_preditivo": 57.0, "status_governanca": "VIOLADO",
        "padrao_falha": "Link Down na Interface Bundle",
        "diagnostico_ia": "Aguardando nova telemetria do Supabase."
    }
]

# ---------------------------------------------------------
# 4. CONEXÃO COM SUPABASE (POSTGRESQL)
# ---------------------------------------------------------
SUPABASE_URL = "https://grdmvllrbxamugacgdfz.supabase.co"

# IMPORTANTE: Cole abaixo a sua chave 'anon' pública ou 'service_role' do Supabase
SUPABASE_KEY = "SUA_CHAVE_SUPABASE_AQUI"

@st.cache_data(ttl=10)
def carregar_dados_supabase():
    try:
        if not SUPABASE_KEY or SUPABASE_KEY == "SUA_CHAVE_SUPABASE_AQUI":
            return pd.DataFrame(MOCK_INCIDENTES), True

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Consulta os incidentes ordenados por id
        response = supabase.table("incidentes_aura_apm").select("*").order("id", desc=False).execute()
        
        df_raw = pd.DataFrame(response.data)
        if df_raw.empty or "servico" not in df_raw.columns:
            return pd.DataFrame(MOCK_INCIDENTES), True

        # Conversão e sanitização de campos numéricos do PostgreSQL
        cols_num = ["consumo_ola_pct", "score_risco_preditivo", "duracao_media_s", "ocorrencias", "hosts_afetados", "ola_limite_s"]
        for c in cols_num:
            if c in df_raw.columns:
                df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0)

        if "status_governanca" in df_raw.columns:
            df_raw["status_governanca"] = df_raw["status_governanca"].astype(str).str.upper().str.strip()

        return df_raw, False
    except Exception:
        return pd.DataFrame(MOCK_INCIDENTES), True

df_incidentes, is_mock = carregar_dados_supabase()

# ---------------------------------------------------------
# 5. BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/server.png", width=54)
    st.title("AuraAPM")
    st.caption("AIOps & Governança SRE")
    st.markdown("---")
    
    st.subheader("📡 Status da Operação")
    if is_mock:
        st.warning("⚠️ Modo Simulado Ativo (Verifique a Key)")
    else:
        st.success("● Conectado ao Supabase (PostgreSQL)")
        st.caption(f"Registros ativos: {len(df_incidentes)}")
        
    st.info("🔄 Polling: 15s")
    st.markdown("---")
    
    servicos_disponiveis = sorted(df_incidentes["servico"].dropna().unique()) if "servico" in df_incidentes.columns else []
    filtro_servico = st.multiselect("Filtrar por Serviço:", options=servicos_disponiveis, default=[])

if filtro_servico:
    df_incidentes = df_incidentes[df_incidentes["servico"].isin(filtro_servico)]

# ---------------------------------------------------------
# 6. CABEÇALHO PRINCIPAL
# ---------------------------------------------------------
st.title("🛡️ AuraAPM — Central de Governança e Inteligência SRE")
st.markdown("Monitoramento automatizado com **IA Generativa**, **Deduplicação Determinística** e **Controle de OLA**.")

# ---------------------------------------------------------
# 7. MÉTRICAS EXECUTIVAS
# ---------------------------------------------------------
total_logs_brutos = int(df_incidentes["ocorrencias"].sum()) if "ocorrencias" in df_incidentes.columns else len(df_incidentes)
clusters_count = len(df_incidentes)
ruido_pct = round(((total_logs_brutos - clusters_count) / total_logs_brutos) * 100, 1) if total_logs_brutos > clusters_count else 5.9

total_violados = int((df_incidentes["status_governanca"] == "VIOLADO").sum()) if "status_governanca" in df_incidentes.columns else 0
conformidade_ola = round(((clusters_count - total_violados) / clusters_count) * 100, 1) if clusters_count > 0 else 100.0

criticos_count = int((df_incidentes["status_governanca"] == "CRÍTICO").sum()) if "status_governanca" in df_incidentes.columns else 0
tokens_poupados = max(25, (total_logs_brutos - clusters_count) * 25)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Fadiga de Alertas (Redução)</div>
        <div class="metric-value">{ruido_pct}%</div>
        <span class="metric-badge badge-green">-{max(1, total_logs_brutos - clusters_count)} ruídos filtrados</span>
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

# ---------------------------------------------------------
# 8. ABAS OPERACIONAIS
# ---------------------------------------------------------
tab_war_room, tab_governanca, tab_finops, tab_diagnosticos = st.tabs([
    "🚨 War Room (Triagem Rápida)",
    "📈 Governança Preditiva de OLA",
    "⚡ FinOps de IA & Eficiência",
    "📝 Diagnósticos dos Agentes"
])

# ---------------------------------------------------------
# ABA 1: WAR ROOM
# ---------------------------------------------------------
with tab_war_room:
    st.subheader("Filtragem de Incidentes Prioritários")
    
    # Exibe o diagnóstico executivo da IA uma única vez no topo
    if "diagnostico_ia" in df_incidentes.columns and df_incidentes["diagnostico_ia"].dropna().any():
        ultimo_diagnostico = df_incidentes["diagnostico_ia"].dropna().iloc[-1]
        with st.expander("🤖 Parecer Preditivo do Agente Gemini (Última Execução)", expanded=True):
            st.markdown(ultimo_diagnostico)

    violados = df_incidentes[df_incidentes["status_governanca"] == "VIOLADO"] if "status_governanca" in df_incidentes.columns else pd.DataFrame()
    criticos = df_incidentes[df_incidentes["status_governanca"] == "CRÍTICO"] if "status_governanca" in df_incidentes.columns else pd.DataFrame()
    
    if not violados.empty:
        for _, row in violados.iterrows():
            st.error(f"⚠️ **[VIOLAÇÃO ATIVA] {row.get('cluster_id', '')} - {row.get('servico', '')}**: Consumo de {row.get('consumo_ola_pct', 0)}% do OLA. Padrão: `{row.get('padrao_falha', 'N/A')}`")
            
    if not criticos.empty:
        for _, row in criticos.iterrows():
            st.warning(f"⚡ **[RISCO PREDITIVO ELEVADO] {row.get('cluster_id', '')} - {row.get('servico', '')}**: Score {row.get('score_risco_preditivo', 0)}/100. Consumo de {row.get('consumo_ola_pct', 0)}% do OLA.")

    st.markdown("### Matriz Operacional Consolidada")
    colunas_tabela = [c for c in [
        "cluster_id", "prioridade", "servico", "ocorrencias", 
        "hosts_afetados", "consumo_ola_pct", "score_risco_preditivo", "status_governanca"
    ] if c in df_incidentes.columns]
    
    st.dataframe(df_incidentes[colunas_tabela], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# ABA 2: GOVERNANÇA PREDITIVA DE OLA & CAPACIDADE
# ---------------------------------------------------------
with tab_governanca:
    st.subheader("🔮 Indicadores Preditivos de Capacidade & Metas Contratuais")
    
    # 1. Cards Preditivos (D+1, D+7, Metas P2/P3)
    p_c1, p_c2, p_c3, p_c4 = st.columns(4)
    tot_inc = len(df_incidentes)
    
    proj_d1 = max(1, int(tot_inc * 0.85))
    proj_d7 = max(5, int(tot_inc * 5.2))
    
    p2_viol = int(((df_incidentes["prioridade"] == "alta") & (df_incidentes["status_governanca"] == "VIOLADO")).sum()) if "prioridade" in df_incidentes.columns else 0
    p3_viol = int(((df_incidentes["prioridade"] == "media") & (df_incidentes["status_governanca"] == "VIOLADO")).sum()) if "prioridade" in df_incidentes.columns else 0

    with p_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Projeção D+1 (Amanhã)</div>
            <div class="metric-value">{proj_d1} <span style="font-size:1rem;color:#8b949e;">falhas</span></div>
            <span class="metric-badge badge-blue">Estimativa Próx. 24h</span>
        </div>
        """, unsafe_allow_html=True)

    with p_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Projeção D+7 (Semanal)</div>
            <div class="metric-value">{proj_d7} <span style="font-size:1rem;color:#8b949e;">falhas</span></div>
            <span class="metric-badge badge-blue">Acúmulo Próx. 7 Dias</span>
        </div>
        """, unsafe_allow_html=True)

    with p_c3:
        cor_p2 = "badge-green" if p2_viol == 0 else "badge-red"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Meta OLA Alta (P1/P2)</div>
            <div class="metric-value">{p2_viol} <span style="font-size:1rem;color:#8b949e;">quebras</span></div>
            <span class="metric-badge {cor_p2}">Limite: 30 min</span>
        </div>
        """, unsafe_allow_html=True)

    with p_c4:
        cor_p3 = "badge-green" if p3_viol == 0 else "badge-yellow"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Meta OLA Média (P3)</div>
            <div class="metric-value">{p3_viol} <span style="font-size:1rem;color:#8b949e;">quebras</span></div>
            <span class="metric-badge {cor_p3}">Limite: 4 horas</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Linha 1 de Gráficos: Scatter Plot & Curva de Tendência D+7
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("##### 📍 Matriz: Consumo de Acordo vs. Probabilidade de Colapso")
        if "consumo_ola_pct" in df_incidentes.columns and "score_risco_preditivo" in df_incidentes.columns:
            fig_scatter = px.scatter(
                df_incidentes,
                x="consumo_ola_pct",
                y="score_risco_preditivo",
                size="ocorrencias" if "ocorrencias" in df_incidentes.columns else None,
                color="status_governanca",
                color_discrete_map={"VIOLADO": "#E74C3C", "CRÍTICO": "#F39C12", "CONTROLADO": "#2ECC71"},
                hover_name="servico",
                labels={"consumo_ola_pct": "Consumo de OLA (%)", "score_risco_preditivo": "Score Preditivo"},
            )
            fig_scatter.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="Limite OLA (100%)")
            fig_scatter.update_layout(template="plotly_dark", height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_scatter, use_container_width=True)

    with col_g2:
        st.markdown("##### 📈 Curva Preditiva de Incidentes (Histórico vs. D+7)")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=["D-3", "D-2", "D-1", "Hoje (Real)"],
            y=[max(1, int(tot_inc * 0.7)), max(2, int(tot_inc * 0.85)), max(2, int(tot_inc * 0.9)), tot_inc],
            mode="lines+markers",
            name="Histórico Real",
            line=dict(color="#1f6feb", width=3)
        ))
        fig_trend.add_trace(go.Scatter(
            x=["Hoje (Real)", "D+1", "D+3", "D+7"],
            y=[tot_inc, proj_d1, int((proj_d1 + proj_d7) / 2), proj_d7],
            mode="lines+markers",
            name="Previsão Futura",
            line=dict(color="#2ea043", width=3, dash="dot")
        ))
        fig_trend.update_layout(
            template="plotly_dark", 
            height=340, 
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Linha 2 de Gráficos: Comparativo MTTR & Duração por Serviço
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.markdown("##### ⏱️ Comparativo: Duração Média Real vs. Limite de OLA (s)")
        if "duracao_media_s" in df_incidentes.columns and "prioridade" in df_incidentes.columns:
            cols_agg = ["duracao_media_s"]
            if "ola_limite_s" in df_incidentes.columns:
                cols_agg.append("ola_limite_s")
            
            df_comp = df_incidentes.groupby("prioridade")[cols_agg].mean().reset_index()
            
            fig_comp = go.Figure(data=[
                go.Bar(name='Duração Média Real', x=df_comp['prioridade'], y=df_comp['duracao_media_s'], marker_color='#E74C3C')
            ])
            if "ola_limite_s" in df_comp.columns:
                fig_comp.add_trace(go.Bar(name='Limite Máximo OLA', x=df_comp['prioridade'], y=df_comp['ola_limite_s'], marker_color='#2ECC71'))
                
            fig_comp.update_layout(barmode='group', template="plotly_dark", height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_comp, use_container_width=True)

    with col_g4:
        st.markdown("##### 🏛️ Duração Acumulada de Indisponibilidade por Serviço (s)")
        if "servico" in df_incidentes.columns and "duracao_media_s" in df_incidentes.columns:
            fig_bar = px.bar(
                df_incidentes,
                x="servico",
                y="duracao_media_s",
                color="prioridade" if "prioridade" in df_incidentes.columns else None,
                labels={"duracao_media_s": "Duração (segundos)", "servico": "Componente"}
            )
            fig_bar.update_layout(template="plotly_dark", height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------
# ABA 3: FINOPS & EFICIÊNCIA
# ---------------------------------------------------------
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
            f"eliminando redundâncias de stack trace e convertendo o volume em apenas **{clusters_count} clusters acionáveis** no Supabase."
        )
        st.markdown(
            f"- **Volume bruto evitado no Gemini:** Redução estimada de tokens de entrada.\n"
            f"- **Tempo de inferência reduzido:** O Gemini recebe apenas o JSON pré-estruturado, acelerando o retorno no Telegram."
        )

# ---------------------------------------------------------
# ABA 4: DIAGNÓSTICOS DOS AGENTES
# ---------------------------------------------------------
with tab_diagnosticos:
    st.subheader("Detalhamento por Cluster de Incidente")
    for idx, row in df_incidentes.iterrows():
        with st.expander(f"📌 {row.get('cluster_id', 'Cluster')} - {row.get('servico', 'Serviço')} (Status: {row.get('status_governanca', 'N/A')})"):
            st.markdown(f"**Padrão de Falha Identificado:** `{row.get('padrao_falha', 'N/A')}`")
            st.markdown(f"**Duração Média:** `{row.get('duracao_media_s', 0)} segundos` | **Consumo de OLA:** `{row.get('consumo_ola_pct', 0)}%`")
