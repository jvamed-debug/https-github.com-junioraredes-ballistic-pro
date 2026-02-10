def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-deep: #060606;
        --bg-card: #0f172a;
        --accent-cyan: #00f2ff;
        --accent-orange: #ff4d00;
        --text-main: #f8fafc;
        --text-dim: #94a3b8;
        --border-sharp: 1px solid rgba(0, 242, 255, 0.2);
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: var(--text-main);
    }

    /* Global Dark Theme Overrides */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, var(--bg-deep) 100%);
        background-attachment: fixed;
    }

    /* Sidebar - High End Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(6, 6, 6, 0.9) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Sharp Metric HUD Styling */
    .stMetric {
        background: rgba(15, 23, 42, 0.8) !important;
        padding: 1.2rem !important;
        border-radius: 2px !important;
        border: var(--border-sharp) !important;
        border-left: 4px solid var(--accent-cyan) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .stMetric:hover {
        background: rgba(15, 23, 42, 1) !important;
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.15);
        transform: scale(1.02);
    }

    .stMetric [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-weight: 900 !important;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -1px;
    }
    
    .stMetric [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 1px;
        color: var(--text-dim) !important;
    }

    /* Tabs Styling - Tactical Pods */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.02);
        padding: 5px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: transparent !important;
        border: none !important;
        padding: 0 24px !important;
        color: var(--text-dim) !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--accent-cyan) !important;
        color: var(--bg-deep) !important;
        border-radius: 8px !important;
    }

    /* Expander Styling */
    .stExpander {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 4px !important;
        margin-bottom: 1.5rem;
    }
    
    .stExpander summary {
        font-weight: 700 !important;
        color: var(--accent-cyan) !important;
    }

    /* Buttons - Hard Action */
    .stButton > button {
        background: transparent;
        color: var(--accent-cyan);
        border: 1px solid var(--accent-cyan);
        padding: 0.8rem 2rem;
        border-radius: 2px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: var(--accent-cyan);
        color: var(--bg-deep);
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.4);
    }

    /* Auth Card */
    .auth-card {
        background: rgba(10, 10, 10, 0.95);
        padding: 3.5rem;
        border-radius: 4px;
        border: 2px solid var(--accent-cyan);
        box-shadow: 0 0 50px rgba(0, 242, 255, 0.1);
    }

    /* Technical Specs Card (Blueprint HUD) */
    .tech-hud {
        background: rgba(6, 6, 6, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-right: 4px solid var(--accent-cyan);
        padding: 24px;
        border-radius: 4px;
        margin-top: 20px;
        position: relative;
        overflow: hidden;
    }
    
    .tech-hud::before {
        content: 'SCANNING...';
        position: absolute;
        top: 10px;
        right: 15px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        color: var(--accent-cyan);
        opacity: 0.5;
        animation: blink 1s infinite;
    }

    @keyframes blink { 50% { opacity: 0; } }

    /* Images */
    .stImage img {
        border-radius: 2px;
        filter: grayscale(0.2) contrast(1.1);
        border: 1px solid rgba(0, 242, 255, 0.2);
    }

    /* Selectbox Overrides */
    div[data-baseweb="select"] {
        border-radius: 4px !important;
    }

    /* Better Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-deep); }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 0; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }

    /* Custom Info Boxes */
    .stAlert {
        background: rgba(0, 242, 255, 0.05) !important;
        border: 1px solid rgba(0, 242, 255, 0.2) !important;
        border-radius: 2px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_header():
    st.markdown("""
        <div style='text-align: center; padding: 2.5rem 0 3.5rem 0; background: radial-gradient(circle at center, rgba(0, 242, 255, 0.08) 0%, transparent 70%);'>
            <h1 style='background: linear-gradient(90deg, #00f2ff, #ffffff, #00f2ff); background-size: 200% auto; animation: shine 4s linear infinite; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 4.5rem; font-weight: 900; margin-bottom: 0; letter-spacing: -3px;'>BALLISTIC PRO</h1>
            <p style='color: #94a3b8; font-size: 1rem; font-weight: 700; letter-spacing: 6px; text-transform: uppercase; margin-top: -5px; opacity: 0.8;'>Precison Reloading Interface</p>
            <div style='width: 100px; height: 1px; background: #00f2ff; margin: 15px auto; opacity: 0.3;'></div>
        </div>
        <style>
            @keyframes shine {
                to { background-position: 200% center; }
            }
        </style>
    """, unsafe_allow_html=True)
