import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-main: #f8fafc;
        --bg-sidebar: #0f172a;
        --card-bg: #ffffff;
        --accent-primary: #2563eb;
        --accent-secondary: #64748b;
        --text-header: #0f172a;
        --text-body: #334155;
        --text-light: #64748b;
        --border-color: #e2e8f0;
        --success-base: #10b981;
        --warning-base: #f59e0b;
    }

    /* Layout & Base */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: var(--text-body);
    }

    .stApp {
        background-color: var(--bg-main);
    }

    /* Sidebar - Professional Dark Contrast */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }

    /* Professional Metrics */
    .stMetric {
        background: var(--card-bg) !important;
        padding: 1.5rem !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: var(--accent-primary) !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    
    .stMetric [data-testid="stMetricLabel"] {
        color: var(--text-light) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.5px;
    }

    /* Tabs - Clean Modern */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
        border-bottom: 2px solid var(--border-color);
        padding: 0;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none !important;
        padding: 0 10px !important;
        color: var(--text-light) !important;
        font-weight: 500 !important;
        transition: color 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        color: var(--accent-primary) !important;
        border-bottom: 2px solid var(--accent-primary) !important;
    }

    /* Expander - Card Style */
    .stExpander {
        background: var(--card-bg);
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stExpander summary {
        font-weight: 600 !important;
        color: var(--text-header) !important;
    }

    /* Technical Hud - Engineering Schematic Style */
    .tech-hud {
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-top: 4px solid var(--accent-primary);
        padding: 2rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
    }

    /* Image Display - Document/Lab Style */
    .stImage img {
        background: #ffffff;
        padding: 10px;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.02);
    }

    /* Buttons - Solid Primary */
    .stButton > button {
        background-color: var(--accent-primary);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        transition: background-color 0.2s ease, transform 0.1s ease;
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8;
        transform: translateY(-1px);
    }

    /* Auth Card */
    .auth-card {
        background: white;
        padding: 3rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
    }

    /* General Inputs */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border-radius: 6px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stAlert {
        border-radius: 8px !important;
        border: 1px solid transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_header():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 3rem 0;'>
            <h1 style='color: #0f172a; font-size: 3.5rem; font-weight: 950; margin-bottom: 0; letter-spacing: -2px;'>BALLISTIC PRO</h1>
            <p style='color: #64748b; font-size: 0.85rem; font-weight: 600; letter-spacing: 4px; text-transform: uppercase; margin-top: -5px;'>Engineering & Precision Interface</p>
            <div style='width: 40px; height: 3px; background: #2563eb; margin: 1.5rem auto;'></div>
        </div>
    """, unsafe_allow_html=True)
