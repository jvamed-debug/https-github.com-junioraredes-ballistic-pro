import streamlit as st
import re
import requests
from core.models import managed_session, User, Firearm
from ui.styles import apply_custom_styles
from bio_auth import save_biometrics, clear_biometrics, check_biometrics_available
from report_gen import create_inspection_report

def show_profile():
    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login.")
        return

    user_id = st.session_state["user_id"]

    # Load user data into plain dict to avoid DetachedInstanceError
    user_data = None
    firearms_data = []
    sessions_data = []

    with managed_session() as session:
        user = session.get(User, user_id)
        if not user:
            st.error("Usuário não encontrado.")
            return
            
        # Serializar usuário
        user_data = {
            "name": user.name or "",
            "cpf": user.cpf or "",
            "cr_number": user.cr_number or "",
            "email": user.email or "",
            "phone": user.phone or "",
            "cr_expiration": user.cr_expiration,
            "address_acervo": user.address_acervo or ""
        }
        
        # Serializar armas
        for f in user.firearms:
            firearms_data.append({
                "model": f.model or "—",
                "serial": f.serial or "—",
                "sigma": f.sigma or "—",
                "craf": f.craf or "—"
            })
            
        # Serializar sessões recentes
        from core.models import ReloadSession
        sessions = session.query(ReloadSession).filter_by(user_id=user_id).order_by(ReloadSession.date.desc()).limit(10).all()
        for s in sessions:
            sessions_data.append({
                "date_str": s.date.strftime('%d/%m/%Y') if s.date else "N/A",
                "caliber": s.caliber,
                "charge": s.charge or 0,
                "quantity": s.quantity or 0,
                "date": s.date
            })

    u = user_data # Para compatibilidade com o código abaixo

    st.markdown("### 👤 PERFIL DO ATIRADOR (CREDENTIALS)")
    st.markdown("""
        <div style='background: #fff; padding: 15px; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 25px; border-left: 5px solid var(--accent-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <p style='color: var(--accent-primary); font-family: "JetBrains Mono", monospace; font-size: 0.75rem; font-weight: 700; margin: 0;'>
                [IDENTIFICAÇÃO OPERACIONAL]
            </p>
            <p style='color: var(--text-light); font-size: 0.85rem; margin: 5px 0 0 0;'>
                Mantenha seus dados atualizados conforme a legislação vigente (Decreto 11.615/2023). 
                Estes dados são criptografados localmente.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    u_col1, u_col2 = st.columns(2)
    with u_col1:
        new_name = st.text_input("Nome Completo", value=u["name"])
        new_cpf = st.text_input("CPF (XXX.XXX.XXX-XX)", value=u["cpf"], max_chars=14)
        new_cr = st.text_input("CR (Certificado de Registro)", value=u["cr_number"])
    
    with u_col2:
        new_email = st.text_input("E-mail", value=u["email"])
        new_phone = st.text_input("Telefone (XX) XXXXX-XXXX", value=u["phone"], max_chars=15)
        new_cr_exp = st.date_input("Validade do CR", value=u["cr_expiration"], format="DD/MM/YYYY")
        
        st.markdown("---")
        if st.button("📄 Gerar Relatório de Acervo (PDF)", use_container_width=True):
            with st.spinner("Gerando relatório..."):
                pdf_data = create_inspection_report(user_data, firearms_data, sessions_data)
                st.download_button(
                    label="📥 Baixar Relatório de Acervo",
                    data=pdf_data,
                    file_name=f"Relatorio_Acervo_{user_data['name'].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        
        st.markdown("---")
        st.caption("📍 Endereço do Acervo")
        
        addr_cols = st.columns([1, 1])
        cep = addr_cols[0].text_input("CEP", value=st.session_state.get("cep_val", ""), max_chars=9, placeholder="00000-000")
        
        if addr_cols[1].button("🔍 Buscar CEP", use_container_width=True) and len(cep) >= 8:
            with st.spinner("Buscando..."):
                try:
                    clean_cep = re.sub(r'\D', '', cep)
                    response = requests.get(f"https://viacep.com.br/ws/{clean_cep}/json/")
                    if response.status_code == 200:
                        data = response.json()
                        if "erro" not in data:
                            st.session_state["addr_street"] = data.get("logradouro", "")
                            st.session_state["addr_neigh"] = data.get("bairro", "")
                            st.session_state["addr_city"] = f"{data.get('localidade')}/{data.get('uf')}"
                            st.toast("Endereço sincronizado!", icon="🗺️")
                            st.rerun()
                except Exception:
                    st.error("Erro ao buscar CEP")
        
        logradouro = st.text_input("Logradouro", value=st.session_state.get("addr_street", ""), key="addr_street_key")
        
        c_num, c_comp = st.columns(2)
        numero = c_num.text_input("Número")
        complemento = c_comp.text_input("Complemento")
        
        c_bairro, c_cidade = st.columns(2)
        bairro = c_bairro.text_input("Bairro", value=st.session_state.get("addr_neigh", ""), key="addr_neigh_key")
        cidade_uf = c_cidade.text_input("Cidade/UF", value=st.session_state.get("addr_city", ""), key="addr_city_key")

    if st.button("Salvar Perfil Completo", use_container_width=True):
        full_address = f"{logradouro}, {numero}"
        if complemento:
            full_address += f", {complemento}"
        full_address += f", {bairro} - {cidade_uf}, CEP: {cep}"

        # M6: Validação Pydantic
        from schemas import UserCreate
        try:
            # Pegamos apenas os campos necessários para o schema (alguns podem ser opcionais)
            UserCreate(
                username=st.session_state.get("user_name", "user"), # Placeholder para validação
                password="validpassword123", # Placeholder para validação
                name=new_name,
                cpf=re.sub(r'\D', '', new_cpf),
                email=new_email,
                phone=new_phone,
                cr_number=new_cr,
                cr_expiration=new_cr_exp,
                address_acervo=full_address
            )
            
            with managed_session() as session:
                user = session.get(User, user_id)
                if user:
                    user.name = new_name
                    user.cpf = new_cpf
                    user.cr_number = new_cr
                    user.cr_expiration = new_cr_exp
                    user.email = new_email
                    user.phone = new_phone
                    user.address_acervo = full_address
            st.success("Perfil atualizado!")
        except Exception as e:
            st.error(f"Erro de validação: {str(e)}")
    
    st.divider()
    st.markdown("### 🔫 Minhas Armas (Acervo)")
    # List existing firearms — serialize to dicts to avoid DetachedInstanceError
    firearms_data = []
    with managed_session() as db:
        firearms = db.query(Firearm).filter_by(user_id=user_id).all()
        for f in firearms:
            firearms_data.append({
                "id": f.id,
                "model": f.model or "—",
                "sigma": f.sigma or "—",
                "craf": f.craf or "—",
                "serial": f.serial or "—",
                "expiration": str(f.expiration) if f.expiration else "—",
            })

    if firearms_data:
        for fd in firearms_data:
            cols = st.columns([3, 2, 2, 1])
            cols[0].markdown(f"**{fd['model']}** – Série: {fd['serial']}")
            cols[1].markdown(f"SIGMA: {fd['sigma']} | CRAF: {fd['craf']}")
            cols[2].markdown(f"Validade: {fd['expiration']}")
            if cols[3].button("🗑️", key=f"del_{fd['id']}"):
                with managed_session() as db_del:
                    firearm_to_del = db_del.get(Firearm, fd['id'])
                    if firearm_to_del:
                        from core.models import log_action
                        # Log da remoção antes de deletar
                        log_action(
                            user_id=user_id,
                            action="firearm_deleted",
                            table_name="firearms",
                            record_id=fd['id'],
                            old={"model": fd['model'], "serial": fd['serial'], "sigma": fd['sigma'], "craf": fd['craf']}
                        )
                        db_del.delete(firearm_to_del)
                st.success("Arma removida.")
                st.rerun()
    else:
        st.info("Nenhuma arma cadastrada.")

    # Form to add new firearm
    with st.expander("➕ Adicionar Arma", expanded=False):
        with st.form("new_firearm_form"):
            m_model = st.text_input("Modelo")
            m_serial = st.text_input("Número de Série")
            m_sigma = st.text_input("SIGMA")
            m_craf = st.text_input("CRAF")
            m_exp = st.date_input("Data de Validade")
            submit_f = st.form_submit_button("Salvar Arma")
            if submit_f and m_model:
                with managed_session() as db3:
                    new_f = Firearm(
                        user_id=user_id,
                        model=m_model,
                        serial=m_serial if m_serial else None,
                        sigma=m_sigma if m_sigma else None,
                        craf=m_craf if m_craf else None,
                        expiration=m_exp,
                    )
                    db3.add(new_f)
                    db3.flush() # Para pegar o ID
                    
                    from core.models import log_action
                    log_action(
                        user_id=user_id,
                        action="firearm_added",
                        table_name="firearms",
                        record_id=new_f.id,
                        new={"model": m_model, "serial": m_serial, "sigma": m_sigma, "craf": m_craf}
                    )
                st.success("Arma adicionada.")
                st.rerun()

if __name__ == "__main__":
    apply_custom_styles()
    show_profile()
