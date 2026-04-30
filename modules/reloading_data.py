import streamlit as st

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
            .safety-strip .msg {
                color: #cbd5e1;
                font-size: 0.7rem;
                margin-top: 4px;
            }
        </style>
        """, unsafe_allow_html=True)

        data_col = st.container()
        with data_col:
            # Helper to format metric values with inches conversion
            import re
            def fmt_dim(val):
                if val == "N/A" or not val:
                    return "—", ""
                v_str = str(val).strip()
                # Try to extract number + mm + optional inches
                # Format: "32.51 mm (1.280\")" or "32.51 mm" or just "32.51"
                mm_match = re.search(r'([\d.]+)\s*mm', v_str)
                inch_match = re.search(r'\(([\d.]+)', v_str)
                
                if mm_match:
                    mm_val = mm_match.group(1)
                    inch_str = f'({inch_match.group(1)}")' if inch_match else ""
                    return f'{mm_val} <span class="unit">mm</span>', inch_str
                else:
                    # No mm found, just return the raw value
                    return str(val), ""

            oal_val, oal_inch = fmt_dim(max_oal)
            case_val, case_inch = fmt_dim(max_case)
            proj_val, proj_inch = fmt_dim(proj_dia)
            base_val, base_inch = fmt_dim(base_dia)

            v_source = caliber_data.get("source", "PADRÃO")
            v_year = caliber_data.get("year", "2024")
            
            st.markdown(f"""
            <div class="schematic-header" style="background: rgba(59, 130, 246, 0.05); padding: 15px; border-radius: 8px 8px 0 0;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="badge" style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px;">ESPECIFICAÇÕES NOMINAIS</span>
                    <span class="caliber-name">{selected_caliber}</span>
                </div>
                <div style="margin-left: auto; display: flex; align-items: center; gap: 10px;">
                    <span style="color: #10b981; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace; font-weight: 800; border: 1px solid #10b98133; background: #10b98111; padding: 4px 10px; border-radius: 6px;">
                        SOURCE: {v_source} {v_year}
                    </span>
                    <span style="height: 8px; width: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></span>
                </div>
            </div>
            <div class="dim-grid">
                <div class="dim-card">
                    <div class="label">OAL MAX (COAL)</div>
                    <div class="value">{oal_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{oal_inch}</div>
                </div>
                <div class="dim-card">
                    <div class="label">CASE MAX (TRIM)</div>
                    <div class="value">{case_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{case_inch}</div>
                </div>
                <div class="dim-card">
                    <div class="label">BULLET DIA</div>
                    <div class="value">{proj_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{proj_inch}</div>
                </div>
                <div class="dim-card">
                    <div class="label">BASE DIA</div>
                    <div class="value">{base_val}</div>
                    <div style="color: #475569; font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;">{base_inch}</div>
                </div>
            </div>
            <div class="safety-strip">
                <div class="tag">⚠ VIGILÂNCIA DE SEGURANÇA</div>
                <div class="msg">Especificações dimensionais nominais. Sempre verifique o TRIM do estojo após os disparos.</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

    if is_manual_mode:
        st.markdown("""
        <div style='background: rgba(245, 158, 11, 0.08); padding: 15px; border-radius: 8px; border: 1px solid var(--warning-base); margin-bottom: 20px;'>
            <span style='color: var(--warning-base); font-family: "JetBrains Mono", monospace; font-weight: 700;'>[⚠️ AVISO: MODO MANUAL ATIVO]</span><br>
            <span style='color: var(--text-light); font-size: 0.85rem;'>Componentes não validados em conjunto pelo banco de dados oficial. Opere com cautela técnica.</span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if selected_caliber == "Outro":
                st.text_input("Calibre", key="man_cal", placeholder="Ex: .308 Win")
            if selected_projectile == "Outro":
                st.text_input("Projétil (grains)", key="man_proj", placeholder="Ex: 150gr Sierra")
            if selected_powder == "Outro":
                st.text_input("Pólvora", key="man_pow", placeholder="Ex: IMR 4064")
        with col2:
            st.number_input("Carga Mín (grains)", key="man_min_val", step=0.1)
            st.number_input("Carga Máx (grains)", key="man_max_val", step=0.1)
    else:
        load_data = db["calibers"][selected_caliber]["projectiles"][selected_projectile]["powders"][selected_powder]
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="background: rgba(16, 185, 129, 0.1); padding: 8px 16px; border-radius: 6px; border: 1px solid #10b981;">
                <span style="color: #10b981; font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 0.7rem;">DADOS OBC TI-44 √</span>
            </div>
            <div style="color: #64748b; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;">REF: {load_data.get('note', 'TI-44')}</div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2); text-align: center;">
                <p style="color: #10b981; font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 700; margin-bottom: 8px;">MIN LOAD</p>
                <p style="color: #f8fafc; font-size: 1.8rem; font-weight: 900; font-family: 'JetBrains Mono', monospace; margin: 0;">{load_data.get('min', 0.0)}<span style="font-size: 0.8rem; color: #64748b; margin-left: 4px;">gr</span></p>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.2); text-align: center;">
                <p style="color: #ef4444; font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 700; margin-bottom: 8px;">MAX LOAD (NEVER EXCEED)</p>
                <p style="color: #f8fafc; font-size: 1.8rem; font-weight: 900; font-family: 'JetBrains Mono', monospace; margin: 0;">{load_data.get('max', 0.0)}<span style="font-size: 0.8rem; color: #64748b; margin-left: 4px;">gr</span></p>
            </div>
            """, unsafe_allow_html=True)
            
        with m3:
            st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2); text-align: center;">
                <p style="color: #3b82f6; font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 700; margin-bottom: 8px;">TARGET VELOCITY</p>
                <p style="color: #f8fafc; font-size: 1.8rem; font-weight: 900; font-family: 'JetBrains Mono', monospace; margin: 0;">{load_data.get('velocity', 'N/A')}<span style="font-size: 0.8rem; color: #64748b; margin-left: 4px;">fps</span></p>
            </div>
            """, unsafe_allow_html=True)
        
        if load_data.get("max", 0) > 0 and load_data.get("min", 0) > 0:
            range_val = load_data["max"] - load_data["min"]
            st.markdown(f"""
            <div style="margin-top: 24px; background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;">ESPECTRO DE TRABALHO</span>
                    <span style="color: #60a5fa; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;">RANGE: {range_val:.1f} gr</span>
                </div>
                <div style="height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; position: relative; overflow: hidden;">
                    <div style="position: absolute; left: 0; top: 0; height: 100%; width: 100%; background: linear-gradient(90deg, #10b981 0%, #f59e0b 50%, #ef4444 100%);"></div>
                </div>
                <p style="color: #64748b; font-size: 0.65rem; margin-top: 10px;"><b>DICA:</b> Comece sempre pela carga mínima (Min Load) e suba em incrementos de 0.1gr observando sinais de pressão no estojo.</p>
            </div>
            """, unsafe_allow_html=True)

def show_calculator(selected_projectile):
    st.markdown("### 🧪 Estimativa de Carga (EXPERIMENTAL)")
    
    # AUDITORIA FUN-001: Alerta Crítico Proeminente
    st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
            <p style="color: #ef4444; font-weight: 900; margin-bottom: 8px; font-size: 1.1rem;">⚠️ AVISO DE RISCO DE VIDA (AUDITORIA FUN-001)</p>
            <p style="color: #cbd5e1; font-size: 0.85rem; line-height: 1.5;">
                Balística interna de armas de fogo envolve picos de pressão <b>NÃO-LINEARES</b>. Estimativas matemáticas 
                simplificadas como esta podem sugerir cargas que resultam em <b>explosões de câmara</b> se usadas sem 
                experiência técnica. 
            </p>
            <ul style="color: #94a3b8; font-size: 0.75rem; margin-top: 10px;">
                <li>NUNCA comece pela carga estimada abaixo.</li>
                <li>Este módulo serve apenas para comparação de energia cinética teórica.</li>
                <li>O desenvolvedor não se responsabiliza por qualquer dano.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        target_vel = st.number_input("Velocidade Alvo (fps)", min_value=500, max_value=4500, value=1000, key="calc_target_vel", help="Velocidade final desejada na boca do cano.")
        proj_w = st.number_input("Peso do Projétil (grains)", min_value=1.0, max_value=1000.0, value=158.0, key="calc_proj_w")
    with c2:
        # Pólvoras variam muito em densidade energética
        calorific = st.number_input("Poder Calorífico da Pólvora (J/g)", min_value=2000, max_value=6000, value=3800, key="calc_calorific", help="Ex: Pólvoras de base simples (~3400) vs base dupla (~4200)")
        efficiency = st.slider("Eficiência Térmica Estimada (%)", 5, 60, 25, key="calc_efficiency", help="Quanto da queima vira movimento. Geralmente entre 20% e 35%.")
    
    # Cálculos Físicos
    m_kg = proj_w * 0.0000647989
    v_ms = target_vel * 0.3048
    energy_j = 0.5 * m_kg * (v_ms ** 2)
    
    # Conversão de Energia -> Gramas -> Grains
    powder_g = energy_j / (calorific * (efficiency / 100))
    est_gr = powder_g * 15.4324

    # Interface de Resultados (HUD)
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.3); text-align: center;">
                <p style="color: #60a5fa; font-size: 0.7rem; font-family: 'JetBrains Mono'; margin: 0;">ENERGIA CINÉTICA</p>
                <p style="color: #f8fafc; font-size: 1.5rem; font-weight: 800; margin: 5px 0;">{energy_j:.1f} <span style="font-size: 0.8rem; color: #64748b;">Joules</span></p>
            </div>
        """, unsafe_allow_html=True)

    with res_col2:
        status_color = "#ef4444" if est_gr > 50 else "#10b981"
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 8px; border: 1px solid {status_color}; text-align: center;">
                <p style="color: {status_color}; font-size: 0.7rem; font-family: 'JetBrains Mono'; margin: 0;">ESTIMATIVA TEÓRICA</p>
                <p style="color: #f8fafc; font-size: 1.5rem; font-weight: 800; margin: 5px 0;">{est_gr:.2f} <span style="font-size: 0.8rem; color: #64748b;">grains</span></p>
            </div>
        """, unsafe_allow_html=True)

    st.warning("⚠️ SEMPRE reduza 10% da carga sugerida para iniciar os testes (Carga de Segurança) e utilize um cronógrafo.")
