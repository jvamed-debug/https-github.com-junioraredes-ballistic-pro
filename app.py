import streamlit as st
import json
import os

# Set page config
st.set_page_config(
    page_title="Assistente de Recarga Balística",
    page_icon="🎯",
    layout="wide"
)

# Load Database
def load_data():
    if os.path.exists("database.json"):
        with open("database.json", "r") as f:
            return json.load(f)
    return {"calibers": {}}

db = load_data()

# Ensure Database Initialization and Default User
from models import User, Firearm, ReloadSession, InventoryItem, get_session
import bcrypt

def init_db_if_empty():
    session = get_session()
    try:
        if session.query(User).count() == 0:
            # Create Default Admin
            from datetime import date
            admin = User(
                username="atirador_pro",
                name="Atirador Demo",
                cpf="000.000.000-00",
                email="admin@ballisticpro.com",
                phone="(00) 00000-0000",
                cr_number="000000",
                cr_expiration=date(2030, 1, 1),
                is_premium=1
            )
            admin.set_password("senha123")
            session.add(admin)
            session.commit()
            print("Default user 'atirador_pro' created.")
    except Exception as e:
        print(f"DB Init Error: {e}")
    finally:
        session.close()

init_db_if_empty()
from datetime import datetime
from label_gen import create_label_pdf
from report_gen import create_inspection_report
from cv_utils import calculate_group_size
from bio_auth import save_biometrics, check_biometrics_available, clear_biometrics
import requests
import re

def show_ad():
    """Exibe um placeholder de anúncio se o usuário não for Premium."""
    if "user_id" in st.session_state and st.session_state["user_id"]:
        session = get_session()
        user = session.query(User).get(st.session_state["user_id"])
        
        if user and not user.is_premium:
            st.markdown("---")
            st.caption("Publicidade")
            # AdSense style placeholder (In a real app, this would be your ad script or native ad view)
            st.info("📢 **Espaço para Google Ads**\n\nTorne-se **Premium** para remover os anúncios e apoiar o desenvolvimento!")
            st.markdown("---")
        session.close()

# User Authentication Logic
def authenticate(username, password):
    session = get_session()
    user = session.query(User).filter_by(username=username).first()
    if user and user.check_password(password):
        session.close()
        return user
    session.close()
    return None

def register_user(username, password, name, cpf, email, phone):
    session = get_session()
    if session.query(User).filter_by(username=username).first():
        session.close()
        return False, "Usuário já existe."
    if email and session.query(User).filter_by(email=email).first():
        session.close()
        return False, "E-mail já cadastrado."
    
    new_user = User(username=username, name=name, cpf=cpf, email=email, phone=phone)
    new_user.set_password(password)
    session.add(new_user)
    session.commit()
    session.close()
    return True, "Usuário registrado com sucesso!"

