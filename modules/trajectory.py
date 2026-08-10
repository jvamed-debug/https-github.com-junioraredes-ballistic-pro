import streamlit as st
import pandas as pd
from html import escape as html_escape
from services.trajectory_service import (
    calculate_trajectory,
    build_dope_card,
    ProjectileData,
    AtmosphericConditions,
)


#  Valores de clique de torre mais comuns, por unidade. O texto e o rotulo; o
#  numero e o valor de um clique na propria unidade (0.1 mil, 0.25 MOA, ...).
_CLICK_OPTIONS = {
    "MIL": [("0.1 mil (padrao)", 0.1), ("0.05 mil", 0.05)],
    "MOA": [("1/4 MOA (padrao)", 0.25), ("1/8 MOA", 0.125), ("1/2 MOA", 0.5)],
}


def _render_dope_card_html(entries, unit, click_label, incline_deg, header):
    """Monta um cartao de DOPE imprimivel (HTML) para plastificar e levar ao
    campo. So texto/tabela, sem dependencia externa."""
    rows = []
    for e in entries:
        wind = "—" if e.windage_dir == "-" else f"{e.windage:.1f} {e.windage_dir}"
        rows.append(
            f"<tr><td>{int(e.range_m)}</td>"
            f"<td class='up'>{e.elevation:.1f}<span>{e.elevation_clicks} clk</span></td>"
            f"<td class='wd'>{wind}<span>{e.windage_clicks} clk</span></td>"
            f"<td>{int(e.velocity_fps)}</td><td>{int(e.energy_ftlbs)}</td>"
            f"<td>{e.time_of_flight_s:.2f}</td></tr>"
        )
    incline_txt = f" · Angulo {incline_deg:+.0f}°" if incline_deg else ""
    return f"""<!doctype html><html lang='pt-br'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Cartao de DOPE</title><style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; margin: 0;
    background: #0f172a; color: #e2e8f0; padding: 16px; }}
  .card {{ max-width: 520px; margin: 0 auto; background: #1e293b;
    border: 1px solid #334155; border-radius: 12px; overflow: hidden; }}
  header {{ padding: 14px 16px; background: #111827; border-bottom: 2px solid #f59e0b; }}
  header h1 {{ margin: 0; font-size: 1rem; letter-spacing: .04em; text-transform: uppercase; }}
  header p {{ margin: 4px 0 0; font-size: .72rem; color: #94a3b8; }}
  table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }}
  th, td {{ padding: 8px 6px; text-align: center; font-size: .82rem;
    border-bottom: 1px solid #334155; }}
  th {{ font-size: .62rem; text-transform: uppercase; letter-spacing: .05em;
    color: #94a3b8; background: #0f172a; }}
  td span {{ display: block; font-size: .6rem; color: #64748b; }}
  td.up {{ color: #fca5a5; font-weight: 700; }}
  td.wd {{ color: #fcd34d; font-weight: 700; }}
  td:first-child {{ font-weight: 700; color: #fff; }}
  @media print {{ body {{ background: #fff; color: #000; }}
    .card {{ border-color: #000; }} th {{ background: #eee; color: #000; }} }}
</style></head><body><div class='card'>
<header><h1>Cartao de DOPE</h1><p>{html_escape(header)} · Torre {html_escape(click_label)}{incline_txt}</p></header>
<table><thead><tr><th>Dist (m)</th><th>Elev ({unit})</th><th>Vento ({unit})</th>
<th>Vel (fps)</th><th>En (ft·lb)</th><th>ToF (s)</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></body></html>"""


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

    if st.button("CALCULAR TRAJETORIA", width='stretch', type="primary"):
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
        st.dataframe(df, width='stretch', hide_index=True)

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
            width='stretch',
        )

        st.divider()
        _show_dope_card(result, selected_caliber, selected_projectile)


def _show_dope_card(result, selected_caliber, selected_projectile):
    """Cartao de DOPE: a trajetoria ja calculada, traduzida para o que se dial
    na torre da luneta em cliques, com opcao de compensacao de angulo."""
    st.markdown("### 🎯 Cartao de DOPE (Correcao de Torre)")
    st.caption(
        "A correcao de elevacao (come-up) e de vento que voce dial na luneta "
        "para acertar em cada distancia, ja convertida em cliques da torre."
    )

    d1, d2, d3 = st.columns(3)
    with d1:
        dope_unit = st.radio(
            "Unidade da torre", ["MIL", "MOA"], horizontal=True, key="dope_unit"
        )
    with d2:
        click_opts = _CLICK_OPTIONS[dope_unit]
        click_choice = st.selectbox(
            "Valor do clique", options=click_opts,
            format_func=lambda x: x[0], key=f"dope_click_{dope_unit}",
        )
        click_value = click_choice[1]
        click_label = click_choice[0]
    with d3:
        incline_deg = st.slider(
            "Angulo de tiro (°)", min_value=-60, max_value=60, value=0, step=5,
            key="dope_incline",
            help="Aclive (+) ou declive (-). Reduz a elevacao necessaria por "
                 "cos(angulo) — a 'regra do atirador'. Subir ou descer o mesmo "
                 "angulo pede a mesma correcao.",
        )

    entries = build_dope_card(
        result, unit=dope_unit, click_value=click_value, incline_deg=float(incline_deg)
    )
    if not entries:
        st.info("Calcule a trajetoria acima para gerar o cartao.")
        return

    dope_rows = []
    for e in entries:
        wind = "—" if e.windage_dir == "-" else f"{e.windage:.1f} {e.windage_dir}"
        dope_rows.append({
            "Dist (m)": int(e.range_m),
            f"Elevacao ({dope_unit})": e.elevation,
            "Elev (cliques)": e.elevation_clicks,
            f"Vento ({dope_unit})": wind,
            "Vento (cliques)": e.windage_clicks,
            "Vel (fps)": int(e.velocity_fps),
        })
    dope_df = pd.DataFrame(dope_rows)
    st.dataframe(dope_df, width='stretch', hide_index=True)
    st.caption(
        "Vento: **E** = dial para a esquerda (tiro foi para a direita), "
        "**D** = dial para a direita. Elevacao positiva = dial para cima."
    )
    if incline_deg:
        st.caption(
            f"Elevacao compensada para tiro a {incline_deg:+d}° "
            "(aproximacao pela regra do atirador)."
        )

    header = f"{selected_caliber} · {selected_projectile}"
    if selected_caliber == "Outro":
        header = "Configuracao manual"
    card_html = _render_dope_card_html(
        entries, dope_unit, click_label, float(incline_deg), header
    )

    exp1, exp2 = st.columns(2)
    with exp1:
        st.download_button(
            label="📇 BAIXAR CARTAO (HTML p/ imprimir)",
            data=card_html.encode("utf-8"),
            file_name="cartao_dope.html",
            mime="text/html",
            width='stretch',
        )
    with exp2:
        dope_csv = dope_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="EXPORTAR DOPE (CSV)",
            data=dope_csv,
            file_name="cartao_dope.csv",
            mime="text/csv",
            width='stretch',
        )
