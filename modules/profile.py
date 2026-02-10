import streamlit as st
import re
import requests
from core.models import get_session, User, Firearm
from ui.styles import apply_custom_styles
from bio_auth import save_biometrics, clear_biometrics, check_biometrics_available
from report_gen import create_inspection_report

def show_profile():
    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login.")
        return

    session = get_session()
    user = session.query(User).get(st.session_state["user_id"])
    
    st.markdown("### 👤 PERFIL DO ATIRADOR (CREDENTIALS)")
    st.markdown("""
        <div style='background: rgba(0, 242, 255, 0.03); padding: 15px; border-radius: 4px; border: 1px solid rgba(0, 242, 255, 0.1); margin-bottom: 25px;'>
            <p style='color: #00f2ff; font-family: "JetBrains Mono", monospace; font-size: 0.75rem; font-weight: 700; margin: 0;'>
                [IDENTIFICAÇÃO OPERACIONAL]
            </p>
            <p style='color: #94a3b8; font-size: 0.85rem; margin: 5px 0 0 0;'>
                Mantenha seus dados atualizados conforme a legislação vigente (Decreto 11.615/2023). 
                Estes dados são criptografados localmente.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    u_col1, u_col2 = st.columns(2)
    with u_col1:
        new_name = st.text_input("Nome Completo", value=user.name or "")
        new_cpf = st.text_input("CPF (XXX.XXX.XXX-XX)", value=user.cpf or "", max_chars=14)
        new_cr = st.text_input("CR (Certificado de Registro)", value=user.cr_number or "")
    
    with u_col2:
        new_email = st.text_input("E-mail", value=user.email or "")
        new_phone = st.text_input("Telefone (XX) XXXXX-XXXX", value=user.phone or "", max_chars=15)
        new_cr_exp = st.date_input("Validade do CR", value=user.cr_expiration or None, format="DD/MM/YYYY")
        
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
                except:
                    st.error("Erro ao buscar CEP")
        
        logradouro = st.text_input("Logradouro", value=st.session_state.get("addr_street", ""), key="addr_street_key")
        
        c_num, c_comp = st.columns(2)
        numero = c_num.text_input("Número")
        complemento = c_comp.text_input("Complemento")
        
        c_bairro, c_cidade = st.columns(2)
        bairro = c_bairro.text_input("Bairro", value=st.session_state.get("addr_neigh", ""), key="addr_neigh_key")
        cidade_uf = c_cidade.text_input("Cidade/UF", value=st.session_state.get("addr_city", ""), key="addr_city_key")

    if st.button("Salvar Perfil Completo", use_container_width=True):
        # Validation & Save logic
        user.name = new_name
        user.cpf = new_cpf
        user.cr_number = new_cr
        user.cr_expiration = new_cr_exp
        user.email = new_email
        user.phone = new_phone
        
        full_address = f"{logradouro}, {numero}"
        if complemento: full_address += f", {complemento}"
        full_address += f", {bairro} - {cidade_uf}, CEP: {cep}"
        user.address_acervo = full_address

        session.commit()
        st.success("Perfil atualizado!")
    
    st.divider()
    # Firearms management section...
    st.markdown("### 🔫 Minhas Armas (Acervo)")
    # (Rest of firearms logic here)
    session.close()

if __name__ == "__main__":
    apply_custom_styles()
    show_profile()
