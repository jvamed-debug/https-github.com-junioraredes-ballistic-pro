import streamlit as st
from core.config import setup_app
from core.auth import authenticate, register_user, recover_password
from core.models import init_db_if_empty, get_session, User
from ui.styles import apply_custom_styles, show_header
from services.ballistics_service import BallisticsService
from modules.reloading_data import show_reloading_data, show_calculator
from components.logbook_inventory import show_logbook_and_inventory
from modules.performance import show_performance_tab
from modules.profile import show_profile
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
        if auth_mode == "Login":
            with st.form("login_form"):
                user_in = st.text_input("Usuário")
                pass_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = authenticate(user_in, pass_in)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user.id
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
        # ... other auth modes
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 4. Main Application (Post-Auth)
show_header()

# Sidebar Setup
st.sidebar.markdown(f"""
    <div style='text-align: center; padding: 1.5rem 0; background: rgba(0, 242, 255, 0.03); border-radius: 8px; border: 1px solid rgba(0, 242, 255, 0.1); margin-bottom: 2rem;'>
        <div style='width: 12px; height: 12px; background: #00f2ff; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 10px #00f2ff;'></div>
        <span style='color: #00f2ff; font-family: "JetBrains Mono", monospace; font-size: 0.8rem; font-weight: 700;'>SISTEMA OPERACIONAL</span>
        <h3 style='color: white; margin-top: 10px; font-weight: 900; letter-spacing: -1px;'>OPERADOR {st.session_state.get("user_id", "N/A")}</h3>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["authenticated"] = False
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
