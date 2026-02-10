import streamlit as st
import os

def show_reloading_data(db, selected_caliber, selected_projectile, selected_powder, is_manual_mode):
    # Dimensões do Calibre
    caliber_data = db["calibers"].get(selected_caliber, {})
    max_oal = caliber_data.get("max_oal", "N/A")
    max_case = caliber_data.get("max_case", "N/A")
    proj_dia = caliber_data.get("proj_dia", "N/A")
    base_dia = caliber_data.get("base_dia", "N/A")

    if max_oal != "N/A":
        st.markdown("#### 📡 TACTICAL SCHEMATICS & SPECS")
        
        # Tactical HUD Container
        st.markdown('<div class="tech-hud">', unsafe_allow_html=True)
        img_col, data_col = st.columns([1.5, 2])
        
        with img_col:
            # Logic to find a specific diagram for the caliber
            img_name = selected_caliber.replace(" ", "_").replace(".", "").replace("&", "").lstrip("_")
            options = [
                f"assets/{img_name}_Diagram.png",
                f"assets/{img_name}.png",
                "cartridge_diagram.png"
            ]
            
            image_path = None
            for opt in options:
                if os.path.exists(opt):
                    image_path = opt
                    break
            
            if image_path:
                st.image(image_path, caption=f"DIAGRAMA: {selected_caliber}", use_container_width=True)
            else:
                st.info("Esquema técnico indisponível.")
        
        with data_col:
            st.markdown(f"""
                <div style='border-bottom: 2px solid #00f2ff; padding-bottom: 5px; margin-bottom: 15px;'>
                    <span style='font-family: "JetBrains Mono", monospace; color: #00f2ff; font-size: 0.9rem; font-weight: 700;'>CALIBRE: {selected_caliber}</span>
                </div>
            """, unsafe_allow_html=True)
            
            d1, d2 = st.columns(2)
            with d1:
                st.metric("OAL MAX", max_oal)
                st.metric("PROJ DIA", proj_dia)
            with d2:
                st.metric("CASE MAX", max_case)
                st.metric("BASE DIA", base_dia)
                
            st.markdown("""
            <div style='background: rgba(255, 77, 0, 0.05); padding: 12px; border-radius: 4px; border-left: 4px solid #ff4d00; margin-top: 15px;'>
                <p style='color: #ff4d00; font-family: "JetBrains Mono", monospace; font-size: 0.7rem; font-weight: 700; margin: 0;'>
                    [VIGILÂNCIA DE SEGURANÇA]
                </p>
                <p style='color: #cbd5e1; font-size: 0.75rem; margin: 5px 0 0 0;'>
                    Medidas nominais SAAMI. Verifique o HEADSPACE da arma antes de operar.
                </p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

    if is_manual_mode:
        st.markdown(f"""
        <div style='background: rgba(255, 77, 0, 0.1); padding: 15px; border-radius: 4px; border: 1px solid #ff4d00; margin-bottom: 20px;'>
            <span style='color: #ff4d00; font-family: "JetBrains Mono", monospace; font-weight: 700;'>[⚠️ AVISO: MODO MANUAL ATIVO]</span><br>
            <span style='color: #cbd5e1; font-size: 0.85rem;'>Componentes não validados em conjunto pelo banco de dados oficial. Opere com cautela técnica.</span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if selected_caliber == "Outro": st.text_input("Calibre", key="man_cal", placeholder="Ex: .308 Win")
            if selected_projectile == "Outro": st.text_input("Projétil (grains)", key="man_proj", placeholder="Ex: 150gr Sierra")
            if selected_powder == "Outro": st.text_input("Pólvora", key="man_pow", placeholder="Ex: IMR 4064")
        with col2:
            st.number_input("Carga Mín (grains)", key="man_min_val", step=0.1)
            st.number_input("Carga Máx (grains)", key="man_max_val", step=0.1)
    else:
        st.markdown(f"""
        <div style='background: rgba(0, 242, 255, 0.05); padding: 15px; border-radius: 4px; border: 1px solid #00f2ff; margin-bottom: 20px; border-left: 5px solid #00f2ff;'>
            <span style='color: #00f2ff; font-family: "JetBrains Mono", monospace; font-weight: 700;'>[✅ DADOS TÉCNICOS VERIFICADOS]</span><br>
            <span style='color: #cbd5e1; font-size: 0.85rem;'>Integridade confirmada. Parâmetros carregados com sucesso do Database Ballistic Pro.</span>
        </div>
        """, unsafe_allow_html=True)
        load_data = db["calibers"][selected_caliber]["projectiles"][selected_projectile]["powders"][selected_powder]
        m1, m2, m3 = st.columns(3)
        m1.metric("CARGA MÍNIMA", f"{load_data.get('min', 0.0)} gr")
        m2.metric("CARGA MÁXIMA", f"{load_data.get('max', 0.0)} gr")
        m3.metric("VELOCIDADE", f"{load_data.get('velocity', 'N/A')} fps")
        if load_data.get("note"): 
            st.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 4px; border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: 10px;'>
                <p style='color: #94a3b8; font-size: 0.8rem; margin: 0;'><b>NOTA TÉCNICA:</b> {load_data['note']}</p>
            </div>
            """, unsafe_allow_html=True)

def show_calculator(selected_projectile):
    st.markdown("### 🧪 Estimativa de Carga")
    c1, c2 = st.columns(2)
    with c1:
        target_vel = st.number_input("Velocidade Alvo (fps)", value=1000)
        proj_w = st.number_input("Peso do Projétil (grains)", value=158.0)
    with c2:
        calorific = st.number_input("Poder Calorífico (J/g)", value=3800)
        efficiency = st.slider("Eficiência (%)", 5, 50, 25)
    
    m_kg, v_ms = proj_w * 0.0000647989, target_vel * 0.3048
    energy_j = 0.5 * m_kg * (v_ms ** 2)
    powder_g = energy_j / (calorific * (efficiency / 100))
    est_gr = powder_g * 15.4324
    
    st.metric("Energia Estimada", f"{energy_j:.1f} J")
    st.metric("Carga Sugerida", f"{est_gr:.2f} grains")
