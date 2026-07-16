import streamlit as st
import pandas as pd
from core.models import managed_session, ReloadSession, InventoryItem


def show_cost_analytics(user_id):
    st.markdown("### ANALISE DE CUSTOS E CONSUMO")
    st.markdown("""
        <div style='background: var(--card-bg); padding: 15px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid #10b981; margin-bottom: 20px;'>
            <p style='color: var(--text-light); font-size: 0.8rem; margin: 0;'>
                <b style='color: #10b981;'>GESTAO FINANCEIRA:</b> Custo por municao, consumo de insumos e projecoes de estoque.
            </p>
        </div>
    """, unsafe_allow_html=True)

    with managed_session() as db:
        inventory = db.query(InventoryItem).filter_by(user_id=user_id).all()
        inv_data = [{
            "Categoria": i.category,
            "Nome": i.name,
            "Quantidade": i.quantity,
            "Unidade": i.unit,
            "Preco/Un": i.price_unit,
            "Valor Total": round(i.quantity * i.price_unit, 2),
            "Lote": i.batch_number or "-",
            "Validade": str(i.expiration_date) if i.expiration_date else "-",
        } for i in inventory]

        sessions = db.query(ReloadSession).filter_by(user_id=user_id).order_by(
            ReloadSession.date.desc()
        ).limit(50).all()
        sess_data = [{
            "Data": s.date.strftime("%d/%m/%Y") if s.date else "-",
            "Calibre": s.caliber,
            "Polvora": s.powder or "-",
            "Carga (gr)": s.charge or 0,
            "Projetil": s.projectile or "-",
            "Quantidade": s.quantity or 0,
        } for s in sessions]

    # Summary metrics
    if inv_data:
        df_inv = pd.DataFrame(inv_data)
        total_value = df_inv["Valor Total"].sum()
        categories = df_inv.groupby("Categoria")["Valor Total"].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Valor Total em Estoque", f"R$ {total_value:.2f}")
        m2.metric("Itens no Estoque", len(inv_data))
        m3.metric("Sessoes Registradas", len(sess_data))

        total_rounds = sum(s["Quantidade"] for s in sess_data)
        m4.metric("Total de Municoes", f"{total_rounds} un")

        st.divider()

        # Cost per round estimation
        st.markdown("##### Custo Estimado por Municao")

        col_est1, col_est2 = st.columns(2)

        with col_est1:
            powder_items = [i for i in inv_data if i["Categoria"] == "Polvora"]
            primer_items = [i for i in inv_data if i["Categoria"] == "Espoleta"]
            bullet_items = [i for i in inv_data if i["Categoria"] == "Projetil"]
            case_items = [i for i in inv_data if i["Categoria"] == "Estojo"]

            st.markdown("**Componentes em estoque:**")
            for cat, items in [("Polvora", powder_items), ("Projetil", bullet_items),
                               ("Espoleta", primer_items), ("Estojo", case_items)]:
                if items:
                    for it in items:
                        st.caption(f"{cat}: {it['Nome']} - {it['Quantidade']:.1f} {it['Unidade']} @ R${it['Preco/Un']:.2f}/{it['Unidade']}")
                else:
                    st.caption(f"{cat}: Nenhum em estoque")

        with col_est2:
            charge_gr = st.number_input("Carga por Municao (grains)", value=5.0, step=0.1, key="cost_charge")

            powder_cost = 0.0
            if powder_items:
                p = powder_items[0]
                if p["Unidade"].lower() == "g":
                    charge_g = charge_gr / 15.4324
                    powder_cost = charge_g * p["Preco/Un"]
                else:
                    powder_cost = charge_gr * p["Preco/Un"]

            primer_cost = primer_items[0]["Preco/Un"] if primer_items else 0
            bullet_cost = bullet_items[0]["Preco/Un"] if bullet_items else 0
            case_cost = case_items[0]["Preco/Un"] if case_items else 0

            total_per_round = powder_cost + primer_cost + bullet_cost + case_cost

            st.markdown(f"""
                <div style='background: rgba(16, 185, 129, 0.05); padding: 15px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2); text-align: center; margin-top: 15px;'>
                    <p style='color: #10b981; font-family: "JetBrains Mono"; font-size: 0.7rem; margin: 0;'>CUSTO POR MUNICAO</p>
                    <p style='color: #f8fafc; font-size: 2rem; font-weight: 900; font-family: "JetBrains Mono"; margin: 5px 0;'>R$ {total_per_round:.2f}</p>
                    <div style='font-size: 0.7rem; color: #64748b; text-align: left; margin-top: 10px;'>
                        <div>Polvora: R$ {powder_cost:.3f}</div>
                        <div>Projetil: R$ {bullet_cost:.3f}</div>
                        <div>Espoleta: R$ {primer_cost:.3f}</div>
                        <div>Estojo: R$ {case_cost:.3f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Inventory value by category
        st.markdown("##### Valor do Estoque por Categoria")
        cat_df = categories.reset_index()
        cat_df.columns = ["Categoria", "Valor (R$)"]
        st.bar_chart(cat_df.set_index("Categoria"), color="#f59e0b")

        # Full inventory table
        st.markdown("##### Inventario Completo")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)

        # CSV exports
        exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            csv_inv = df_inv.to_csv(index=False).encode("utf-8")
            st.download_button("EXPORTAR INVENTARIO (CSV)", csv_inv, "inventario.csv", "text/csv", use_container_width=True)

        if sess_data:
            with exp_c2:
                df_sess = pd.DataFrame(sess_data)
                csv_sess = df_sess.to_csv(index=False).encode("utf-8")
                st.download_button("EXPORTAR SESSOES (CSV)", csv_sess, "sessoes.csv", "text/csv", use_container_width=True)
    else:
        st.info("Nenhum item no inventario. Adicione insumos na aba **Log** para ver analises de custo.")

    _show_low_stock_alerts(user_id)
    _show_expiration_alerts(user_id)


def _show_low_stock_alerts(user_id):
    st.divider()
    st.markdown("##### Alertas de Estoque Baixo")

    thresholds = {"Pólvora": 100, "Projétil": 50, "Espoleta": 100, "Estojo": 50}

    with managed_session() as db:
        items = db.query(InventoryItem).filter_by(user_id=user_id).all()
        alerts = []
        for item in items:
            threshold = thresholds.get(item.category, 20)
            if item.quantity <= 0:
                alerts.append((item.name, item.category, item.quantity, item.unit, "ESGOTADO"))
            elif item.quantity <= threshold:
                alerts.append((item.name, item.category, item.quantity, item.unit, "BAIXO"))

    if alerts:
        for name, cat, qty, unit, status in alerts:
            is_empty = status == "ESGOTADO"
            color = "#ef4444" if is_empty else "#f59e0b"
            icon = "!!" if is_empty else "!"
            st.markdown(f"""
                <div style='background: rgba({'239, 68, 68' if is_empty else '245, 158, 11'}, 0.08); padding: 10px 15px; border-radius: 6px; border-left: 4px solid {color}; margin-bottom: 8px;'>
                    <span style='color: {color}; font-weight: 700; font-family: "JetBrains Mono"; font-size: 0.75rem;'>[{icon}] {status}</span>
                    <span style='color: var(--text-body); margin-left: 10px;'>{name} ({cat})</span>
                    <span style='color: var(--text-light); font-size: 0.8rem; float: right;'>{qty:.1f} {unit}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Todos os insumos com estoque adequado.")


def _show_expiration_alerts(user_id):
    from datetime import date, timedelta
    from core.models import Firearm, User

    st.divider()
    st.markdown("##### Alertas de Vencimento")

    today = date.today()
    alert_threshold = today + timedelta(days=90)

    alerts = []

    with managed_session() as db:
        user = db.get(User, user_id)
        if user and user.cr_expiration:
            if user.cr_expiration <= today:
                alerts.append(("CR (Certificado de Registro)", user.cr_expiration, "VENCIDO"))
            elif user.cr_expiration <= alert_threshold:
                days_left = (user.cr_expiration - today).days
                alerts.append(("CR (Certificado de Registro)", user.cr_expiration, f"Vence em {days_left} dias"))

        firearms = db.query(Firearm).filter_by(user_id=user_id).all()
        for f in firearms:
            if f.expiration:
                if f.expiration <= today:
                    alerts.append((f"CRAF - {f.model}", f.expiration, "VENCIDO"))
                elif f.expiration <= alert_threshold:
                    days_left = (f.expiration - today).days
                    alerts.append((f"CRAF - {f.model}", f.expiration, f"Vence em {days_left} dias"))

        inv_items = db.query(InventoryItem).filter_by(user_id=user_id).all()
        for item in inv_items:
            if item.expiration_date:
                if item.expiration_date <= today:
                    alerts.append((f"Insumo: {item.name} (Lote {item.batch_number or 'N/A'})", item.expiration_date, "VENCIDO"))
                elif item.expiration_date <= alert_threshold:
                    days_left = (item.expiration_date - today).days
                    alerts.append((f"Insumo: {item.name}", item.expiration_date, f"Vence em {days_left} dias"))

    if alerts:
        for item_name, exp_date, status in alerts:
            is_expired = status == "VENCIDO"
            color = "#ef4444" if is_expired else "#f59e0b"
            icon = "!!" if is_expired else "!"
            st.markdown(f"""
                <div style='background: rgba({'239, 68, 68' if is_expired else '245, 158, 11'}, 0.08); padding: 10px 15px; border-radius: 6px; border-left: 4px solid {color}; margin-bottom: 8px;'>
                    <span style='color: {color}; font-weight: 700; font-family: "JetBrains Mono"; font-size: 0.75rem;'>[{icon}] {status}</span>
                    <span style='color: var(--text-body); margin-left: 10px;'>{item_name}</span>
                    <span style='color: var(--text-light); font-size: 0.8rem; float: right;'>{exp_date.strftime('%d/%m/%Y')}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Nenhum alerta de vencimento nos proximos 90 dias.")
