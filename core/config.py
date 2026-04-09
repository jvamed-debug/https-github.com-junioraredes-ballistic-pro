import streamlit as st

def setup_app():
    st.set_page_config(
        page_title="Ballistic Pro",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # PWA Injection
    st.markdown("""
        <link rel="manifest" href="/assets/pwa/manifest.json">
        <meta name="theme-color" content="#2563eb">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <script>
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('/assets/pwa/service-worker.js').then(function(registration) {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                    }, function(err) {
                        console.log('ServiceWorker registration failed: ', err);
                    });
                });
            }
        </script>
    """, unsafe_allow_html=True)
