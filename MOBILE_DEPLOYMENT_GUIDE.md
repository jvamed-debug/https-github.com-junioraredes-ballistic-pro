# Guia de Publicação Mobile: Ballistic Pro 📱🎯

Este guia cobre a publicação nas lojas (Apple/Google) e a estratégia de monetização (Ads + Premium).

---

## 🏗️ Fase 1: Hospedagem do Backend (Python)
Como o app é feito em Streamlit (tecnologia Web), ele precisa estar hospedado em um servidor. O app mobile será uma "janela" (WebView) para este servidor.

1.  **Hospede o código:**
    *   Sugestão: **Google Cloud Run** ou **Streamlit Community Cloud**.
    *   Resultado: Você terá uma URL (ex: `https://app.ballisticpro.com.br`).

---

## 🤖 Fase 2: Android (Google Play Store)

### Passo 1: Transformar em App (TWA / Bubblewrap)
Usaremos a ferramenta oficial do Google para criar um APK a partir da sua URL.

1.  Instale o Bubblewrap: `npm install -g @bubblewrap/cli`
2.  Inicie o projeto: `bubblewrap init --manifest https://sua-url.com/manifest.json`
3.  Gere o arquivo `.aab`: `bubblewrap build`

### Passo 2: Google AdMob (Anúncios)
Como seu app é híbrido, temos duas opções para anúncios:
1.  **Anúncios Web (Mais simples):** Colocar blocos de Adsense/HTML no próprio código Python (já implementamos o placeholder).
    *   *Atenção:* O Google pode restringir Adsense dentro de apps.
2.  **Anúncios Nativos (Recomendado):** Usar um wrapper mais robusto (como **Median.co** ou **Capacitor**) que injeta o banner do AdMob nativamente no rodapé do app, sem mexer no Python.

### Passo 3: Publicação
1.  Crie conta no [Google Play Console](https://play.google.com/console) ($25 USD).
2.  Crie a ficha da loja (Imagens, Descrição, Classificação Etária).
3.  Suba o arquivo `.aab`.

---

## 🍎 Fase 3: iOS (Apple App Store)

A Apple exige que o app pareça nativo. Wrappers simples são rejeitados.

### Estratégia: Median.co (antigo GoNative)
Esta é a solução mais rápida para transformar sites em apps iOS aprováveis.
1.  Acesse [median.co](https://median.co).
2.  Insira a URL do seu app Streamlit.
3.  Ative plugins nativos (Biometria, Push Notifications) para justificar ser um app.
4.  **AdMob via Median:** Eles possuem integração nativa onde você coloca seu "Ad Unit ID" e o banner aparece no app.

---

## 💎 Estratégia de Monetização (Premium)

Já implementamos a lógica no código Python (`is_premium`):

1.  **Free:** O usuário vê o banner de "Espaço para Google Ads".
    *   *No app real:* O wrapper (Median/Android) detecta que o usuário é Free e exibe o banner do AdMob no rodapé.
2.  **Premium:** O usuário paga uma taxa única.
    *   *No código:* O botão "Virar Premium" atualiza o banco de dados (`user.is_premium = 1`).
    *   *UI:* O placeholder de anúncio desaparece.
    *   *Integração Real:* Você precisará integrar **Stripe** ou **RevenueCat** para processar o pagamento real. O botão atual é uma simulação.

---

## ✅ Checklist Final

- [x] Lógica de Premium no Banco de Dados.
- [x] Placeholder de Anúncios na UI.
- [ ] Contratar Hospedagem (Cloud).
- [ ] Gerar APK (Android) e IPA (iOS).
- [ ] Criar contas de Desenvolvedor (Apple/Google).
- [ ] Integrar Gateway de Pagamento (para cobrar de verdade).

Seu app está pronto para a fase de **Deploy**! 🚀
