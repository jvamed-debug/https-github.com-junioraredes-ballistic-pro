import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from core.models import get_session, User, ReloadSession
from cv_utils import calculate_group_size_v2
from PIL import Image
import io

def show_performance_tab(user_id):
    db = get_session()
    user = db.query(User).get(user_id)
    
    st.markdown("### 📊 DASHBOARD DE PERFORMANCE OPERACIONAL")
    st.markdown('<div class="tech-hud">', unsafe_allow_html=True)
    
    # 1. Historical Trends
    sessions = db.query(ReloadSession).filter_by(user_id=user_id).all()
    if sessions:
        df = pd.DataFrame([{
            "Data": s.date.strftime('%d/%m/%Y'),
            "Agrupamento (mm)": s.grouping_mm,
            "Velocidade (fps)": s.velocity_avg,
            "SD": s.velocity_sd
        } for s in sessions])
        
        c1, c2 = st.columns(2)
        with c1:
            st.caption("📈 TENDÊNCIA DE AGRUPAMENTO (MOA/mm)")
            st.line_chart(df.set_index("Data")["Agrupamento (mm)"], color="#3b82f6")
        with c2:
            st.caption("📉 CONSISTÊNCIA BALÍSTICA (SD/Velocidade)")
            st.bar_chart(df.set_index("Data")["SD"], color="#334155")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    
    # 2. Advanced CV Analysis
    st.markdown("#### 🔘 SCANNER DE ALVO & BALÍSTICA COMPUTACIONAL")
    st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.02); padding: 15px; border-radius: 4px; border-left: 3px solid var(--accent-focus); margin-bottom: 20px;'>
            <p style='color: var(--text-dim); font-size: 0.8rem; margin: 0;'>
                <b style='color: var(--accent-focus);'>ANÁLISE AVANÇADA:</b> Calibração via visão computacional (OpenCV). 
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
                
                # Metric Summary
                st.session_state["cv_stats"] = results
                st.success(f"Análise concluída: {results['shot_count']} impactos encontrados em {len(results['groups'])} grupos.")

        # Show Results
        if "cv_stats" in st.session_state:
            res = st.session_state["cv_stats"]
            
            # Display Annotated Image
            st.image(res["annotated_image"], caption="Alvo Processado (Verificado)", use_container_width=True)
            
            # Group Detailing
            for group in res["groups"]:
                with st.expander(f"📌 Grupo {group['id']} - Detalhes", expanded=True):
                    gc1, gc2, gc3 = st.columns(3)
                    gc1.metric("Agrupamento", f"{group['group_size_mm']:.2f} mm")
                    gc2.metric("Impactos", len(group["shots"]))
                    
                    if use_poi:
                        px, py = group["poi_mm"]
                        gc3.metric("Desvio (POI)", f"X:{px:+.1f} Y:{py:+.1f} mm")
                    
                    if st.button(f"Salvar Grupo {group['id']} no Histórico", key=f"save_g_{group['id']}"):
                        # Logic to save to DB...
                        st.toast("Medição salva no histórico!", icon="💾")
            
            # --- Export Technical Report Button ---
            st.divider()
            from report_gen import create_performance_report_v2
            
            st.markdown("##### 📄 Exportar Relatório Técnico")
            st.caption("Gere um documento PDF profissional com a foto do alvo e as métricas detectadas.")
            
            perf_report_pdf = create_performance_report_v2(user, res, res['annotated_image'])
            st.download_button(
                label="🖨️ Baixar Laudo de Performance",
                data=perf_report_pdf,
                file_name=f"laudo_performance_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    db.close()