def recover_password(identifier):
    session = get_session()
    user = session.query(User).filter((User.email == identifier) | (User.phone == identifier)).first()
    if user:
        # In a real app, we would send an email/SMS with a token.
        # For this demo, we'll just return a success message.
        session.close()
        return True, f"Instruções de recuperação enviadas para {identifier}."
    session.close()
    return False, "Usuário não encontrado com este e-mail ou telefone."

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# Custom CSS for Modern Clean Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    :root {
        --primary-color: #2563eb;
        --text-color: #000000; /* Pure Black for max contrast */
        --subtext-color: #333333; /* Dark Gray, almost black */
        --bg-color: #f4f4f5;
        --card-bg: #ffffff;
        --border-color: #d4d4d8;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--bg-color);
    }
    
    .stApp {
        background-color: var(--bg-color);
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    
    /* Force high contrast on generic text */
    p, li, label, .stMarkdown {
        color: #111111 !important;
    }

    /* --- METRICS FIX (CRITICAL) --- */
    div[data-testid="stMetric"] {
        background-color: var(--card-bg);
        border: 2px solid var(--border-color); /* Thicker border */
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1); /* Hard shadow for contrast */
        height: auto;
        min-height: 120px; 
    }
    
    /* Label */
    div[data-testid="stMetricLabel"] label {
        color: #444444 !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
    }
    
    /* Value - Fix Overflow */
    div[data-testid="stMetricValue"] {
        font-size: 24px !important; /* Fixed pixel size to avoid rem scaling issues */
        font-weight: 800 !important;
        color: #000000 !important;
        line-height: 1.3 !important;
        
        /* Force wrapping */
        word-wrap: break-word !important; 
        white-space: normal !important;
        overflow-wrap: break-word !important;
        width: 100% !important;
    }
    
    /* Specific check for very small containers */
    div[data-testid="stMetricValue"] div {
        word-break: break-all !important; 
    }

    /* --- INPUTS & CONTROLS --- */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 2px solid #a1a1aa !important; /* High contrast border */
        color: #000000 !important;
        font-weight: 600;
        border-radius: 8px;
    }
    
    /* Ensure text INSIDE the select box is black */
    .stSelectbox div[data-baseweb="select"] span {
        color: #000000 !important;
    }
    
    /* Dropdown Menu (Popover) - Critical for readability */
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 2px solid #000000 !important;
    }
    
    /* Dropdown Options */
    li[data-baseweb="menu-item"] {
        color: #000000 !important; 
        font-weight: 600 !important;
        background-color: #ffffff !important;
    }
    
    /* Dropdown Hover/Selected State */
    li[data-baseweb="menu-item"]:hover, li[data-baseweb="menu-item"][aria-selected="true"] {
        background-color: #e4e4e7 !important; /* Light Gray */
        color: #000000 !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }

    /* Buttons - Primary Blue Style for Main Actions */
    .stButton > button {
        background-color: #2563eb !important; /* Primary Blue */
        color: #ffffff !important; /* White Text - Guaranteed Contrast */
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 12px 20px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8 !important; /* Darker Blue */
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Specific styling for Form Submit buttons (Entrar, Cadastrar) to ensure they pop */
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
        font-size: 1.1rem !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important; /* Pure White */
        border-right: 1px solid #e5e7eb !important;
        box-shadow: 2px 0 5px rgba(0,0,0,0.02);
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #111827 !important; /* Almost Black */
    }
    
    /* Fix Sidebar Labels/Text and Expander Content */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] li, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #111827 !important; /* Black text for inputs in sidebar */
    }
    
    /* Specific fix for Sidebar Expander content (like Powder Details) */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] strong {
         color: #000000 !important;
    }

    /* Force background of expander content in sidebar to be white */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        color: #000000 !important;
    }
    
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #e4e4e7;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #52525b !important;
        font-weight: 600;
        font-size: 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 3px solid #000000 !important;
    }
    
    /* Expander - General */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: 1px solid #e4e4e7;
        border-radius: 8px;
    }
    
    /* Expander Content - General */
    div[data-testid="stExpander"] > div[role="group"] {
        background-color: #ffffff !important;
    }
    
    /* --- LOGIN PAGE & FORM FIXES --- */
    /* Target inputs specifically within forms to ensure they are white/readable */
    div[data-testid="stForm"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #a1a1aa !important;
    }
    
    div[data-testid="stForm"] label {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* Logout Button Specific - Red/Distinct to separate from inputs */
    section[data-testid="stSidebar"] button {
        background-color: #ef4444 !important; /* Red-500 */
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background-color: #dc2626 !important; /* Red-600 */
    }

    /* Alerts/Toasts */
    .stAlert {
        border: 1px solid rgba(0,0,0,0.1);
        font-weight: 600;
        background-color: #ffffff !important; /* Force white background on alerts too */
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and Intro
# st.markdown("# 🎯 Ballistic Pro")
if os.path.exists("logo.png"):
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("logo.png", width=120)
    with col2:
        st.markdown("# Ballistic Pro")
        st.markdown("##### *Inteligência e Precisão em Recarga de Munições*")
else:
    st.markdown("# 🎯 Ballistic Pro")
    st.markdown("##### *Inteligência e Precisão em Recarga de Munições*")

if not st.session_state["authenticated"]:
    # Bio check
    bio_user = check_biometrics_available()
    
    if bio_user:
        st.info(f"Bem-vindo de volta, **{bio_user}**!")
        col_bio1, col_bio2 = st.columns([1, 1])
        if col_bio1.button("🔓 Entrar com Biometria", type="primary", use_container_width=True):
            # Auto-login simulation
            session = get_session()
            user = session.query(User).filter_by(username=bio_user).first()
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user_id"] = user.id
                st.session_state["username"] = user.username
                st.toast("Autenticado via Biometria!", icon="✅")
                st.rerun()
            session.close()
            
        if col_bio2.button("Usar Outra Conta", use_container_width=True):
            clear_biometrics()
            st.rerun()
            
    else:
        auth_mode = st.radio("Selecione uma opção", ["Login", "Cadastro", "Recuperar Senha"], horizontal=True)
        
        if auth_mode == "Login":
            with st.form("login_form"):
                st.subheader("Acesso ao Sistema")
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                remember_me = st.checkbox("Habilitar Biometria/FaceID para próximos acessos")
                submit = st.form_submit_button("Entrar")
                
                if submit:
                    user = authenticate(username, password)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user.id
                        st.session_state["username"] = user.username
                        
                        if remember_me:
                            save_biometrics(user.username)
                        
                        st.success(f"Bem-vindo, {user.name or user.username}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        elif auth_mode == "Cadastro":
            with st.form("register_form"):
                st.subheader("Criar Nova Conta")
                new_username = st.text_input("Usuário")
                new_password = st.text_input("Senha", type="password")
                confirm_password = st.text_input("Confirme a Senha", type="password")
                new_name = st.text_input("Nome Completo")
                new_cpf = st.text_input("CPF")
                new_email = st.text_input("E-mail")
                new_phone = st.text_input("Telefone")
                submit = st.form_submit_button("Cadastrar")
                
                if submit:
                    if new_username and new_password:
                        if new_password != confirm_password:
                            st.error("As senhas não coincidem.")
                        else:
                            success, message = register_user(new_username, new_password, new_name, new_cpf, new_email, new_phone)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    else:
                        st.error("Usuário e senha são obrigatórios.")
        else:
            with st.form("recovery_form"):
                st.subheader("Recuperação de Senha")
                identifier = st.text_input("E-mail ou Telefone cadastrado")
                submit = st.form_submit_button("Recuperar")
                
                if submit:
                    if identifier:
                        success, message = recover_password(identifier)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Informe seu e-mail ou telefone.")
    st.stop()

# Logout in sidebar
if st.sidebar.button("Sair / Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    clear_biometrics() # Clear biometrics on explicit logout
    st.rerun()

with st.expander("🛡️ Protocolo de Segurança e Termos"):
    st.info("""
    **Aviso:** A recarga de munição exige atenção absoluta. 
    Este software é uma ferramenta de apoio. Sempre valide os dados com manuais físicos e inicie com cargas mínimas.
    """)

# --- Financial & Inventory Dashboard ---
session = get_session()
user_inv = session.query(InventoryItem).filter_by(user_id=st.session_state["user_id"]).all()
total_investment = sum(item.quantity * item.price_unit for item in user_inv)
categories_count = {}
for item in user_inv:
    categories_count[item.category] = categories_count.get(item.category, 0) + 1
session.close()

db_col1, db_col2, db_col3, db_col4 = st.columns(4)
db_col1.metric("Investimento Total", f"R$ {total_investment:.2f}")
db_col2.metric("Itens em Estoque", len(user_inv))
db_col3.metric("Pólvoras", categories_count.get("Pólvora", 0))
db_col4.metric("Projéteis/Espoletas", categories_count.get("Projétil", 0) + categories_count.get("Espoleta", 0))

st.divider()

# Sidebar for Selection
st.sidebar.header("Configuração de Carga")

# Initialize manual variables
manual_caliber, manual_projectile, manual_powder = "N/A", "N/A", "N/A"

# 1. Caliber Selection
calibers = list(db["calibers"].keys())
calibers.sort()
calibers.append("Outro")
selected_caliber = st.sidebar.selectbox("Selecione o Calibre", calibers)

# 2. Projectile Selection
projectiles = []
if selected_caliber != "Outro" and selected_caliber in db["calibers"]:
    projectiles = list(db["calibers"][selected_caliber]["projectiles"].keys())
    projectiles.sort()
projectiles.append("Outro")
selected_projectile = st.sidebar.selectbox("Selecione o Projétil", projectiles)

# 3. Powder Selection (Filtered by Projectile)
available_powders = set()
if selected_caliber != "Outro" and selected_projectile != "Outro":
    try:
        proj_data = db["calibers"][selected_caliber]["projectiles"][selected_projectile]
        available_powders.update(proj_data["powders"].keys())
    except KeyError:
        pass

powders_list = list(available_powders)
powders_list.sort()
powders_list.append("Outro")
selected_powder = st.sidebar.selectbox("Selecione a Pólvora", powders_list)

# Display Powder Info (if available)
powder_meta = db.get("powders_metadata", {}).get(selected_powder)
if powder_meta:
    with st.sidebar.expander("ℹ️ Detalhes da Pólvora", expanded=True):
        st.markdown(f"**Formato:** {powder_meta.get('format', 'N/A')}")
        st.markdown(f"**Densidade:** {powder_meta.get('density', 'N/A')}")
        st.markdown(f"**Aplicação:** {powder_meta.get('app', 'N/A')}")

# Logic for Mode
# Check if the specific combination exists in DB
is_manual_mode = True
if selected_caliber != "Outro" and selected_projectile != "Outro" and selected_powder != "Outro":
    try:
        if selected_powder in db["calibers"][selected_caliber]["projectiles"][selected_projectile]["powders"]:
            is_manual_mode = False
    except KeyError:
        pass # Stays manual mode

# Main Content Area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dados de Recarga", "🧪 Calculadora Preditiva", "📔 Logbook & Insumos", "📈 Análise de Performance", "👤 Meu Perfil"])

with tab1:
    # Display Dimensions (Always if available)
    caliber_data = db["calibers"].get(selected_caliber, {})
    max_oal = caliber_data.get("max_oal", "N/A")
    max_case = caliber_data.get("max_case", "N/A")
    proj_dia = caliber_data.get("proj_dia", "N/A")
    base_dia = caliber_data.get("base_dia", "N/A")

    if max_oal != "N/A":
        st.markdown("#### 📏 Dimensões do Calibre (SAAMI)")
        img_col, data_col = st.columns([1, 2])
        with img_col:
            image_path = "/Users/junioraredes/.gemini/antigravity/brain/06aa0d14-da33-45b0-80f6-4b95dbb92417/cartridge_technical_drawing_v2_1768246991029.png"
            if os.path.exists(image_path):
                st.image(image_path, caption="Esquema de Medidas (Genérico)", use_container_width=True)
            else:
                st.caption("Esquema de Medidas (Genérico)")
        with data_col:
            d1, d2 = st.columns(2)
            with d1:
                st.metric("Comp. Total (OAL)", max_oal)
                st.metric("Diâmetro Projétil", proj_dia)
            with d2:
                st.metric("Comp. do Estojo", max_case)
                st.metric("Diâmetro Base", base_dia)
        st.divider()

    if is_manual_mode:
        st.warning("⚠️ **MODO MANUAL**: Componentes não verificados em conjunto.")
        col1, col2 = st.columns(2)
        with col1:
            if selected_caliber == "Outro": manual_caliber = st.text_input("Calibre", key="man_cal")
            if selected_projectile == "Outro": manual_projectile = st.text_input("Projétil", key="man_proj")
            if selected_powder == "Outro": manual_powder = st.text_input("Pólvora", key="man_pow")
        with col2:
            if "manual_min" not in st.session_state: st.session_state["manual_min"] = 0.0
            if "manual_max" not in st.session_state: st.session_state["manual_max"] = 0.0
            final_min = st.number_input("Carga Mín (grains)", value=st.session_state["manual_min"], key="min_in")
            final_max = st.number_input("Carga Máx (grains)", value=st.session_state["manual_max"], key="max_in")
            st.session_state["manual_min"], st.session_state["manual_max"] = final_min, final_max
    else:
        st.success("✅ **DADOS VERIFICADOS**: Carregados do banco de dados oficial.")
        load_data = db["calibers"][selected_caliber]["projectiles"][selected_projectile]["powders"][selected_powder]
        final_min, final_max = load_data.get("min", 0.0), load_data.get("max", 0.0)
        final_unit, final_note = load_data.get("unit", "grains"), load_data.get("note", "")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Carga Mínima", f"{final_min} {final_unit}")
        m2.metric("Carga Máxima", f"{final_max} {final_unit}")
        m3.metric("Velocidade", f"{load_data.get('velocity', 'N/A')} fps")
        if final_note: st.info(f"Nota: {final_note}")

with tab2:
    if selected_powder == "Outro":
        st.markdown("### 🧪 Estimativa de Carga")
        st.caption("Baseado em modelos de energia cinética e eficiência termodinâmica.")
        c1, c2 = st.columns(2)
        with c1:
            target_vel = st.number_input("Velocidade Alvo (fps)", value=1000)
            # Robust weight parsing
            proj_w = 158.0 # Default
            if selected_projectile != "Outro":
                try:
                    proj_w = float(selected_projectile.split("gr")[0])
                except (ValueError, IndexError):
                    pass
            else:
                proj_w = st.number_input("Peso do Projétil (grains)", value=158.0)
        with c2:
            calorific = st.number_input("Poder Calorífico (J/g)", value=3800)
            efficiency = st.slider("Eficiência (%)", 5, 50, 25)
        
        # Calc
        m_kg, v_ms = proj_w * 0.0000647989, target_vel * 0.3048
        energy_j = 0.5 * m_kg * (v_ms ** 2)
        powder_g = energy_j / (calorific * (efficiency / 100))
        est_gr = powder_g * 15.4324
        
        st.metric("Energia Estimada", f"{energy_j:.1f} J")
        st.metric("Carga Sugerida", f"{est_gr:.2f} grains")
        if st.button("Aplicar Estimativa"):
            st.session_state["manual_max"], st.session_state["manual_min"] = round(est_gr, 2), round(est_gr * 0.9, 2)
            st.rerun()
    else:
        st.info("A calculadora está disponível apenas no **Modo Manual** (Pólvora: Outro).")

with tab3:
    session = get_session()
    user = session.query(User).get(st.session_state["user_id"])
    
    log_tab, inv_tab = st.tabs(["📔 Sessões de Recarga", "📦 Estoque de Insumos"])
    
    with log_tab:
        st.markdown("### 📔 Histórico de Recarga")
        
        # New Session Form
        with st.expander("📝 Registrar Nova Sessão", expanded=False):
            with st.form("new_session_form"):
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    s_date = st.date_input("Data da Recarga", value=datetime.now(), format="DD/MM/YYYY")
                    s_cal = st.text_input("Calibre", value=selected_caliber if selected_caliber != "Outro" else "")
                    s_proj = st.text_input("Projétil", value=selected_projectile if selected_projectile != "Outro" else "")
                    s_pow = st.text_input("Pólvora", value=selected_powder if selected_powder != "Outro" else "")
                    s_charge = st.number_input("Carga (grains)", min_value=0.0, step=0.1)
                with s_col2:
                    s_firearm = st.selectbox("Arma Destino", options=[None] + [(f.id, f.model) for f in user.firearms], format_func=lambda x: x[1] if x else "Nenhuma / Genérica")
                    s_qty = st.number_input("Quantidade", min_value=1, step=1)
                    s_primer = st.text_input("Espoleta")
                    s_case = st.text_input("Estojo / Marca")
                
                st.markdown("#### ⏱️ Performance & Agrupamento")
                p_col1, p_col2, p_col3 = st.columns(3)
                s_v_avg = p_col1.number_input("Vel. Média (fps)", min_value=0.0)
                s_v_sd = p_col2.number_input("SD (Desvio)", min_value=0.0)
                s_group = p_col3.number_input("Agrupamento (mm)", min_value=0.0)
                
                s_notes = st.text_area("Observações Adicionais")
                
                if st.form_submit_button("Salvar Registro"):
                    new_sess = ReloadSession(
                        user_id=user.id,
                        firearm_id=s_firearm[0] if s_firearm else None,
                        date=s_date,
                        caliber=s_cal,
                        projectile=s_proj,
                        powder=s_pow,
                        charge=s_charge,
                        primer=s_primer,
                        case=s_case,
                        quantity=s_qty,
                        velocity_avg=s_v_avg,
                        velocity_sd=s_v_sd,
                        grouping_mm=s_group,
                        notes=s_notes
                    )
                    session.add(new_sess)
                    
                    # --- Automatic Inventory Deduction ---
                    inv_messages = []
                    
                    # 1. Deduct Powder
                    if s_pow:
                        powder_item = session.query(InventoryItem).filter(
                            InventoryItem.user_id == user.id,
                            InventoryItem.category == "Pólvora",
                            InventoryItem.name.ilike(f"%{s_pow}%")
                        ).first()
                        if powder_item:
                            needed_grains = s_charge * s_qty
                            deduction = needed_grains
                            # Conversion if stock is in grams (1g = 15.4324 grains)
                            if powder_item.unit.lower() == "g":
                                deduction = needed_grains / 15.4324
                            
                            powder_item.quantity -= deduction
                            inv_messages.append(f"Subtraído {deduction:.2f}{powder_item.unit} de {powder_item.name}")

                    # 2. Deduct Projectiles
                    if s_proj:
                        proj_item = session.query(InventoryItem).filter(
                            InventoryItem.user_id == user.id,
                            InventoryItem.category == "Projétil",
                            InventoryItem.name.ilike(f"%{s_proj}%")
                        ).first()
                        if proj_item:
                            proj_item.quantity -= s_qty
                            inv_messages.append(f"Subtraído {s_qty}un de {proj_item.name}")

                    # 3. Deduct Primers
                    if s_primer:
                        primer_item = session.query(InventoryItem).filter(
                            InventoryItem.user_id == user.id,
                            InventoryItem.category == "Espoleta",
                            InventoryItem.name.ilike(f"%{s_primer}%")
                        ).first()
                        if primer_item:
                            primer_item.quantity -= s_qty
                            inv_messages.append(f"Subtraído {s_qty}un de {primer_item.name}")

                    # 4. Deduct Cases
                    if s_case:
                        case_item = session.query(InventoryItem).filter(
                            InventoryItem.user_id == user.id,
                            InventoryItem.category == "Estojo",
                            InventoryItem.name.ilike(f"%{s_case}%")
                        ).first()
                        if case_item:
                            case_item.quantity -= s_qty
                            inv_messages.append(f"Subtraído {s_qty}un de {case_item.name}")

                    session.commit()
                    st.success("Sessão registrada com sucesso!")
                    if inv_messages:
                        for msg in inv_messages:
                            st.toast(msg, icon="📦")
                    st.rerun()

        # Display sessions
        user_sessions = session.query(ReloadSession).filter_by(user_id=user.id).order_by(ReloadSession.date.desc()).all()
        if user_sessions:
            for s in user_sessions:
                with st.container(border=True):
                    h_col1, h_col2, h_col3 = st.columns([1, 2, 1])
                    h_col1.markdown(f"**{s.date.strftime('%d/%m/%Y')}**")
                    h_col1.caption(f"{s.caliber}")
                    
                    h_col2.markdown(f"**{s.quantity}un** com {s.charge}gr de {s.powder}")
                    h_col2.markdown(f"*{s.projectile}* | {s.primer} | {s.case}")
                    
                    # --- Cost Calculation for Display ---
                    def get_item_price(cat, name):
                        it = session.query(InventoryItem).filter(InventoryItem.user_id == user.id, InventoryItem.category == cat, InventoryItem.name.ilike(f"%{name}%")).first()
                        return it.price_unit if it else 0

                    p_price = get_item_price("Pólvora", s.powder)
                    proj_price = get_item_price("Projétil", s.projectile)
                    prim_price = get_item_price("Espoleta", s.primer)
                    case_price = get_item_price("Estojo", s.case)

                    # Calc powder cost (grains to unit)
                    powder_item = session.query(InventoryItem).filter(InventoryItem.user_id == user.id, InventoryItem.category == "Pólvora", InventoryItem.name.ilike(f"%{s.powder}%")).first()
                    p_cost_unit = 0
                    if powder_item:
                        grains_per_unit = 1.0 if powder_item.unit.lower() == "grains" else 15.4324
                        p_cost_unit = (s.charge / grains_per_unit) * powder_item.price_unit
                    
                    total_unit_cost = p_cost_unit + proj_price + prim_price + case_price
                    
                    if total_unit_cost > 0:
                        h_col2.info(f"💰 Custo Est.: R$ {total_unit_cost:.2f} / munição")

                    if s.velocity_avg:
                        h_col3.metric("Vel. Média", f"{s.velocity_avg}fps")
                    
                    if s.notes:
                        st.info(f"Notas: {s.notes}")
                    
                    if st.button("Excluir", key=f"del_sess_{s.id}"):
                        session.delete(s)
                        session.commit()
                        st.rerun()
                    
                    # Label Button
                    label_pdf = create_label_pdf(s, user.username)
                    st.download_button(
                        label="🖨️ Etiqueta",
                        data=label_pdf,
                        file_name=f"label_{s.date}_{s.caliber}.pdf",
                        mime="application/pdf",
                        key=f"dl_lbl_{s.id}"
                    )
        else:
            st.info("Nenhuma sessão de recarga registrada ainda.")

    with inv_tab:
        st.markdown("### 📦 Meu Estoque")
        
        with st.expander("➕ Adicionar/Atualizar Item", expanded=False):
            with st.form("new_inv_form"):
                i_col1, i_col2 = st.columns(2)
                i_cat = i_col1.selectbox("Categoria", ["Pólvora", "Projétil", "Espoleta", "Estojo", "Outro"])
                i_name = i_col1.text_input("Nome/Marca")
                i_qty = i_col2.number_input("Quantidade", min_value=0.0)
                i_unit = i_col2.selectbox("Unidade", ["g", "grains", "un", "kg", "lb"])
                i_price = i_col2.number_input("Preço da Embalagem / Lote (R$)", min_value=0.0, step=0.01)
                
                if st.form_submit_button("Salvar no Estoque"):
                    unit_price = i_price / i_qty if i_qty > 0 else 0
                    existing = session.query(InventoryItem).filter_by(user_id=user.id, category=i_cat, name=i_name).first()
                    if existing:
                        # Update quantity and average price
                        total_qty = existing.quantity + i_qty
                        if total_qty > 0:
                            existing.price_unit = ((existing.quantity * existing.price_unit) + i_price) / total_qty
                        existing.quantity = total_qty
                        st.success(f"Estoque de {i_name} atualizado!")
                    else:
                        new_item = InventoryItem(user_id=user.id, category=i_cat, name=i_name, quantity=i_qty, unit=i_unit, price_unit=unit_price)
                        session.add(new_item)
                        st.success(f"{i_name} adicionado ao inventário!")
                    session.commit()
                    st.rerun()
        
        # List inventory
        items = session.query(InventoryItem).filter_by(user_id=user.id).all()
        if items:
            for item in items:
                with st.container(border=True):
                    i_c1, i_c2, i_c3 = st.columns([2, 2, 1])
                    i_c1.markdown(f"**{item.name}**")
                    i_c1.caption(item.category)
                    i_c2.metric("Quantidade", f"{item.quantity:.2f} {item.unit}")
                    i_c2.caption(f"Custo Médio: R$ {item.price_unit:.4f}/{item.unit}")
                    if i_c3.button("Remover", key=f"del_inv_{item.id}"):
                        session.delete(item)
                        session.commit()
                        st.rerun()
        else:
            st.info("Seu estoque está vazio.")

    session.close()

with tab4:
    import pandas as pd
    session = get_session()
    user = session.query(User).get(st.session_state["user_id"])
    
    st.markdown("### 📈 Performance Operacional")
    st.caption("Visualize a evolução da sua precisão e consistência ao longo do tempo.")
    
    # Filters
    perf_col1, perf_col2 = st.columns(2)
    p_cal = perf_col1.multiselect("Filtrar por Calibre", options=list(set([s.caliber for s in user.sessions])), default=None)
    
    # Fetch Data
    query = session.query(ReloadSession).filter_by(user_id=user.id)
    if p_cal:
        query = query.filter(ReloadSession.caliber.in_(p_cal))
    
    data = query.order_by(ReloadSession.date).all()
    
    if data:
        df = pd.DataFrame([{
            "Data": d.date.strftime('%d/%m/%Y'),
            "Agrupamento (mm)": d.grouping_mm,
            "Desvio Padrão (SD)": d.velocity_sd,
            "Velocidade Média": d.velocity_avg,
            "Carga (gr)": d.charge,
            "Calibre": d.caliber
        } for d in data])
        
        # Ensure numeric types
        df["Agrupamento (mm)"] = pd.to_numeric(df["Agrupamento (mm)"], errors='coerce').fillna(0)
        df["Desvio Padrão (SD)"] = pd.to_numeric(df["Desvio Padrão (SD)"], errors='coerce').fillna(0)

        # 1. Grouping Evolution
        st.markdown("#### 🎯 Evolução de Agrupamento")
        if not df[df["Agrupamento (mm)"] > 0].empty:
            chart_data = df[df["Agrupamento (mm)"] > 0].set_index("Data")[["Agrupamento (mm)"]]
            st.line_chart(chart_data, color="#ff4b4b")
        else:
            st.info("Sem dados de agrupamento registrados.")

        col_g1, col_g2 = st.columns(2)
        
        # 2. Velocity Consistency (SD)
        with col_g1:
            st.markdown("#### ⚡ Consistência (SD)")
            if not df[df["Desvio Padrão (SD)"] > 0].empty:
                sd_data = df[df["Desvio Padrão (SD)"] > 0].set_index("Data")[["Desvio Padrão (SD)"]]
                st.line_chart(sd_data, color="#29b5e8")
            else:
                st.caption("Sem dados de SD.")

        # 3. Load vs Velocity (Scatter - simplified as line for now or scatter with altair later)
        with col_g2:
            st.markdown("#### 🚀 Carga vs Velocidade")
            if not df[df["Velocidade Média"] > 0].empty:
                # Simple relation check
                vel_data = df[df["Velocidade Média"] > 0][["Carga (gr)", "Velocidade Média"]].sort_values("Carga (gr)")
                st.scatter_chart(vel_data, x="Carga (gr)", y="Velocidade Média", color="#00cc66")
            else:
                st.caption("Sem dados de velocidade.")

    else:
        st.info("Registre sessões no Logbook para visualizar os gráficos.")
    
    st.divider()
    st.markdown("#### 📋 Detalhamento por Recarga")
    if data:
        st.dataframe(
            df[[
                "Data", "Calibre", "Carga (gr)", "Velocidade Média", 
                "Desvio Padrão (SD)", "Agrupamento (mm)"
            ]].style.format({
                "Carga (gr)": "{:.1f}",
                "Velocidade Média": "{:.0f}",
                "Desvio Padrão (SD)": "{:.2f}",
                "Agrupamento (mm)": "{:.2f}"
            }),
            use_container_width=True
        )

    st.divider()
    st.markdown("#### 📷 Análise de Agrupamento por Foto (Beta)")
    st.caption("Faça upload de uma foto do seu alvo para estimar o tamanho do agrupamento.")
    
    target_img = st.file_uploader("Enviar Foto do Alvo", type=["jpg", "png", "jpeg"])
    
    if target_img:
        col_img1, col_img2 = st.columns(2)
        
        with col_img1:
            st.image(target_img, caption="Imagem Original", use_container_width=True)
            
        # Calibration Input
        ref_width = st.number_input("Largura Real da Imagem/Alvo (mm)", value=210.0, help="Para calibração precisa, informe a largura real da área capturada na foto (ex: 210mm para uma folha A4).")
        
        with st.expander("⚙️ Ajustes de Detecção (Avançado)", expanded=False):
            st.caption("Se os impactos não forem detectados corretamente, ajuste a sensibilidade.")
            cv_sens = st.slider("Sensibilidade (Limiar de Contraste)", 0, 255, 155, help="Valores menores detectam apenas pontos muito escuros. Aumente se o alvo estiver mal iluminado (Padrão 60% = 155).")
            cv_min_area = st.slider("Tamanho Mínimo do Furo (pixels)", 1, 200, 50, help="Aumente para ignorar sujeira. Um furo de 3mm costuma ter >50px em fotos normais.")
            debug_mode = st.checkbox("Mostrar Máscara Binária (Debug)", value=False)

    
        if st.button("🔍 Analisar Alvo (Auto-Detect)"):
             with st.spinner("Processando..."):
                 # 1. Run CV Analysis
                 results = calculate_group_size(target_img, target_width_mm=ref_width, sensitivity=cv_sens, min_area_px=cv_min_area)
                 
                 # 2. Prepare Display Data immediately
                 # We need to load dimensions here to calculate scaling
                 import io
                 import base64
                 from PIL import Image
                 if hasattr(target_img, "seek"): target_img.seek(0)
                 pil_image_temp = Image.open(target_img).convert("RGB")
                 
                 c_width = 600
                 scale = c_width / pil_image_temp.size[0]
                 c_height = pil_image_temp.size[1] * scale
                 
                 # Convert detected spots to FabricJS objects
                 canvas_objs = []
                 for x, y in results.get("detected_shots", []):
                     canvas_objs.append({
                        "type": "circle",
                        "originX": "center", "originY": "center",
                        "left": x * scale,
                        "top": y * scale,
                        "radius": 15,
                        "fill": "rgba(255, 0, 0, 0.8)", 
                        "stroke": "black", "strokeWidth": 2
                     })
                 
                 # Feedback to user
                 if len(canvas_objs) == 0:
                     st.warning("⚠️ Nenhum impacto detectado! Tente ajustar a 'Sensibilidade' ou 'Tamanho Mínimo'.")
                 else:
                     st.success(f"✅ {len(canvas_objs)} impactos detectados e marcados no alvo.")
                 
                 # Resize for display ONCE and make Base64 String (Stable)
                 c_height = pil_image_temp.size[1] * scale
                 pil_image_resized = pil_image_temp.resize((int(c_width), int(c_height)))
                 
                 import io
                 buff = io.BytesIO()
                 pil_image_resized.save(buff, format="JPEG")
                 img_str = base64.b64encode(buff.getvalue()).decode()
                 img_b64 = f"data:image/jpeg;base64,{img_str}"

                 # 3. Save EVERYTHING to Session State
                 st.session_state["cv_results"] = results 
                 # We separate INIT state (fixed) from LIVE state (metrics)
                 st.session_state["canvas_init_fixed"] = {"version": "4.4.0", "objects": canvas_objs} 
                 st.session_state["canvas_key"] = str(datetime.now()) 
                 st.session_state["canvas_bg_b64"] = img_b64 
                 st.session_state["canvas_dims"] = (int(c_width), int(c_height))
                 
                 st.rerun()
    
        # Logic for Interactive Canvas
        from streamlit_drawable_canvas import st_canvas
        from PIL import Image
        import io
        import base64

        def get_image_base64_url(img):
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        
        # Prepare initial state (background image)
        if hasattr(target_img, "seek"): target_img.seek(0)
        pil_image = Image.open(target_img).convert("RGB")
        
        # Determine canvas dimensions relative to image aspect ratio
        canvas_width = 600
        w_percent = (canvas_width / float(pil_image.size[0]))
        canvas_height = int((float(pil_image.size[1]) * float(w_percent)))
        
        # Scaling factor (Real Image Coords -> Canvas Coords)
        scale_factor = canvas_width / pil_image.size[0]

        # Resize for display
        pil_image_resized = pil_image.resize((canvas_width, canvas_height))
        
        # We need to inform scale factors elsewhere or use original pil_image size for calculations
        # The logic below already uses 'scale_factor' derived from original PIL image vs canvas width, so calculations remain valid locally.

        # Prepare Initial Drawings (from Auto-Detect)
        initial_drawing = {"version": "4.4.0", "objects": []}
        
        if "cv_results" in st.session_state and st.session_state["cv_results"]:
            res = st.session_state["cv_results"]
            shots = res.get("detected_shots", [])
            
            for i, (x, y) in enumerate(shots):
                # Convert to canvas coords
                cx, cy = x * scale_factor, y * scale_factor
                obj = {
                    "type": "circle",
                    "originX": "center",
                    "originY": "center",
                    "left": cx,
                    "top": cy,
                    "radius": 10,
                    "fill": "rgba(0, 255, 0, 0.5)",
                    "stroke": "red",
                    "strokeWidth": 2
                }
                initial_drawing["objects"].append(obj)

        st.markdown("#### ✏️ Edição Interativa")
        st.caption("Use o mouse para: **Mover** (arrastar), **Adicionar** (ferramenta círculo) ou **Remover** (selecionar e del) os impactos.")

        # Prepare Image for Canvas (Load from Session State String)
        if "canvas_bg_b64" in st.session_state:
            bg_image_param = st.session_state["canvas_bg_b64"]
            canvas_width, canvas_height = st.session_state.get("canvas_dims", (600, 400))
        else:
             # Fallback
             canvas_width = 600
             canvas_height = 400
             bg_image_param = None # Will produce blank canvas if not analyzed

        # --- STATE MANAGEMENT ---
        if "canvas_init_fixed" not in st.session_state:
            st.session_state["canvas_init_fixed"] = {"version": "4.4.0", "objects": []}

        # Toolbar Controls
        col_tools = st.columns([3, 1])
        with col_tools[0]:
            tool_map = {"🤚 Mover": "transform", "🟢 Adicionar": "circle", "❌ Apagar": "transform"}
            tool_choice = st.radio("Modo:", list(tool_map.keys()), horizontal=True, label_visibility="collapsed")
            mode = tool_map[tool_choice]
            if "Apagar" in tool_choice:
                st.info("💡 Clique no ponto e tecle **Delete/Backspace**.")

        # Manual Delete Button (Server-Side)
        with col_tools[1]:
            if st.button("↩️ Desfazer", help="Remove o último ponto"):
                # For Undo to work now, we must manipulate a state that feeds into initial_drawing OR force a key refensh.
                # Since we decoupled, the only way to undo is to UPDATE init_fixed and RESTART canvas.
                curr = st.session_state.get("canvas_current_state", st.session_state["canvas_init_fixed"]).get("objects", [])
                if curr: 
                    curr.pop()
                    st.session_state["canvas_init_fixed"]["objects"] = curr # Update "init"
                    st.session_state["canvas_key"] = str(datetime.now()) # Force Full Reload with new Init
                    st.rerun()


        canvas_result = None
        try:
             # Ensure we have a PIL image for background (String causes crash in older lib)
             bg_img_for_canvas = None
             if "canvas_bg_b64" in st.session_state:
                  # We have the string, but library wants PIL or URL. 
                  # Base64 URL works in newer versions. For 0.8.0, safest is PIL image.
                  # Let's decode or better: Use the dimension-matched blank PIL image if string fails?
                  # Actually, let's recover the PIL image from user input or cache it properly.
                  # Since I removed the PIL cache, let's Re-Open it here cheaply or use the one from session state if I saved it.
                  # I saved 'canvas_bg_b64'. I should have saved 'canvas_bg_pil'.
                  # QUICK FIX: Decode base64 back to PIL or load from file again (cached).
                  
                  # Re-loading from source is fast enough if cached by OS.
                  if hasattr(target_img, "seek"): target_img.seek(0)
                  from PIL import Image
                  img_source = Image.open(target_img).convert("RGB")
                  w, h = st.session_state.get("canvas_dims", (600, 400))
                  bg_img_for_canvas = img_source.resize((w, h))

             canvas_result = st_canvas(
                fill_color="rgba(255, 0, 0, 0.8)",
                stroke_color="black",
                background_image=bg_img_for_canvas,
                initial_drawing=st.session_state["canvas_init_fixed"], 
                update_streamlit=True,
                height=canvas_height,
                width=canvas_width,
                drawing_mode=mode,
                key=st.session_state.get("canvas_key", "init"),
                display_toolbar=True
            )
             
             # Sync Browser Results -> Server State (For Undo/Metrics only)
             # We DO NOT update 'canvas_init_fixed' here, preventing the loop.
             if canvas_result and canvas_result.json_data is not None:
                 st.session_state["canvas_current_state"] = canvas_result.json_data
                 
        except Exception as e:
            st.error(f"Erro canvas: {e}")
            
        # Real-time Calculation based on Canvas Data
        if canvas_result and canvas_result.json_data:
            objects_for_metrics = canvas_result.json_data["objects"]
        else:
            # Fallback to init if no interaction yet
            objects_for_metrics = st.session_state["canvas_init_fixed"].get("objects", [])

        if 'objects_for_metrics' in locals() and objects_for_metrics is not None:
            objects = objects_for_metrics
            final_shots = []
            
            # Extract centers from canvas objects (circles)
            for obj in objects:
                if obj["type"] == "circle":
                    # Convert back to real image coordinates for accurate MM calc
                    # Canvas (cx) / scale = Real (rx)
                    rx = (obj["left"]) / scale_factor
                    ry = (obj["top"]) / scale_factor
                    final_shots.append((rx, ry))
            
            # Calculate Metrics from Final Shots
            if len(final_shots) > 0:
                pixel_per_mm = pil_image.size[0] / ref_width
                
                # 1. MPI
                avg_x = sum([p[0] for p in final_shots]) / len(final_shots)
                avg_y = sum([p[1] for p in final_shots]) / len(final_shots)
                
                # 2. Max Spread (Group Size)
                max_dist_px = 0
                import numpy as np
                if len(final_shots) >= 2:
                    for i in range(len(final_shots)):
                        for j in range(i + 1, len(final_shots)):
                            dist = np.sqrt((final_shots[i][0] - final_shots[j][0])**2 + (final_shots[i][1] - final_shots[j][1])**2)
                            if dist > max_dist_px: max_dist_px = dist
                
                group_mm = max_dist_px / pixel_per_mm
                
                # 3. Mean Radius
                total_dist = sum([np.sqrt((p[0] - avg_x)**2 + (p[1] - avg_y)**2) for p in final_shots])
                mean_radius_mm = (total_dist / len(final_shots)) / pixel_per_mm

                st.markdown("#### 📊 Resultados (Tempo Real)")
                res_c1, res_c2, res_c3 = st.columns(3)
                res_c1.metric("Agrupamento", f"{group_mm:.2f} mm")
                res_c2.metric("Raio Médio", f"{mean_radius_mm:.2f} mm")
                res_c3.metric("Impactos", len(final_shots))
                
            else:
                st.warning("Adicione impactos (círculos) no alvo para calcular.")
    
    show_ad()
    session.close()

with tab5:
    session = get_session()
    user = session.query(User).get(st.session_state["user_id"])
    
    st.markdown("### 👤 Perfil do Atirador")
    st.info("Mantenha seus dados atualizados conforme a legislação vigente (Decreto 11.615/2023).")
    
    # --- Profile Form (No st.form wrapper to allow CEP button interactivity) ---
    u_col1, u_col2 = st.columns(2)
    with u_col1:
        new_name = st.text_input("Nome Completo", value=user.name or "")
        new_cpf = st.text_input("CPF (XXX.XXX.XXX-XX)", value=user.cpf or "", max_chars=14, help="Insira apenas números ou formato padrão")
        new_cr = st.text_input("CR (Certificado de Registro)", value=user.cr_number or "", help="Número do CR junto ao Exército Brasileiro/SFPC")
    
    with u_col2:
        new_email = st.text_input("E-mail", value=user.email or "")
        new_phone = st.text_input("Telefone (XX) XXXXX-XXXX", value=user.phone or "", max_chars=15, help="Formato: (11) 99999-9999")
        new_cr_exp = st.date_input("Validade do CR", value=user.cr_expiration or None, format="DD/MM/YYYY")
        
        st.markdown("---")
        st.caption("📍 Endereço do Acervo")
        
        # Address Logic
        addr_cols = st.columns([1, 2])
        cep = addr_cols[0].text_input("CEP", max_chars=9, placeholder="00000-000")
        
        # Helper variables for address
        current_addr = user.address_acervo or ""
        street_val, num_val, comp_val, neigh_val, city_val = "", "", "", "", ""
        
        if "cep_data" not in st.session_state:
            st.session_state["cep_data"] = {}

        if addr_cols[1].button("🔍 Buscar CEP") and len(cep) >= 8:
            try:
                clean_cep = re.sub(r'\D', '', cep)
                response = requests.get(f"https://viacep.com.br/ws/{clean_cep}/json/")
                if response.status_code == 200:
                    data = response.json()
                    if "erro" not in data:
                        st.session_state["cep_data"] = data
                        st.toast("Endereço encontrado!", icon="🗺️")
                    else:
                        st.error("CEP não encontrado.")
            except Exception as e:
                st.error(f"Erro ao buscar CEP")
        
        # Populate fields from session state or attempt to parse existing string (simplistic)
        if st.session_state.get("cep_data"):
            d = st.session_state["cep_data"]
            street_val = d.get("logradouro", "")
            neigh_val = d.get("bairro", "")
            city_val = f"{d.get('localidade')}/{d.get('uf')}"
        
        logradouro = st.text_input("Logradouro", value=street_val)
        
        c_num, c_comp = st.columns(2)
        numero = c_num.text_input("Número")
        complemento = c_comp.text_input("Complemento")
        
        c_bairro, c_cidade = st.columns(2)
        bairro = c_bairro.text_input("Bairro", value=neigh_val)
        cidade_uf = c_cidade.text_input("Cidade/UF", value=city_val)

    if st.button("Salvar Perfil Completo"):
        # Format validation (simple)
        clean_cpf = re.sub(r'\D', '', new_cpf)
        if len(clean_cpf) == 11:
            formatted_cpf = f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}"
        else:
            formatted_cpf = new_cpf # Keep as is if invalid length

        full_address = user.address_acervo # Default keep old
        if logradouro and numero:
            full_address = f"{logradouro}, {numero}"
            if complemento: full_address += f", {complemento}"
            full_address += f", {bairro} - {cidade_uf}"
            if cep: full_address += f", CEP: {cep}"

        user.name = new_name
        user.cpf = formatted_cpf
        user.cr_number = new_cr
        user.cr_expiration = new_cr_exp
        user.email = new_email
        user.phone = new_phone
        user.address_acervo = full_address

        session.commit()
        st.success("Perfil atualizado com sucesso!")
            
    # Setting Biometrics in Profile
    st.divider()
    st.markdown("### 🔐 Segurança")
    is_bio_active = check_biometrics_available() == user.username
    
    if is_bio_active:
        st.success("✅ Login Biométrico Ativado neste dispositivo.")
        if st.button("Desativar Biometria"):
            clear_biometrics()
            st.rerun()
    else:
        if st.button("Ativar Login Biométrico"):
            save_biometrics(user.username)
            st.success("Biometria ativada para os próximos logins!")
            st.rerun()

    # --- Premium Subscription ---
    st.divider()
    st.markdown("### 💎 Assinatura Premium")
    
    if user.is_premium:
        st.success("🌟 Você é um usuário **PREMIUM**! Aproveite o Ballistic Pro sem anúncios.")
        if st.button("Gerenciar Assinatura (Simulação)"):
             st.info("Em um app real, aqui abriria o gerenciamento da App Store / Google Play.")
    else:
        st.info("Remova anúncios e apoie o projeto por um valor único.")
        p_col1, p_col2 = st.columns([2, 1])
        p_col1.markdown("""
        **Vantagens Premium:**
        - 🚫 **Zero Anúncios**
        - ⚡ Prioridade no Suporte
        - ☁️ Backup Automático (Em breve)
        """)
        if p_col2.button("⭐ Virar Premium", type="primary"):
            # Simulate purchase
            user.is_premium = 1
            session.commit()
            st.balloons()
            st.success("🎉 Parabéns! Você agora é Premium.")
            st.rerun()


    # --- Report Generation Button ---
    st.divider()
    rep_col1, rep_col2 = st.columns([3, 1])
    rep_col1.markdown("### 📄 Relatório / Vistoria")
    rep_col1.caption("Gere um relatório PDF oficial contendo seus dados de acervo e histórico recente de recargas para apresentação em vistorias.")
    
    report_pdf = create_inspection_report(user)
    rep_col2.download_button(
        label="🖨️ Baixar Relatório",
        data=report_pdf,
        file_name=f"relatorio_acervo_{user.username}.pdf",
        mime="application/pdf"
    )

    st.divider()
    st.markdown("### 🔫 Minhas Armas (Acervo)")
    
    # Form to add new firearm
    with st.expander("➕ Cadastrar Nova Arma"):
        f_presets = ["Selecione...", "Glock G17", "Glock G19", "Taurus G2c", "Taurus TS9", "Taurus TH9", "Sig Sauer P320", "CZ P-10 C", "Imbel MD1", "Imbel MD2", "CBC Pump Military 3.0", "CBC 7022"]
        selected_preset = st.selectbox("Modelos Populares (Opcional)", f_presets)
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            default_model = selected_preset if selected_preset != "Selecione..." else ""
            f_model = st.text_input("Modelo", value=default_model)
            f_sigma = st.text_input("SIGMA")
            f_serial = st.text_input("Número de Série")
        with f_col2:
            f_craf = st.text_input("CRAF")
            f_exp = st.date_input("Data de Expiração (CRAF)", format="DD/MM/YYYY")
            
        if st.button("Adicionar Arma"):
            if f_model:
                new_firearm = Firearm(
                    user_id=user.id,
                    model=f_model,
                    sigma=f_sigma,
                    craf=f_craf,
                    serial=f_serial,
                    expiration=f_exp
                )
                session.add(new_firearm)
                session.commit()
                st.success(f"{f_model} cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("O modelo da arma é obrigatório.")

    # List firearms
    user_firearms = user.firearms
    if user_firearms:
        from datetime import datetime
        today = datetime.now().date()
        
        for firearm in user_firearms:
            exp_date = firearm.expiration
            days_left = (exp_date - today).days if exp_date else 999
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**{firearm.model}**")
                    st.caption(f"Série: {firearm.serial}")
                with c2:
                    st.markdown(f"SIGMA: {firearm.sigma}")
                    st.markdown(f"CRAF: {firearm.craf}")
                with c3:
                    if exp_date:
                        if days_left < 0:
                            st.error(f"EXPIRADO\n({firearm.expiration.strftime('%d/%m/%Y')})")
                        elif days_left < 90:
                            st.warning(f"Vence em {days_left} dias\n({firearm.expiration.strftime('%d/%m/%Y')})")
                        else:
                            st.success(f"Válido\n({firearm.expiration.strftime('%d/%m/%Y')})")
                    
                    if st.button("Excluir", key=f"del_{firearm.id}"):
                        session.delete(firearm)
                        session.commit()
                        st.rerun()
    else:
        st.info("Nenhuma arma cadastrada.")
    session.close()

# Tactical Range Card Summary
st.divider()
display_cal = selected_caliber if selected_caliber != "Outro" else locals().get('manual_caliber', 'MANUAL')
display_proj = selected_projectile if selected_projectile != "Outro" else locals().get('manual_projectile', 'MANUAL')
display_pow = selected_powder if selected_powder != "Outro" else locals().get('manual_powder', 'MANUAL')

st.markdown("---")
st.caption("© 2026 BALLISTIC TACTICAL ASSISTANT | FIELD READY SYSTEM")

