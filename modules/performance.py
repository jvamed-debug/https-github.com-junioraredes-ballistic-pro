import streamlit as st
import pandas as pd
from datetime import datetime
from html import escape as html_escape
from core.models import managed_session, User, ReloadSession
from cv_utils import calculate_group_size_v2

def show_performance_tab(user_id):
    # --- Carregar todos os dados do banco ANTES da renderização ---
    with managed_session() as db:
        db_user = db.get(User, user_id)
        if not db_user:
            st.error("Usuário não encontrado.")
            return
        user_info = {
            "id": db_user.id,
            "name": getattr(db_user, "name", ""),
            "email": getattr(db_user, "email", ""),
        }
        sessions_raw = db.query(ReloadSession).filter_by(user_id=user_id).order_by(ReloadSession.date.desc()).limit(100).all()
        sessions_raw.reverse() # For chronological plotting
        sessions_data = [{
            "Data": s.date.strftime('%d/%m/%Y'),
            "Agrupamento (mm)": s.grouping_mm,
            "Velocidade (fps)": s.velocity_avg,
            "SD": s.velocity_sd,
        } for s in sessions_raw]
    # Sessão fechada com segurança aqui ↑

    st.markdown("### 📊 DASHBOARD DE PERFORMANCE OPERACIONAL")
    operator_name = html_escape(str(user_info.get("name") or "—")).upper()
    st.markdown(f"""
        <div style='background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); padding: 2px; border-radius: 12px; margin-bottom: 25px;'>
            <div style='background: #0f172a; padding: 20px; border-radius: 10px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <p style='color: #3b82f6; font-family: "JetBrains Mono", monospace; font-size: 0.7rem; font-weight: 700; margin: 0;'>SISTEMA DE ANÁLISE BALÍSTICA v2.5</p>
                        <h2 style='color: white; margin: 5px 0 0 0; font-size: 1.5rem;'>Status de Tiro: <span style='color: #10b981;'>ESTÁVEL</span></h2>
                    </div>
                    <div style='text-align: right;'>
                        <p style='color: #94a3b8; font-family: "JetBrains Mono", monospace; font-size: 0.6rem; margin: 0;'>OPERADOR</p>
                        <p style='color: #f1f5f9; font-weight: 600; margin: 0;'>{operator_name}</p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. Historical Trends
    if sessions_data:
        df = pd.DataFrame(sessions_data)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.caption("📈 TENDÊNCIA DE AGRUPAMENTO (MOA/mm)")
            st.line_chart(df.set_index("Data")["Agrupamento (mm)"], color="#3b82f6")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.caption("📉 CONSISTÊNCIA BALÍSTICA (SD/Velocidade)")
            st.bar_chart(df.set_index("Data")["SD"], color="#334155")
            st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

    # 2. Advanced CV Analysis
    st.markdown("#### 🔘 SCANNER DE ALVO & BALÍSTICA COMPUTACIONAL")
    st.markdown("""
        <div style='background: var(--card-bg); padding: 15px; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 20px; border-left: 5px solid var(--accent-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <p style='color: var(--text-light); font-size: 0.8rem; margin: 0;'>
                <b style='color: var(--accent-primary);'>ANÁLISE AVANÇADA:</b> Calibração via visão computacional (OpenCV).
                Detecção de POI e agrupamento submétrico.
            </p>
        </div>
    """, unsafe_allow_html=True)

    target_img = st.file_uploader("Enviar Foto do Alvo", type=["jpg", "png", "jpeg"], key="perf_target_img")

    if target_img:
        col_ui1, col_ui2 = st.columns([1, 2])

        with col_ui1:
            st.markdown("##### ⚙️ Ajustes de Análise")
            cv_sens = st.slider("Sensibilidade (Contraste)", 0, 255, 155)
            cv_min_area = st.number_input("Tamanho Mínimo (px)", value=50)

            calib_mode = st.radio("Referência de Escala", ["Largura Manual (mm)", "Moeda (Auto-Calibrar)"])
            ref_width = 210.0
            if calib_mode == "Largura Manual (mm)":
                ref_width = st.number_input("Largura Alvo (mm)", value=210.0)

            st.markdown("---")
            use_poi = st.toggle("Calcular POI (Ponto de Impacto)", value=False)
            center_x, center_y = 0, 0
            if use_poi:
                st.caption("Informe o centro do alvo (pixels na imagem original):")
                pc1, pc2 = st.columns(2)
                center_x = pc1.number_input("X Centro", value=0)
                center_y = pc2.number_input("Y Centro", value=0)

        if st.button("🚀 Executar Análise Inteligente", use_container_width=True):
            with st.spinner("Inteligência computacional em curso..."):
                results = calculate_group_size_v2(
                    target_img,
                    target_width_mm=ref_width,
                    sensitivity=cv_sens,
                    min_area_px=cv_min_area,
                    center_point=(center_x, center_y) if use_poi else None,
                    use_auto_calib=(calib_mode == "Moeda (Auto-Calibrar)")
                )
                st.session_state["cv_stats"] = results
                st.success(f"Análise concluída: {results['shot_count']} impactos encontrados em {len(results['groups'])} grupos.")

        if "cv_stats" in st.session_state:
            res = st.session_state["cv_stats"]

            st.image(res["annotated_image"], caption="Alvo Processado (Verificado)", use_container_width=True)

            for group in res["groups"]:
                with st.expander(f"📌 Grupo {group['id']} - Detalhes", expanded=True):
                    gc1, gc2, gc3 = st.columns(3)
                    gc1.metric("Agrupamento", f"{group['group_size_mm']:.2f} mm")
                    gc2.metric("Impactos", len(group["shots"]))

                    if use_poi:
                        px, py = group["poi_mm"]
                        gc3.metric("Desvio (POI)", f"X:{px:+.1f} Y:{py:+.1f} mm")

                    if st.button(f"Salvar Grupo {group['id']} no Histórico", key=f"save_g_{group['id']}"):
                        # FUN-003: Persiste agrupamento na sessão mais recente do usuário
                        best_group_mm = group["group_size_mm"]
                        saved_session_id = None

                        with managed_session() as db_save:
                            # Busca sessão mais recente — sem filtro de calibre para maior compatibilidade
                            last_sess = db_save.query(ReloadSession).filter_by(user_id=user_id).order_by(
                                ReloadSession.date.desc()
                            ).first()
                            if last_sess:
                                last_sess.grouping_mm = round(best_group_mm, 2)
                                saved_session_id = last_sess.id
                        
                        if saved_session_id:
                            st.toast(f"✅ Agrupamento {best_group_mm:.2f}mm salvo na sessão #{saved_session_id}!", icon="💾")
                        else:
                            st.warning("Nenhuma sessão de recarga encontrada. Registre uma sessão no Logbook primeiro.")

            st.divider()
            from report_gen import create_performance_report_v2

            st.markdown("##### 📄 Exportar Relatório Técnico")
            st.caption("Gere um documento PDF profissional com a foto do alvo e as métricas detectadas.")

            # user_info é um dict simples — não requer sessão aberta
            perf_report_pdf = create_performance_report_v2(user_info, res, res['annotated_image'])
            st.download_button(
                label="🖨️ Baixar Laudo de Performance",
                data=perf_report_pdf,
                file_name=f"laudo_performance_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

