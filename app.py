import streamlit as st
from html import escape as html_escape
from datetime import datetime, timedelta
from core.config import setup_app
from core.auth import authenticate, register_user
from core.models import init_db_if_empty, managed_session, User
from ui.styles import apply_custom_styles, show_header
from services.ballistics_service import BallisticsService
from modules.reloading_data import show_reloading_data, show_calculator
from components.logbook_inventory import show_logbook_and_inventory
from modules.performance import show_performance_tab
from modules.profile import show_profile
from modules.trajectory import show_trajectory_tab
from modules.ai_advisor_tab import show_ai_advisor_tab
from modules.cost_analytics import show_cost_analytics
from bio_auth import check_biometrics_available, save_biometrics

# 1. Setup & Styles
setup_app()
apply_custom_styles()
init_db_if_empty()

# 2. Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = None

# Session timeout: 60 minutes of inactivity
SESSION_TIMEOUT = timedelta(minutes=60)
if st.session_state["authenticated"]:
    now = datetime.now()
    last = st.session_state.get("last_activity")
    if last and (now - last) > SESSION_TIMEOUT:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        #  Depois da limpeza, para sobreviver a ela; e depois do rerun, porque
        #  um aviso desenhado aqui seria descartado no redesenho e o usuario
        #  cairia na tela de login sem saber por que foi deslogado.
        st.session_state["logout_reason"] = (
            "Sessão expirada por inatividade. Faça login novamente."
        )
        st.rerun()
    st.session_state["last_activity"] = now

# 3. Auth Flow
if not st.session_state["authenticated"]:
    show_header()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logout_reason = st.session_state.pop("logout_reason", None)
        if logout_reason:
            st.warning(logout_reason)
        auth_mode = st.radio("Selecione", ["Login", "Cadastro", "Recuperar"], horizontal=True)
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # 1. Biometria Funcional (WebAuthn/Passkey)
        from bio_auth import render_biometric_login
        
        if auth_mode == "Login":
            passkey_user = render_biometric_login()
            if passkey_user:
                # Se o WebAuthn autenticou, fazemos o login direto
                with managed_session() as db_sess:
                    user_db = db_sess.query(User).filter(User.username == passkey_user.username).first()
                    if user_db:
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user_db.id
                        st.session_state["user_name"] = user_db.name or user_db.username
                        st.success(f"Bem-vindo, {st.session_state['user_name']}!")
                        st.rerun()

            # 2. Biometria Legada (Dispositivo Conhecido)
            saved_user = check_biometrics_available()
            if saved_user:
                st.info(f"Acesso rápido disponível para: **{saved_user}**")
                if st.button("🔓 LOGIN RÁPIDO (DISPOSITIVO)", width='stretch'):
                    with managed_session() as db_sess:
                        user_db = db_sess.query(User).filter(User.username == saved_user).first()
                        if user_db:
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user_db.id
                            st.session_state["user_name"] = user_db.name or user_db.username
                            st.success("Acesso autorizado.")
                            st.rerun()

            with st.form("login_form"):
                user_in = st.text_input("Usuário")
                pass_in = st.text_input("Senha", type="password")
                remember = st.checkbox("Habilitar Biometria neste dispositivo")

                if st.form_submit_button("ENTRAR", width='stretch'):
                    from core.auth import (
                        login_lock_remaining,
                        record_failed_login,
                        clear_login_attempts,
                    )
                    #  O bloqueio e verificado no servidor, keyed pelo login
                    #  tentado — reconectar (nova sessao) nao o zera mais.
                    remaining = login_lock_remaining(user_in)
                    if remaining > 0:
                        st.error(
                            f"Muitas tentativas falhas. Tente novamente em {remaining}s."
                        )
                    else:
                        user = authenticate(user_in, pass_in)
                        if user:
                            clear_login_attempts(user_in)
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user.id
                            st.session_state["user_name"] = user.name or user.username
                            if remember:
                                save_biometrics(user.username)
                            st.rerun()
                        else:
                            record_failed_login(user_in)
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
                
                if st.form_submit_button("CRIAR CONTA", width='stretch'):
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
                            st.success("✅ Conta criada com sucesso! Você já pode fazer login.")
                            st.balloons()
                            # Limpa campos se necessário ou redireciona
                        else:
                            st.error(f"❌ Erro ao cadastrar:\n\n{message}")

        elif auth_mode == "Recuperar":
            st.markdown("### Recuperacao de Acesso")
            st.info("Por seguranca, senhas nao sao armazenadas em texto plano e nao podem ser recuperadas automaticamente.")
            with st.form("recovery_form"):
                recovery_input = st.text_input(
                    "E-mail ou Telefone cadastrado",
                    placeholder="email@exemplo.com ou (XX) XXXXX-XXXX"
                )
                if st.form_submit_button("SOLICITAR RECUPERACAO", width='stretch'):
                    if recovery_input:
                        from core.auth import recover_password
                        _, msg = recover_password(recovery_input)
                        st.success(msg)
                    else:
                        st.error("Informe seu e-mail ou telefone.")

            st.markdown("""
                **Alternativas:**

                1. Contate o administrador para redefinir sua senha.
                2. Crie uma nova conta se nao houver dados a preservar.

                Apos acessar, va em **Perfil** para exportar seus dados regularmente.
            """)
            st.markdown("**Contato do Suporte:**")
            st.code("suporte@ballistic-pro.app", language=None)


        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 4. Main Application (Post-Auth)
show_header()

# Sidebar Setup
st.sidebar.markdown(f"""
    <div style='text-align: center; padding: 1.5rem 0; background: rgba(255, 255, 255, 0.03); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2rem;'>
        <div style='width: 10px; height: 10px; background: #3b82f6; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);'></div>
        <span style='color: #94a3b8; font-family: "JetBrains Mono", monospace; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;'>Sessão Ativa</span>
        <h3 style='color: white; margin-top: 8px; font-weight: 700; font-size: 1.1rem;'>OPERADOR {html_escape(st.session_state.get("user_name", "N/A"))}</h3>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", width='stretch'):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.divider()

# Data & Selections
db = BallisticsService.load_data()
calibers = BallisticsService.get_calibers() + ["Outro"]

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
t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs([
    "📊 Dados", "🧪 Calc", "🎯 Trajetoria", "📔 Log",
    "📈 Perf", "🤖 IA", "💰 Custos", "👤 Perfil"
])

with t1:
    show_reloading_data(db, sel_cal, sel_proj, sel_pow, is_manual)

with t2:
    if is_manual:
        show_calculator(sel_proj)
    else:
        st.markdown("### 🧪 Calculadora Manual")
        st.info(
            "A calculadora esta disponivel no Modo Manual.\n\n"
            "Para ativa-la, selecione **\"Outro\"** em qualquer um dos campos de Configuracao de Carga "
            "(Calibre, Projetil ou Polvora) no painel acima.",
        )

with t3:
    show_trajectory_tab(db, sel_cal, sel_proj)

with t4:
    show_logbook_and_inventory()

with t5:
    show_performance_tab(st.session_state["user_id"])

with t6:
    show_ai_advisor_tab(db, sel_cal, sel_proj, sel_pow, st.session_state["user_id"])

with t7:
    show_cost_analytics(st.session_state["user_id"])

with t8:
    show_profile()
