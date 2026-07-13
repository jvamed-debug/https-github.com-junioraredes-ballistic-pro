import streamlit as st
from datetime import date
from core.models import managed_session, ReloadSession, InventoryItem, Firearm
from services.reloading_service import ReloadingService
from services.s3_service import s3_mgr

def show_logbook_and_inventory():
    if "user_id" not in st.session_state:
        st.error("Login necessário.")
        return

    user_id = st.session_state["user_id"]

    st.markdown('<div class="tech-hud">', unsafe_allow_html=True)
    log_tab, inv_tab = st.tabs(["📔 Sessões de Recarga", "📦 Estoque de Insumos"])

    with log_tab:
        st.markdown("### 📔 REGISTRO DE OPERAÇÕES (LOGBOOK)")
        st.markdown("""
            <div style='background: var(--card-bg); padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid var(--accent-primary); margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                <p style='color: var(--text-light); font-size: 0.8rem; margin: 0;'>
                    <b style='color: var(--accent-primary);'>HISTÓRICO TÉCNICO:</b> Registro cronológico de sessões de recarga e validação de lotes.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # UX-002: Paginação configurável
        col_page, col_size = st.columns([3, 1])
        page_size = col_size.selectbox("Por página", [10, 20, 50], index=0, key="log_page_size")
        
        with managed_session() as db:
            total_sessions = db.query(ReloadSession).filter_by(user_id=user_id).count()
            total_pages = max(1, -(-total_sessions // page_size))  # ceil division
            
        current_page = col_page.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1, key="log_page") - 1
        offset = current_page * page_size

        with managed_session() as db:
            sessions = db.query(ReloadSession).filter_by(user_id=user_id).order_by(ReloadSession.date.desc()).limit(page_size).offset(offset).all()
            if sessions:
                for s in sessions:
                    s_date = s.date.strftime('%d/%m/%Y') if s.date else "—"
                    cost_str = ""
                    if s.powder and s.charge:
                        try:
                            unit_cost = ReloadingService.calculate_unit_cost(s, user_id)
                            if unit_cost > 0:
                                cost_str = f" | <span style='color: #16a34a; font-size: 0.75rem;'>R$ {unit_cost:.2f}/un</span>"
                        except Exception:
                            pass
                    vel_str = ""
                    if s.velocity_avg:
                        vel_str = f" | <span style='color: #0ea5e9; font-size: 0.75rem;'>{s.velocity_avg:.0f}fps"
                        if s.velocity_sd:
                            vel_str += f" (SD {s.velocity_sd:.1f})"
                        vel_str += "</span>"
                    firearm_str = ""
                    if s.firearm and s.firearm.model:
                        firearm_str = f" | <span style='color: #a78bfa; font-size: 0.75rem;'>{s.firearm.model}</span>"
                    st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.02); padding: 10px; border-radius: 5px; border: 1px solid rgba(0,0,0,0.05); margin-bottom: 8px;'>
                            <span style='color: #64748b; font-size: 0.75rem; font-family: "JetBrains Mono";'>{s_date}</span> |
                            <b>{s.caliber}</b> |
                            <span style='color: #475569;'>{s.quantity or 0}un</span> |
                            <span style='color: #94a3b8; font-size: 0.8rem;'>{s.powder or '—'} ({s.charge or 0}gr) · {s.projectile or '—'}</span>{vel_str}{firearm_str}{cost_str}
                        </div>
                    """, unsafe_allow_html=True)
                    col_actions = st.columns([1, 1, 4])
                    if s.image_url:
                        with col_actions[0]:
                            st.image(s.image_url, caption=f"Alvo - {s.caliber}", width=300)
                    with col_actions[1]:
                        if st.button("Etiqueta", key=f"label_{s.id}"):
                            from label_gen import create_label_pdf
                            user_name = st.session_state.get("user_name", "N/A")
                            label_pdf = create_label_pdf(s, user_name)
                            st.download_button(
                                "Baixar Etiqueta",
                                data=label_pdf,
                                file_name=f"etiqueta_{s.caliber}_{s.id}.pdf",
                                mime="application/pdf",
                                key=f"dl_label_{s.id}",
                            )
                st.caption(f"Mostrando {len(sessions)} de {total_sessions} sessoes · Pagina {current_page + 1} de {total_pages}")
            else:
                st.info("Nenhuma sessão de recarga registrada ainda.")

        with st.expander("➕ Nova Sessão de Recarga", expanded=False):
            with managed_session() as db_fa:
                firearms_list = db_fa.query(Firearm).filter_by(user_id=user_id).all()
                firearm_options = {f"{f.model} (#{f.id})": f.id for f in firearms_list}

            with st.form("new_reload_form", clear_on_submit=True):
                if firearm_options:
                    r_firearm = st.selectbox("Arma", ["— Nenhuma —"] + list(firearm_options.keys()))
                else:
                    r_firearm = None
                    st.caption("Nenhuma arma cadastrada. Cadastre em Perfil > Armas.")

                r_col1, r_col2 = st.columns(2)
                r_caliber = r_col1.text_input("Calibre", placeholder="Ex: 9mm")
                r_powder = r_col1.text_input("Pólvora", placeholder="Ex: IMR 4064")
                r_charge = r_col1.number_input("Carga (grains)", min_value=0.0, step=0.1)
                r_primer = r_col1.text_input("Espoleta", placeholder="Ex: Small Pistol")
                r_proj = r_col2.text_input("Projétil", placeholder="Ex: 147gr JHP")
                r_vel = r_col2.number_input("Velocidade média (fps)", min_value=0.0, step=1.0)
                r_sd = r_col2.number_input("Desvio padrão (SD)", min_value=0.0, step=0.1)
                r_qty = r_col2.number_input("Quantidade", min_value=0, step=1)
                r_case = r_col2.text_input("Estojo", placeholder="Ex: CBC latão")
                r_img = st.file_uploader("Foto do Alvo (Opcional)", type=["jpg", "png", "jpeg"])
                r_notes = st.text_area("Observações Técnicas")
                if st.form_submit_button("SALVAR SESSÃO", use_container_width=True):
                    if r_caliber and r_qty > 0:
                        image_url = None
                        if r_img:
                            with st.spinner("Subindo imagem para o S3..."):
                                image_url = s3_mgr.upload_image(r_img, folder="targets")
                        
                        from schemas import ReloadSessionCreate
                        try:
                            selected_firearm_id = None
                            if r_firearm and r_firearm != "— Nenhuma —":
                                selected_firearm_id = firearm_options.get(r_firearm)

                            ReloadSessionCreate(
                                caliber=r_caliber,
                                quantity=r_qty,
                                charge=r_charge,
                                velocity_avg=r_vel,
                                velocity_sd=r_sd,
                                powder=r_powder or None,
                                projectile=r_proj or None,
                                primer=r_primer or None,
                                case=r_case or None,
                                firearm_id=selected_firearm_id,
                            )
                            
                            with managed_session() as db2:
                                new_sess = ReloadSession(
                                    user_id=user_id,
                                    firearm_id=selected_firearm_id,
                                    date=date.today(),
                                    caliber=r_caliber,
                                    powder=r_powder or None,
                                    charge=r_charge if r_charge > 0 else None,
                                    projectile=r_proj or None,
                                    primer=r_primer or None,
                                    case=r_case or None,
                                    velocity_avg=r_vel if r_vel > 0 else None,
                                    velocity_sd=r_sd if r_sd > 0 else None,
                                    quantity=r_qty,
                                    image_url=image_url,
                                    notes=r_notes or None,
                                )
                                db2.add(new_sess)

                            # FUN-002: Deduzir insumos do inventário (sessão própria no serviço)
                            _, deducted = ReloadingService.deduct_inventory(new_sess, user_id)

                            if deducted:
                                st.success(f"Sessão salva no Logbook! Insumos deduzidos: {len(deducted)} item(ns)")
                                with st.expander("Ver deduções"):
                                    for msg in deducted:
                                        st.caption(f"• {msg}")
                            else:
                                st.success("Sessão salva no Logbook!")
                                st.caption("ℹ️ Nenhum insumo correspondente encontrado no estoque para dedução automática.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Dados técnicos inválidos: {str(e)}")
                    else:
                        st.error("Calibre e Quantidade são obrigatórios.")



    with inv_tab:
        st.markdown("### 📦 ESTOQUE DE INSUMOS (INVENTORY)")
        
        # 1. Show existing inventory
        with managed_session() as db:
            items = db.query(InventoryItem).filter_by(user_id=user_id).all()
            if items:
                for item in items:
                    with st.container():
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                        c1.markdown(f"**{item.name}** ({item.category})")
                        c2.markdown(f"{item.quantity:.1f} {item.unit}")
                        c3.markdown(f"Lote: {item.batch_number or '—'}")
                        if c4.button("🗑️", key=f"del_inv_{item.id}"):
                            with managed_session() as db_del:
                                it_del = db_del.get(InventoryItem, item.id)
                                if it_del:
                                    db_del.delete(it_del)
                            st.rerun()
            else:
                st.info("Estoque vazio.")

        st.divider()

        # 2. Add/Update Item
        with st.expander("➕ Adicionar/Atualizar Insumo", expanded=False):
            with st.form("new_inv_form", clear_on_submit=True):
                i_col1, i_col2 = st.columns(2)
                i_cat = i_col1.selectbox("Categoria", ["Pólvora", "Projétil", "Espoleta", "Estojo", "Outro"])
                i_name = i_col1.text_input("Nome/Marca")
                i_batch = i_col1.text_input("Lote")
                i_qty = i_col2.number_input("Quantidade Adicional", min_value=0.0)
                i_unit = i_col2.selectbox("Unidade", ["grains", "g", "un", "kg", "lb"])
                i_price = i_col2.number_input("Custo Total (R$)", min_value=0.0, step=0.01)
                i_exp = i_col2.date_input("Validade", value=None)
                
                if st.form_submit_button("ATUALIZAR ESTOQUE", use_container_width=True):
                    if i_name and i_qty > 0:
                        # M6: Validação Pydantic
                        from schemas import InventoryItemCreate
                        try:
                            InventoryItemCreate(
                                category=i_cat,
                                name=i_name,
                                quantity=i_qty,
                                unit=i_unit,
                                price_unit=i_price/i_qty if i_qty > 0 else 0.0,
                                batch_number=i_batch or None,
                                expiration_date=i_exp,
                            )
                            
                            with managed_session() as db:
                                # Tenta encontrar lote existente
                                existing = db.query(InventoryItem).filter_by(
                                    user_id=user_id,
                                    category=i_cat,
                                    name=i_name,
                                    batch_number=i_batch
                                ).first()
                                
                                if existing:
                                    total_qty = existing.quantity + i_qty
                                    # Média ponderada do preço se houver custo informado
                                    if i_price > 0 and total_qty > 0:
                                        current_total_value = existing.quantity * existing.price_unit
                                        existing.price_unit = (current_total_value + i_price) / total_qty
                                    existing.quantity = total_qty
                                else:
                                    unit_price = i_price / i_qty if i_qty > 0 else 0
                                    db.add(InventoryItem(
                                        user_id=user_id,
                                        category=i_cat,
                                        name=i_name,
                                        batch_number=i_batch,
                                        quantity=i_qty,
                                        unit=i_unit,
                                        price_unit=unit_price,
                                        expiration_date=i_exp
                                    ))
                            st.success("Estoque atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Dados inválidos: {str(e)}")
                    else:
                        st.error("Nome e Quantidade são obrigatórios.")

    st.markdown('</div>', unsafe_allow_html=True)
