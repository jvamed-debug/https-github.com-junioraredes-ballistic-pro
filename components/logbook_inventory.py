import streamlit as st
from datetime import datetime
from core.models import get_session, User, ReloadSession, InventoryItem, Firearm
from services.reloading_service import ReloadingService
from label_gen import create_label_pdf

def show_logbook_and_inventory():
    if "user_id" not in st.session_state:
        st.error("Login necessário.")
        return

    db = get_session()
    user = db.query(User).get(st.session_state["user_id"])
    
    st.markdown('<div class="tech-hud">', unsafe_allow_html=True)
    log_tab, inv_tab = st.tabs(["📔 Sessões de Recarga", "📦 Estoque de Insumos"])
    
    with log_tab:
        st.markdown("### 📔 REGISTRO DE OPERAÇÕES (LOGBOOK)")
        st.markdown("""
            <div style='background: rgba(0, 242, 255, 0.03); padding: 12px; border-radius: 4px; border-left: 3px solid #00f2ff; margin-bottom: 20px;'>
                <p style='color: #94a3b8; font-size: 0.8rem; margin: 0;'>
                    <b>AUDITORIA TÁTICA:</b> Histórico completo de sessões de recarga e validação de lotes.
                </p>
            </div>
        """, unsafe_allow_html=True)
        # All the logic for reload sessions form and list goes here...
        pass

    with inv_tab:
        st.markdown("### 📦 ESTOQUE DE INSUMOS (INVENTORY)")
        st.markdown("""
            <div style='background: rgba(0, 242, 255, 0.03); padding: 12px; border-radius: 4px; border-left: 3px solid #00f2ff; margin-bottom: 20px;'>
                <p style='color: #94a3b8; font-size: 0.8rem; margin: 0;'>
                    <b>GESTÃO DE MATERIAIS:</b> Controle quantitativo de pólvoras, espoletas e projéteis.
                </p>
            </div>
        """, unsafe_allow_html=True)
        # Inventory management with BATCH NUMBER support
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
                
                if st.form_submit_button("Salvar no Estoque", use_container_width=True):
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
                    db.commit()
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    db.close()
