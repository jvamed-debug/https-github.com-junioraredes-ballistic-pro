import streamlit as st
from services.ai_advisor import advisor


def show_ai_advisor_tab(db, selected_caliber, selected_projectile, selected_powder, user_id):
    st.markdown("### CONSULTOR BALISTICO IA")
    st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1)); padding: 15px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); margin-bottom: 20px;'>
            <p style='color: #a78bfa; font-family: "JetBrains Mono", monospace; font-size: 0.7rem; font-weight: 700; margin: 0;'>POWERED BY AI ENGINE</p>
            <p style='color: var(--text-light); font-size: 0.85rem; margin: 5px 0 0 0;'>
                Consultor inteligente para analise de recarga, performance e otimizacao.
                Funciona com ou sem chave de API (modo offline disponivel).
            </p>
        </div>
    """, unsafe_allow_html=True)

    # AI Config
    with st.expander("Configuracao de IA (Opcional)", expanded=not advisor.is_configured):
        cfg_c1, cfg_c2 = st.columns(2)
        provider = cfg_c1.selectbox("Provedor", ["anthropic", "openai"], key="ai_provider")
        api_key = cfg_c2.text_input("API Key", type="password", key="ai_api_key")

        if st.button("Conectar IA", use_container_width=True):
            if api_key:
                ok = advisor.configure(provider, api_key)
                if ok:
                    st.success(f"Conectado ao provedor {provider}.")
                else:
                    st.error("Falha na conexao. Verifique a API key.")
            else:
                st.warning("Informe uma API key para ativar o consultor IA.")

        status = "ONLINE" if advisor.is_configured else "OFFLINE (Analise Basica)"
        color = "#10b981" if advisor.is_configured else "#f59e0b"
        st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 8px; margin-top: 10px;'>
                <div style='width: 8px; height: 8px; background: {color}; border-radius: 50%; box-shadow: 0 0 8px {color};'></div>
                <span style='color: {color}; font-family: "JetBrains Mono", monospace; font-size: 0.7rem; font-weight: 700;'>STATUS: {status}</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Analysis modes
    analysis_mode = st.radio(
        "Tipo de Analise",
        ["Analise de Agrupamento", "Consultoria de Carga", "Tendencia de Performance"],
        horizontal=True,
        key="ai_analysis_mode"
    )

    if analysis_mode == "Analise de Agrupamento":
        _show_grouping_analysis()
    elif analysis_mode == "Consultoria de Carga":
        _show_load_consultation(selected_caliber, selected_projectile, selected_powder)
    else:
        _show_performance_trend(user_id)


def _show_grouping_analysis():
    st.markdown("##### Analise de Agrupamento por IA")

    if "cv_stats" in st.session_state and st.session_state["cv_stats"].get("groups"):
        groups = st.session_state["cv_stats"]["groups"]
        st.info(f"Dados de CV detectados: {len(groups)} grupo(s) da ultima analise de alvo.")

        if st.button("Analisar Agrupamento com IA", use_container_width=True):
            groups_data = []
            for g in groups:
                groups_data.append({
                    "id": g["id"],
                    "group_size_mm": g["group_size_mm"],
                    "shot_count": len(g["shots"]),
                    "poi_mm": {"x": g["poi_mm"][0], "y": g["poi_mm"][1]},
                })

            with st.spinner("Consultando IA..."):
                result = advisor.analyze_grouping(groups_data)

            st.markdown(f"""
                <div style='background: var(--card-bg); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid #8b5cf6;'>
                    <p style='color: #8b5cf6; font-family: "JetBrains Mono", monospace; font-size: 0.65rem; font-weight: 700; margin-bottom: 10px;'>
                        RESPOSTA [{result.provider.upper()}]
                    </p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(result.content)
    else:
        st.warning("Nenhum dado de CV disponivel. Va para a aba **Perf** e analise um alvo primeiro.")


def _show_load_consultation(caliber, projectile, powder):
    st.markdown("##### Consultoria de Carga")

    c1, c2 = st.columns(2)
    charge = c1.number_input("Carga Atual (grains)", min_value=0.0, step=0.1, key="ai_charge")
    velocity = c1.number_input("Velocidade Medida (fps)", min_value=0, step=10, key="ai_vel")
    sd = c2.number_input("Desvio Padrao (fps)", min_value=0.0, step=0.1, key="ai_sd")
    grouping = c2.number_input("Agrupamento (mm)", min_value=0.0, step=1.0, key="ai_group")

    if st.button("Consultar IA sobre Carga", use_container_width=True):
        current_data = {
            "charge": charge,
            "velocity": velocity,
            "sd": sd,
            "grouping": grouping,
        }

        with st.spinner("Analisando carga..."):
            result = advisor.suggest_load(caliber, projectile, powder, current_data)

        st.markdown(f"""
            <div style='background: var(--card-bg); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid #8b5cf6;'>
                <p style='color: #8b5cf6; font-family: "JetBrains Mono", monospace; font-size: 0.65rem; font-weight: 700; margin-bottom: 10px;'>
                    CONSULTORIA [{result.provider.upper()}]
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(result.content)


def _show_performance_trend(user_id):
    st.markdown("##### Analise de Tendencia")

    from core.models import managed_session, ReloadSession

    with managed_session() as db:
        sessions = db.query(ReloadSession).filter_by(user_id=user_id).order_by(
            ReloadSession.date.desc()
        ).limit(20).all()
        sessions_summary = [{
            "data": s.date.strftime("%d/%m/%Y") if s.date else "N/A",
            "calibre": s.caliber,
            "carga_grains": s.charge,
            "velocidade_fps": s.velocity_avg,
            "sd_fps": s.velocity_sd,
            "agrupamento_mm": s.grouping_mm,
            "quantidade": s.quantity,
        } for s in sessions]

    if not sessions_summary:
        st.warning("Nenhuma sessao de recarga registrada. Registre sessoes no Logbook primeiro.")
        return

    st.info(f"Analisando {len(sessions_summary)} sessoes mais recentes.")

    if st.button("Analisar Tendencia com IA", use_container_width=True):
        with st.spinner("Analisando tendencias..."):
            result = advisor.analyze_performance_trend(sessions_summary)

        st.markdown(f"""
            <div style='background: var(--card-bg); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid #8b5cf6;'>
                <p style='color: #8b5cf6; font-family: "JetBrains Mono", monospace; font-size: 0.65rem; font-weight: 700; margin-bottom: 10px;'>
                    TENDENCIA [{result.provider.upper()}]
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(result.content)
