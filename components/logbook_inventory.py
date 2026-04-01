import streamlit as st
from datetime import datetime, date
from core.models import managed_session, User, ReloadSession, InventoryItem, Firearm
from services.reloading_service import ReloadingService
from label_gen import create_label_pdf

def show_logbook_and_inventory():
    if "user_id" not in st.session_state:
        st.error("Login necessário.")
        return

    user_id = st.session_state["user_id"]

    # --- Lógica de escrita separada da renderização ---
    # O rerun é feito APÓS fechar a sessão, evitando vazamentos.
    _needs_rerun = _handle_inventory_form(user_id)

    # --- Renderização ---
    st.markdown('<div class="tech-hud">', unsafe_allow_html=True)
    log_tab, inv_tab = st.tabs(["📔 Sessões de Recarga", "📦 Estoque de Insumos"])

    with log_tab:
        st.markdown("### 📔 REGISTRO DE OPERAÇÕES (LOGBOOK)")
        st.markdown("""
            <div style='background: #fff; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid var(--accent-primary); margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                <p style='color: var(--text-light); font-size: 0.8rem; margin: 0;'>
                    <b style='color: var(--accent-primary);'>HISTÓRICO TÉCNICO:</b> Registro cronológico de sessões de recarga e validação de lotes.
                </p>
            </div>
        """, unsafe_allow_html=True)
        # Render Logbook entries (reload sessions)
        with managed_session() as db:
            sessions = db.query(ReloadSession).filter_by(user_id=user_id).order_by(ReloadSession.date.desc()).limit(20).all()
            if sessions:
                for s in sessions:
                    s_date = s.date.strftime('%Y-%m-%d') if s.date else "—"
                    s_vel = f"{s.velocity_avg} m/s" if s.velocity_avg else "—"
                    st.markdown(f"**{s_date}** – {s.caliber} – Pólvora: {s.powder or '—'} ({s.charge or 0}g) – Projétil: {s.projectile or '—'} – {s_vel}")
            else:
                st.info("Nenhuma sessão de recarga registrada ainda.")
        # Form to add new reload session
        with st.expander("➕ Nova Sessão de Recarga", expanded=False):
            with st.form("new_reload_form"):
                r_col1, r_col2 = st.columns(2)
                r_caliber = r_col1.text_input("Calibre")
                r_powder = r_col1.text_input("Pólvora (nome/tipo)")
                r_charge = r_col1.number_input("Carga (grains)", min_value=0.0, step=0.1)
                r_proj = r_col2.text_input("Projétil (nome/tipo)")
                r_vel = r_col2.number_input("Velocidade Média (m/s)", min_value=0.0, step=1.0)
                r_qty = r_col2.number_input("Quantidade", min_value=0, step=1)
                r_notes = st.text_area("Observações")
                submit = st.form_submit_button("Salvar Sessão")
                if submit and r_caliber:
                    with managed_session() as db2:
                        new_sess = ReloadSession(
                            user_id=user_id,
                            date=date.today(),
                            caliber=r_caliber,
                            powder=r_powder if r_powder else None,
                            charge=r_charge if r_charge > 0 else None,
                            projectile=r_proj if r_proj else None,
                            velocity_avg=r_vel if r_vel > 0 else None,
                            quantity=r_qty if r_qty > 0 else None,
                            notes=r_notes if r_notes else None,
                        )
                        db2.add(new_sess)
                    st.success("Sessão de recarga salva!")
                    st.rerun()

    with inv_tab:
        st.markdown("### 📦 ESTOQUE DE INSUMOS (INVENTORY)")
        st.markdown("""
            <div style='background: #fff; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); border-left: 5px solid var(--accent-primary); margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                <p style='color: var(--text-light); font-size: 0.8rem; margin: 0;'>
                    <b style='color: var(--accent-primary);'>GESTÃO DE MATERIAIS:</b> Controle quantitativo de pólvoras, espoletas e projéteis.
                </p>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("➕ Adicionar/Atualizar Item", expanded=False):
            with st.form("new_inv_form"):
                i_col1, i_col2 = st.columns(2)
                i_cat = i_col1.selectbox("Categoria", ["Pólvora", "Projétil", "Espoleta", "Estojo", "Outro"])
                i_name = i_col1.text_input("Nome/Marca")
                i_batch = i_col1.text_input("Número do Lote")
                i_qty = i_col2.number_input("Quantidade", min_value=0.0)
                i_unit = i_col2.selectbox("Unidade", ["g", "grains", "un", "kg", "lb"])
                i_price = i_col2.number_input("Preço da Embalagem / Lote (R$)", min_value=0.0, step=0.01)
                i_exp = i_col2.date_input("Validade", value=None)
                st.form_submit_button("Salvar no Estoque", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Rerun fora do with managed_session() — sessão já fechada com segurança
    if _needs_rerun:
        st.rerun()


def _handle_inventory_form(user_id: int) -> bool:
    """
    Processa o submit do formulário de estoque.
    Retorna True se um rerun for necessário (dados foram salvos).
    A sessão do banco é sempre fechada antes de retornar.
    """
    if "new_inv_form" not in st.session_state:
        return False

    form_data = st.session_state.get("new_inv_form", {})
    # Streamlit submits via form state; verificamos se o submit button foi acionado
    # O controle real do submit é feito pelo Streamlit internamente —
    # esta função é chamada antes da renderização para processar dados do ciclo anterior.
    # Por isso usamos st.session_state para flags explícitas.
    if not st.session_state.get("_inv_form_submitted"):
        return False

    # Limpa a flag antes de processar
    st.session_state["_inv_form_submitted"] = False
    data = st.session_state.get("_inv_form_data", {})

    with managed_session() as db:
        user = db.get(User, user_id)
        i_cat = data.get("category")
        i_name = data.get("name")
        i_batch = data.get("batch")
        i_qty = data.get("qty", 0.0)
        i_unit = data.get("unit")
        i_price = data.get("price", 0.0)
        i_exp = data.get("expiration")

        unit_price = i_price / i_qty if i_qty > 0 else 0
        existing = db.query(InventoryItem).filter_by(
            user_id=user.id,
            category=i_cat,
            name=i_name,
            batch_number=i_batch
        ).first()

        if existing:
            total_qty = existing.quantity + i_qty
            if total_qty > 0:
                existing.price_unit = ((existing.quantity * existing.price_unit) + i_price) / total_qty
            existing.quantity = total_qty
            st.success(f"Estoque do Lote {i_batch} atualizado!")
        else:
            new_item = InventoryItem(
                user_id=user.id,
                category=i_cat,
                name=i_name,
                batch_number=i_batch,
                expiration_date=i_exp,
                quantity=i_qty,
                unit=i_unit,
                price_unit=unit_price
            )
            db.add(new_item)
            st.success(f"{i_name} (Lote: {i_batch}) adicionado!")

    return True
