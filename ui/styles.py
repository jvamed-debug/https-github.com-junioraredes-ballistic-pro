import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-deep: #0a0b10;
        --bg-card: #15171e;
        --accent-cyan: #334155; /* Muted Slate */
        --accent-focus: #3b82f6; /* Professional Signal Blue */
        --accent-warn: #92400e; /* Muted Amber */
        --text-main: #f1f5f9;
        --text-dim: #94a3b8;
        --border-sharp: 1px solid rgba(255, 255, 255, 0.08);
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: var(--text-main);
    }

    /* Global Dark Theme Overrides */
    .stApp {
        background-color: var(--bg-deep);
        background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, var(--bg-deep) 100%);
        background-attachment: fixed;
    }

    /* Sidebar - High End Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Sharp Metric HUD Styling */
    .stMetric {
        background: rgba(255, 255, 255, 0.02) !important;
        padding: 1.2rem !important;
        border-radius: 4px !important;
        border: var(--border-sharp) !important;
        border-top: 2px solid var(--accent-focus) !important;
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: var(--text-main) !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stMetric [data-testid="stMetricLabel"] {
        font-weight: 500 !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
        letter-spacing: 2px;
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
        background-color: var(--accent-focus) !important;
        color: white !important;
        border-radius: 4px !important;
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

    /* Buttons - Sober & Professional */
    .stButton > button {
        background: var(--bg-card);
        color: var(--text-main);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 0.6rem 1.5rem;
        border-radius: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: var(--accent-focus);
        border-color: var(--accent-focus);
        color: white;
    }

    /* Auth Card */
    .auth-card {
        background: var(--bg-card);
        padding: 3.5rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }

    /* Technical Specs Card (Muted Blueprint) */
    .tech-hud {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 3px solid var(--accent-focus);
        padding: 24px;
        border-radius: 4px;
        margin-top: 20px;
        position: relative;
    }
    
    .tech-hud::before {
        content: 'VERIFIED DATA';
        position: absolute;
        top: 10px;
        right: 15px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        color: var(--text-dim);
        opacity: 0.6;
    }

    /* Images */
    .stImage img {
        border-radius: 4px;
        border: 1px solid rgba(0, 242, 255, 0.3);
        image-rendering: -webkit-optimize-contrast; /* Focus on sharpness */
        image-rendering: crisp-edges;
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
        <div style='text-align: center; padding: 2.5rem 0 3.5rem 0; background: radial-gradient(circle at center, rgba(255, 255, 255, 0.03) 0%, transparent 70%);'>
            <h1 style='color: white; font-size: 4rem; font-weight: 900; margin-bottom: 0; letter-spacing: -2px;'>BALLISTIC PRO</h1>
            <p style='color: var(--accent-focus); font-size: 0.9rem; font-weight: 600; letter-spacing: 5px; text-transform: uppercase; margin-top: -5px;'>Technical Precision Operations</p>
            <div style='width: 60px; height: 2px; background: var(--accent-focus); margin: 20px auto; opacity: 0.6;'></div>
        </div>
    """, unsafe_allow_html=True)
