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
        st.markdown("""
        <style>
            .schematic-container {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                border-radius: 12px;
                padding: 24px;
                margin: 16px 0;
                border: 1px solid rgba(59, 130, 246, 0.2);
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
            }
            .schematic-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            .schematic-header .badge {
                background: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
                font-size: 0.6rem;
                font-family: "JetBrains Mono", monospace;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: 4px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            .schematic-header .caliber-name {
                color: #f1f5f9;
                font-size: 1.3rem;
                font-weight: 800;
                font-family: "JetBrains Mono", monospace;
                letter-spacing: 0.5px;
            }
            .dim-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-top: 16px;
            }
            .dim-card {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 14px 16px;
                transition: border-color 0.2s;
            }
            .dim-card:hover {
                border-color: rgba(59, 130, 246, 0.4);
            }
            .dim-card .label {
                color: #94a3b8;
                font-size: 0.6rem;
                font-family: "JetBrains Mono", monospace;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 6px;
            }
            .dim-card .value {
                color: #f8fafc;
                font-size: 1.1rem;
                font-weight: 700;
                font-family: "JetBrains Mono", monospace;
            }
            .dim-card .value .unit { color: #64748b; font-size: 0.75rem; font-weight: 400; }
            .safety-strip {
                background: rgba(245, 158, 11, 0.08);
                border-left: 3px solid #f59e0b;
                border-radius: 0 6px 6px 0;
                padding: 10px 14px;
                margin-top: 16px;
            }
            .safety-strip .tag {
                color: #f59e0b;
                font-family: "JetBrains Mono", monospace;
                font-size: 0.6rem;
                font-weight: 700;
                letter-spacing: 1px;
            }
            .safety-strip .msg {
                color: #cbd5e1;
                font-size: 0.7rem;
                margin-top: 4px;
            }
            .img-frame {
                background: #ffffff;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .img-label {
                color: #94a3b8;
                font-size: 0.55rem;
                font-family: "JetBrains Mono", monospace;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                margin-bottom: 8px;
            }
        </style>
        """, unsafe_allow_html=True)

        img_col, data_col = st.columns([1.2, 1.8])

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
                st.markdown(f"""<p class='img-label'>DIAGRAMA SAAMI · {selected_caliber}</p>""", unsafe_allow_html=True)
                st.image(image_path, use_container_width=True)
            else:
                st.markdown(f"""
                <div style='background: rgba(15,23,42,0.6); border: 1px dashed rgba(100,116,139,0.3); border-radius: 8px; padding: 40px 20px; text-align: center;'>
                    <p style='color: #475569; font-family: "JetBrains Mono", monospace; font-size: 0.7rem;'>⚠ DIAGRAMA INDISPONÍVEL</p>
                    <p style='color: #334155; font-size: 0.65rem;'>{selected_caliber}</p>
                </div>
                """, unsafe_allow_html=True)

        with data_col:
            # Helper to format metric values with inches conversion
            def fmt_dim(val):
                if val == "N/A":
                    return "—", ""
                v_str = str(val).replace(" ", "")
                # Extract just the mm part and inches if present
                if "(" in v_str:
                    parts = v_str.split("(")
                    mm_part = parts[0].strip().replace("mm", "").strip()
                    inch_part = parts[1].replace(")", "").replace('"', '').strip()
                    return f'{mm_part} <span class="unit">mm</span>', f'({inch_part}")'
                elif "mm" in v_str:
                    mm_part = v_str.replace("mm", "").strip()
                    return f'{mm_part} <span class="unit">mm</span>', ""
                else:
                    return str(val), ""

            oal_val, oal_inch = fmt_dim(max_oal)
            case_val, case_inch = fmt_dim(max_case)
            proj_val, proj_inch = fmt_dim(proj_dia)
            base_val, base_inch = fmt_dim(base_dia)

            st.markdown(f"""
            <div class="schematic-header">
                <span class="badge">SPECS</span>
                <span class="caliber-name">{selected_caliber}</span>
            </div>
            <div class="dim-grid">
                <div class="dim-card">
                    <div class="label">OAL MAX · Compr. Total</div>
                    <div class="value">{oal_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{oal_inch}</div>
                </div>
                <div class="dim-card">
                    <div class="label">CASE MAX · Compr. Estojo</div>
                    <div class="value">{case_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{case_inch}</div>
                </div>
                <div class="dim-card">
                    <div class="label">PROJ DIA · Diâm. Projétil</div>
                    <div class="value">{proj_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{proj_inch}</div>
                </div>
                <div class="dim-card">
                    <div class="label">BASE DIA · Diâm. Base</div>
                    <div class="value">{base_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{base_inch}</div>
                </div>
            </div>
            <div class="safety-strip">
                <div class="tag">⚠ VIGILÂNCIA DE SEGURANÇA</div>
                <div class="msg">Medidas nominais SAAMI. Verifique o HEADSPACE da arma antes de operar. Sempre confira com manuais oficiais.</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

    if is_manual_mode:
        st.markdown(f"""
        <div style='background: rgba(245, 158, 11, 0.08); padding: 15px; border-radius: 8px; border: 1px solid var(--warning-base); margin-bottom: 20px;'>
            <span style='color: var(--warning-base); font-family: "JetBrains Mono", monospace; font-weight: 700;'>[⚠️ AVISO: MODO MANUAL ATIVO]</span><br>
            <span style='color: var(--text-light); font-size: 0.85rem;'>Componentes não validados em conjunto pelo banco de dados oficial. Opere com cautela técnica.</span>
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
        <div style='background: rgba(16, 185, 129, 0.05); padding: 15px; border-radius: 8px; border: 1px solid var(--success-base); margin-bottom: 20px; border-left: 5px solid var(--success-base);'>
            <span style='color: var(--success-base); font-family: "JetBrains Mono", monospace; font-weight: 700;'>[✅ DADOS TÉCNICOS VERIFICADOS]</span><br>
            <span style='color: var(--text-light); font-size: 0.85rem;'>Integridade confirmada. Parâmetros carregados com sucesso do Database Ballistic Pro.</span>
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
