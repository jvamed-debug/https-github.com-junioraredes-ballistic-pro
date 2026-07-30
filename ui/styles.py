import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        /* Paleta Tática / Engenharia */
        --bg-main: #0a0e14; /* Quase preto técnico */
        --bg-sidebar: #05070a; /* Mais escuro para contraste */
        --card-bg: #11151c; /* Fundo dos painéis */
        --accent-primary: #f59e0b; /* Âmbar Tático / Laranja */
        --accent-secondary: #1e293b; /* Bordas e detalhes secundários */
        --accent-glow: rgba(245, 158, 11, 0.15); /* Brilho sutil do painel */
        
        --text-header: #f8fafc; /* Texto brilhante */
        --text-body: #94a3b8; /* Texto de leitura normal */
        --text-light: #64748b; /* Texto secundário */
        
        --border-color: #1e293b;
        --border-focus: #f59e0b;
        
        --success-base: #10b981;
        --warning-base: #ef4444; /* Vermelho mais intenso para perigo/max */
        
        --br-radius: 2px; /* Brutalista, sem cantos arredondados fofos */
    }

    /* === Layout Base & Tipografia === */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-body);
        background-color: var(--bg-main) !important;
    }

    /* Forçar fundo escuro no app Streamlit */
    .stApp {
        background-color: var(--bg-main) !important;
    }
    
    /* Headers com fonte técnica/industrial */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Rajdhani', sans-serif !important;
        color: var(--text-header) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Escopado ao corpo da página: um seletor solto em `div` vaza para dentro
       de todo componente aninhado e sobrescreve as cores próprias deles. */
    .stMarkdown p, .stMarkdown span, .stMarkdown li {
        color: var(--text-body);
    }

    /* === Foco visível para navegação por teclado === */
    .stButton > button:focus-visible,
    .stDownloadButton > button:focus-visible,
    .stTabs [data-baseweb="tab"]:focus-visible,
    [data-testid="stSidebarCollapsedControl"] button:focus-visible,
    a:focus-visible,
    summary:focus-visible {
        outline: 2px solid var(--accent-primary) !important;
        outline-offset: 2px !important;
    }

    /* === Sidebar Tática === */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebarNav"] { padding-top: 2rem; }
    
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] h3 {
        color: var(--text-header) !important;
    }

    /* === Painéis de Métricas (HUD Style) === */
    .stMetric {
        background: var(--card-bg) !important;
        padding: 1.5rem !important;
        border-radius: var(--br-radius) !important;
        border: 1px solid var(--border-color) !important;
        border-left: 3px solid var(--accent-primary) !important; /* Destaque direcional */
        box-shadow: inset 0 0 15px rgba(0,0,0,0.5) !important;
        transition: all 0.2s ease;
    }
    
    .stMetric:hover {
        border-color: var(--accent-primary) !important;
        box-shadow: inset 0 0 20px var(--accent-glow) !important;
    }

    /* Valores de Engenharia - Fonte monoespaçada */
    .stMetric [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--text-header) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        letter-spacing: -1px;
    }
    
    .stMetric [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif !important;
        color: var(--accent-primary) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.85rem !important;
        letter-spacing: 1.5px;
    }

    /* === Guias (Tabs) - Estilo Painel === */
    /* São oito guias; num celular elas não cabem lado a lado, então a lista
       rola na horizontal em vez de espremer os rótulos. */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 0;
        border-radius: var(--br-radius);
        overflow-x: auto;
        scrollbar-width: thin;
        scrollbar-color: var(--accent-secondary) transparent;
        -webkit-overflow-scrolling: touch;
    }

    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { height: 3px; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track { background: transparent; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
        background: var(--accent-secondary);
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent !important;
        border: none !important;
        border-right: 1px solid var(--border-color) !important;
        padding: 0 20px !important;
        white-space: nowrap;
        /* --text-light sobre o fundo do painel dá 3.9:1, abaixo do mínimo de
           4.5:1 da WCAG AA para este tamanho. --text-body dá 7.3:1. */
        color: var(--text-body) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        color: var(--bg-main) !important;
        background-color: var(--accent-primary) !important;
        border-bottom: none !important;
    }

    /* === Expanders - Estilo Terminal === */
    .stExpander {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--br-radius) !important;
    }
    
    .stExpander summary {
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-header) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* === Entradas de Dados (Inputs) === */
    .stTextInput input, .stSelectbox select, .stNumberInput input, .stDateInput input {
        background-color: #05070a !important; /* Muito escuro para foco */
        color: var(--text-header) !important;
        border-radius: var(--br-radius) !important;
        border: 1px solid var(--border-color) !important;
        font-family: 'JetBrains Mono', monospace !important; /* Dados precisam de precisão */
        transition: border-color 0.15s ease;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 1px var(--accent-primary) !important;
    }

    /* === Botões - Ação Tática === */
    .stButton > button {
        background-color: var(--bg-main);
        color: var(--text-header);
        border: 1px solid var(--accent-primary);
        padding: 0.5rem 1.5rem;
        border-radius: var(--br-radius) !important;
        font-family: 'Rajdhani', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600 !important;
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-primary);
        color: var(--bg-main) !important;
        box-shadow: 0 0 15px var(--accent-glow);
    }
    
    .stButton > button:active { 
        transform: scale(0.98); 
    }

    /* === Caixas de Informação / Alertas === */
    .stAlert {
        background: var(--card-bg) !important;
        border-radius: var(--br-radius) !important;
        border: 1px solid var(--border-color) !important;
        border-left: 4px solid var(--accent-primary) !important;
        color: var(--text-body) !important;
    }
    
    .stAlert p {
        color: var(--text-body) !important;
    }

    /* Imagens de Câmeras/Hardware */
    .stImage img {
        background: var(--bg-main);
        padding: 4px;
        border: 1px solid var(--border-color);
        border-radius: var(--br-radius);
    }

    /* Technical Hud - Custom Component */
    .tech-hud {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-top: 3px solid var(--accent-primary);
        padding: 2rem;
        border-radius: var(--br-radius);
        margin: 1.5rem 0;
        position: relative;
    }
    
    .tech-hud::before {
        content: '[SYS_ACTIVE]';
        position: absolute;
        top: -10px;
        right: 15px;
        background: var(--bg-main);
        padding: 0 5px;
        color: var(--accent-primary);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
    }

    /* Dataframes/Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-color);
    }

    /* === Responsividade === */
    @media (max-width: 768px) {
        .stMetric { padding: 1rem !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        .header-title { font-size: 2.2rem !important; }

        /* Alvos de toque de 44px: recarga é feita de pé, na bancada,
           frequentemente com uma mão só. */
        .stButton > button,
        .stDownloadButton > button {
            min-height: 44px;
            padding: 0.75rem 1.25rem;
        }

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input { min-height: 44px; }

        .stTabs [data-baseweb="tab"] { padding: 0 14px !important; }

        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }

    /* === Movimento reduzido === */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
        .stButton > button:active { transform: none; }
    }

    /* === Esconder Elementos do Streamlit ===
       O cabeçalho não pode ser ocultado por inteiro: no mobile ele abriga o
       botão que reabre a sidebar recolhida, e sem ele o logout fica inacessível. */
    #MainMenu {display: none;}
    footer {display: none;}
    div.stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: auto !important;
    }

    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }

    [data-testid="stSidebarCollapsedControl"] button {
        background: var(--card-bg) !important;
        border: 1px solid var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Correção do fundo de blocos de markdown e info */
    .stMarkdown p { color: var(--text-body); }
    .stMarkdown strong { color: var(--text-header); }
    </style>
    """, unsafe_allow_html=True)

def show_header():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 3rem 0; border-bottom: 1px solid #1e293b; margin-bottom: 2rem;'>
            <h1 class='header-title' style='color: #f8fafc; font-family: "Rajdhani", sans-serif; font-size: 4rem; font-weight: 700; margin-bottom: 0; letter-spacing: 2px; text-transform: uppercase;'>
                BALLISTIC <span style='color: #f59e0b;'>PRO</span>
            </h1>
            <div style='display: flex; align-items: center; justify-content: center; gap: 15px; margin-top: 5px;'>
                <div style='width: 30px; height: 1px; background: #f59e0b;'></div>
                <p style='color: #94a3b8; font-family: "JetBrains Mono", monospace; font-size: 0.8rem; font-weight: 400; letter-spacing: 4px; margin: 0;'>
                    TACTICAL ENGINEERING INTERFACE
                </p>
                <div style='width: 30px; height: 1px; background: #f59e0b;'></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
