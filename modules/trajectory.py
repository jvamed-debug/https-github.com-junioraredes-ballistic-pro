import streamlit as st
import pandas as pd
from services.trajectory_service import (
    calculate_trajectory,
    ProjectileData,
    AtmosphericConditions,
)


def show_trajectory_tab(db, selected_caliber, selected_projectile):
    st.markdown("### CALCULADORA DE TRAJETORIA EXTERNA")
    st.markdown("""
        <div style='background: var(--card-bg); padding: 15px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid #3b82f6; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <p style='color: var(--text-light); font-size: 0.8rem; margin: 0;'>
                <b style='color: #3b82f6;'>MODELO BALISTICO:</b> Simulacao de arrasto atmosferico com compensacao de altitude, temperatura e vento.
                Calcule queda, desvio, energia e tempo de voo ate a distancia desejada.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_proj, col_atm = st.columns(2)

    with col_proj:
        st.markdown("##### Dados do Projetil")
        proj_weight = st.number_input(
            "Peso (grains)", min_value=10.0, max_value=1000.0, value=147.0, step=1.0, key="traj_weight"
        )
        proj_bc = st.number_input(
            "Coeficiente Balistico (G1)", min_value=0.050, max_value=1.000, value=0.400, step=0.001,
            format="%.3f", key="traj_bc",
            help="Valor G1 do fabricante. Quanto maior, menor o arrasto."
        )
        proj_vel = st.number_input(
            "Velocidade Inicial (fps)", min_value=500, max_value=5000, value=2800, step=10, key="traj_vel"
        )
        proj_dia = st.number_input(
            "Diametro (mm)", min_value=4.0, max_value=20.0, value=7.62, step=0.01,
            format="%.2f", key="traj_dia",
            help="Registro apenas. O diametro nao entra no calculo: o "
                 "coeficiente balistico ja o carrega, pela densidade seccional."
        )

        caliber_data = db["calibers"].get(selected_caliber, {})
        if caliber_data and selected_caliber != "Outro":
            projs = caliber_data.get("projectiles", {})
            if selected_projectile in projs:
                proj_info = projs[selected_projectile]
                powders = proj_info.get("powders", {})
                if powders:
                    first_powder = list(powders.values())[0]
                    vel_str = str(first_powder.get("velocity", ""))
                    vel_num = "".join(c for c in vel_str if c.isdigit())
                    if vel_num:
                        st.caption(f"Velocidade de referencia do banco: {vel_num} fps")

    with col_atm:
        st.markdown("##### Condicoes Atmosfericas")
        atm_temp = st.number_input(
            "Temperatura (C)", min_value=-30.0, max_value=60.0, value=25.0, step=1.0, key="traj_temp"
        )
        atm_alt = st.number_input(
            "Altitude (m)", min_value=0, max_value=5000, value=800, step=50, key="traj_alt",
            help="Altitude acima do nivel do mar. Brasilia ~1100m, Sao Paulo ~760m"
        )
        atm_press = st.number_input(
            "Pressao ao nivel do mar (hPa)", min_value=800.0, max_value=1100.0,
            value=1013.25, step=1.0, key="traj_press",
            help="Pressao reduzida ao nivel do mar (QNH) — o valor que apps de "
                 "meteorologia mostram. A queda ate a sua altitude ja entra pelo "
                 "campo Altitude; nao use aqui a pressao medida no local."
        )
        atm_humid = st.number_input(
            "Umidade (%)", min_value=0, max_value=100, value=60, step=5, key="traj_humid",
            help="Ar umido e menos denso e freia menos o projetil. O efeito e de "
                 "cerca de 1% em dia quente e saturado."
        )

    st.divider()

    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        zero_range = st.number_input(
            "Zero da Mira (m)", min_value=25, max_value=1000, value=100, step=25, key="traj_zero"
        )
    with col_cfg2:
        max_range = st.number_input(
            "Distancia Maxima (m)", min_value=100, max_value=2000, value=500, step=50, key="traj_max"
        )
    with col_cfg3:
        sight_height = st.number_input(
            "Altura da Optica (cm)", min_value=1.0, max_value=15.0, value=4.5, step=0.5, key="traj_sight"
        )

    col_wind1, col_wind2 = st.columns(2)
    with col_wind1:
        wind_speed_kmh = st.number_input(
            "Vento (km/h)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key="traj_wind"
        )
    with col_wind2:
        wind_angle = st.selectbox(
            "Direcao do Vento",
            options=[("90 - Lateral (Full Value)", 90), ("45 - Obliquo", 45), ("0 - De frente/tras", 0)],
            format_func=lambda x: x[0],
            key="traj_wind_dir"
        )

    if st.button("CALCULAR TRAJETORIA", use_container_width=True, type="primary"):
        projectile = ProjectileData(
            weight_grains=proj_weight,
            bc_g1=proj_bc,
            diameter_mm=proj_dia,
            muzzle_velocity_fps=proj_vel,
        )
        atmosphere = AtmosphericConditions(
            temperature_c=atm_temp,
            pressure_hpa=atm_press,
            humidity_pct=atm_humid,
            altitude_m=float(atm_alt),
        )

        wind_ms = wind_speed_kmh / 3.6
        wind_ang = wind_angle[1] if isinstance(wind_angle, tuple) else 90

        with st.spinner("Calculando trajetoria..."):
            result = calculate_trajectory(
                projectile=projectile,
                zero_range_m=float(zero_range),
                max_range_m=float(max_range),
                step_m=25.0,
                sight_height_cm=sight_height,
                wind_speed_ms=wind_ms,
                wind_angle_deg=wind_ang,
                atmosphere=atmosphere,
            )

        if not result.points:
            st.error("Erro no calculo. Verifique os parametros.")
            return

        st.session_state["traj_result"] = result

    if "traj_result" in st.session_state:
        result = st.session_state["traj_result"]

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        summary = result.summary
        m1.metric("Vel. Boca", f"{summary.get('muzzle_velocity_fps', 0):.0f} fps")
        m2.metric("Energia Boca", f"{summary.get('muzzle_energy_ftlbs', 0):.0f} ft-lbs")
        m3.metric("Zero", f"{result.zero_range_m:.0f} m")
        m4.metric("MPBR", f"{result.max_point_blank_range_m:.0f} m")

        # Data table
        table_data = []
        for p in result.points:
            row = {
                "Dist (m)": int(p.range_m),
                "Queda (cm)": p.drop_cm,
                "MOA": p.drop_moa,
                "MIL": p.drop_mil,
                "Vel (fps)": int(p.velocity_fps),
                "Energia (ft-lbs)": int(p.energy_ftlbs),
                "ToF (s)": p.time_of_flight_s,
            }
            if wind_speed_kmh > 0:
                row["Drift (cm)"] = p.wind_drift_cm
                row["Drift MOA"] = p.wind_drift_moa
            table_data.append(row)

        df = pd.DataFrame(table_data)

        st.markdown("##### Tabela Balistica")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Charts
        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.caption("QUEDA (DROP) vs DISTANCIA")
            chart_df = pd.DataFrame({
                "Distancia (m)": [int(p.range_m) for p in result.points],
                "Queda (cm)": [p.drop_cm for p in result.points],
            })
            st.line_chart(chart_df.set_index("Distancia (m)"), color="#ef4444")
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_c2:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.caption("VELOCIDADE REMANESCENTE")
            vel_df = pd.DataFrame({
                "Distancia (m)": [int(p.range_m) for p in result.points],
                "Velocidade (fps)": [p.velocity_fps for p in result.points],
            })
            st.line_chart(vel_df.set_index("Distancia (m)"), color="#3b82f6")
            st.markdown('</div>', unsafe_allow_html=True)

        energy_c1, energy_c2 = st.columns(2)
        with energy_c1:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.caption("ENERGIA REMANESCENTE")
            en_df = pd.DataFrame({
                "Distancia (m)": [int(p.range_m) for p in result.points],
                "Energia (ft-lbs)": [p.energy_ftlbs for p in result.points],
            })
            st.line_chart(en_df.set_index("Distancia (m)"), color="#10b981")
            st.markdown('</div>', unsafe_allow_html=True)

        if wind_speed_kmh > 0:
            with energy_c2:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.caption("DESVIO POR VENTO (WIND DRIFT)")
                wd_df = pd.DataFrame({
                    "Distancia (m)": [int(p.range_m) for p in result.points],
                    "Drift (cm)": [p.wind_drift_cm for p in result.points],
                })
                st.line_chart(wd_df.set_index("Distancia (m)"), color="#f59e0b")
                st.markdown('</div>', unsafe_allow_html=True)

        # CSV export
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="EXPORTAR TABELA (CSV)",
            data=csv_data,
            file_name="tabela_balistica.csv",
            mime="text/csv",
            use_container_width=True,
        )
