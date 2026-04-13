import streamlit as st
from core.config import setup_app
from core.auth import authenticate, register_user, recover_password
from core.models import init_db_if_empty, get_session, managed_session, User
from ui.styles import apply_custom_styles, show_header
from services.ballistics_service import BallisticsService
from modules.reloading_data import show_reloading_data, show_calculator
from components.logbook_inventory import show_logbook_and_inventory
from modules.performance import show_performance_tab
from modules.profile import show_profile
from bio_auth import check_biometrics_available, save_biometrics
import os

# 1. Setup & Styles
setup_app()
apply_custom_styles()
init_db_if_empty()

# 2. Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# 3. Auth Flow
if not st.session_state["authenticated"]:
    show_header()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_mode = st.radio("Selecione", ["Login", "Cadastro", "Recuperar"], horizontal=True)
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # Biometric Check (Refatorado TEC-002)
        try:
            saved_user = check_biometrics_available()
        except (PermissionError, RuntimeError):
            # Falha silenciosa: a opção de biometria simplesmente não aparecerá
            saved_user = None
        
        if auth_mode == "Login":
            if saved_user:
                st.info(f"Acesso via biometria disponível para: **{saved_user}**")
                if st.button("🔓 ACESSAR COM BIOMETRIA", use_container_width=True):
                    # Em um app nativo/PWA real, aqui dispararíamos o prompt do SO.
                    # No Streamlit, validamos a sessão criptografada salva.
                    with managed_session() as db_sess:
                        user_db = db_sess.query(User).filter(User.username == saved_user).first()
                        if user_db:
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user_db.id
                            st.session_state["user_name"] = user_db.name or user_db.username
                            st.success("Bem-vindo de volta!")
                            st.rerun()

            with st.form("login_form"):
                user_in = st.text_input("Usuário")
                pass_in = st.text_input("Senha", type="password")
                remember = st.checkbox("Habilitar Biometria neste dispositivo")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = authenticate(user_in, pass_in)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user.id
                        st.session_state["user_name"] = user.name or user.username
                        if remember:
                            save_biometrics(user.username)
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
        elif auth_mode == "Cadastro":
            with st.form("register_form"):
                reg_name = st.text_input("Nome Completo")
                reg_user = st.text_input("Nome de Usuário (Login)")
                reg_email = st.text_input("E-mail")
                reg_cpf = st.text_input("CPF (somente números)", max_chars=14)
                reg_phone = st.text_input("Telefone (opcional)", max_chars=15, placeholder="(XX) XXXXX-XXXX")
                reg_pass = st.text_input("Senha (mín. 8 caracteres)", type="password")
                reg_pass_conf = st.text_input("Confirme a Senha", type="password")
                
                if st.form_submit_button("CRIAR CONTA", use_container_width=True):
                    if reg_pass != reg_pass_conf:
                        st.error("As senhas não coincidem.")
                    elif not reg_user or not reg_pass or not reg_email:
                        st.error("Preencha todos os campos obrigatórios.")
                    elif len(reg_pass) < 8:
                        st.error("A senha deve ter no mínimo 8 caracteres.")
                    else:
                        # SEC-001: Ordem correta dos argumentos
                        success, message = register_user(
                            reg_user, reg_pass, reg_name, reg_cpf, reg_email, reg_phone or None
                        )
                        if success:
                            st.success("Conta criada com sucesso! Faça login.")
                        else:
                            st.error(f"Erro ao cadastrar: {message}")

        elif auth_mode == "Recuperar":
            st.info("ℹ️ **Sistema de Auto-Recuperação Local**")
            st.markdown("""
                Por questões de segurança e privacidade (SG-001), este aplicativo opera de forma 100% offline e não armazena senhas em texto plano.
                
                **Como recuperar o acesso:**
                1. Entre em contato com o **Administrador do Sistema** para um reset manual via banco de dados.
                2. Caso você tenha acesso ao servidor, utilize o script de manutenção `scratch/debug_db.py` para resetar sua credencial.
                
                *Futuras versões incluirão reset via Chave Mestra (Secrets).*
            """)
            if st.button("VOLTAR PARA LOGIN", use_container_width=True):
                st.rerun()


        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 4. Main Application (Post-Auth)
show_header()

# Sidebar Setup
st.sidebar.markdown(f"""
    <div style='text-align: center; padding: 1.5rem 0; background: rgba(255, 255, 255, 0.03); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2rem;'>
        <div style='width: 10px; height: 10px; background: #3b82f6; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);'></div>
        <span style='color: #94a3b8; font-family: "JetBrains Mono", monospace; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;'>Sessão Ativa</span>
        <h3 style='color: white; margin-top: 8px; font-weight: 700; font-size: 1.1rem;'>OPERADOR {st.session_state.get("user_name", "N/A")}</h3>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in ["authenticated", "user_id", "user_name", "cv_stats"]:
        st.session_state.pop(key, None)
    st.rerun()

st.sidebar.divider()

# Data & Selections
db = BallisticsService.load_data()
calibers = BallisticsService.get_calibers()
calibers.append("Outro")

with st.expander("⚡ CONFIGURAÇÃO DE CARGA (PARAMETER INPUT)", expanded=True):
    c1, c2, c3 = st.columns(3)
    sel_cal = c1.selectbox("Calibre", calibers)
    
    projs = []
    if sel_cal != "Outro":
        projs = list(db["calibers"][sel_cal]["projectiles"].keys())
    projs.append("Outro")
    sel_proj = c2.selectbox("Projétil", projs)
    
    pows = ["Outro"]
    if sel_cal != "Outro" and sel_proj != "Outro":
        pows = list(db["calibers"][sel_cal]["projectiles"][sel_proj]["powders"].keys())
    sel_pow = c3.selectbox("Pólvora", pows)

is_manual = (sel_cal == "Outro" or sel_proj == "Outro" or sel_pow == "Outro")

# Tabs Routing
t1, t2, t3, t4, t5 = st.tabs(["📊 Dados", "🧪 Calc", "📔 Log", "📈 Perf", "👤 Perfil"])

with t1:
    show_reloading_data(db, sel_cal, sel_proj, sel_pow, is_manual)

with t2:
    if is_manual:
        show_calculator(sel_proj)
    else:
        st.info("Disponível apenas em Modo Manual.")

with t3:
    show_logbook_and_inventory()

with t4:
    show_performance_tab(st.session_state["user_id"])

with t5:
    show_profile()
