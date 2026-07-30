import streamlit as st

def setup_app():
    st.set_page_config(
        page_title="Ballistic Pro",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # PWA — instalável na tela inicial do celular.
    #
    # Os arquivos ficam em ./static porque é a única pasta que o Streamlit
    # publica (em app/static, com enableStaticServing). O caminho anterior,
    # /assets/pwa/, nunca foi servido: o manifest respondia 404 e a instalação
    # falhava silenciosamente.
    #
    # Não há service worker. Um SW só controla páginas dentro do seu próprio
    # escopo, então um arquivo servido de /app/static/ jamais controlaria a
    # raiz do app, e o Streamlit não expõe o cabeçalho Service-Worker-Allowed
    # que levantaria essa restrição. Instalação e ícones funcionam sem ele;
    # cache offline, não.
    st.markdown("""
        <link rel="manifest" href="app/static/manifest.json">
        <link rel="apple-touch-icon" href="app/static/apple-touch-icon.png">
        <meta name="theme-color" content="#0a0e14">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-title" content="Ballistic Pro">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """, unsafe_allow_html=True)
