# Publicar nas lojas (App Store & Google Play) — React + Capacitor

Este guia é para o **app web novo** (`web/`, React + Vite). O Capacitor
**empacota os assets dentro do app nativo** — os arquivos rodam do próprio
dispositivo, não é um WebView apontando para um site (o que a Apple costuma
rejeitar pela diretriz 4.2). O app fala com a sua **API remota** (a mesma do
EasyPanel) por HTTPS.

> O `capacitor.config.ts` e o projeto Android já estão no repositório
> (`web/android/`). O projeto iOS é gerado no Mac (`npx cap add ios`).

## Pré-requisitos

| Item | Custo | Observação |
|------|-------|-----------|
| Conta **Apple Developer** | US$ 99/ano | Só publica iOS com ela |
| **Mac + Xcode** | — | Build/assinatura iOS **só** no macOS |
| Conta **Google Play Console** | US$ 25 (único) | Publica Android |
| **Android Studio** | grátis | Build/assinatura Android |
| Node 20+ | grátis | Já usado no `web/` |

## 1. Apontar o app para a API de produção

No app empacotado **não existe** o proxy `/api` do nginx; então o build
precisa da **URL absoluta** da API. Como o serviço `web` no EasyPanel já expõe
a API sob `/api` no seu domínio, basta usar o domínio público:

```bash
cd web
# a base da API vira o seu dominio (que ja proxia /api)
VITE_API_URL=https://app.seudominio.com.br npm run build
```

`api.ts` monta as chamadas como `${VITE_API_URL}/api/...`. Sem `VITE_API_URL`
o build assume mesma origem (bom para a web, **não** para o app de loja).

## 2. Liberar as origens do app no CORS da API

O app nativo chama a API de outra origem (não do seu domínio):

- iOS: `capacitor://localhost`
- Android: `http://localhost`

No serviço **`api`** do EasyPanel, inclua-as em `API_CORS_ORIGINS`:

```
API_CORS_ORIGINS=https://app.seudominio.com.br,capacitor://localhost,http://localhost
```

(A autenticação é por token no cabeçalho `Authorization`, não por cookie —
não é preciso `allow_credentials`.)

## 3. Ícones e splash

Um ícone-fonte 1024×1024 da marca está em `web/resources/icon.png`. Gere os
tamanhos das duas plataformas com a ferramenta oficial:

```bash
cd web
npx @capacitor/assets generate --iconBackgroundColor '#0a0e14' --splashBackgroundColor '#0a0e14'
```

## 4. Android (no Linux/Mac/Windows)

```bash
cd web
VITE_API_URL=https://app.seudominio.com.br npm run build
npx cap sync android          # copia o build para o projeto android/
npm run cap:open:android      # abre no Android Studio
```

No Android Studio:
1. **Build → Generate Signed Bundle / APK → Android App Bundle (.aab)**.
2. Crie/So selecione sua *keystore* (guarde-a: é ela que assina todas as
   atualizações).
3. Suba o `.aab` no **Google Play Console** → crie o app → preencha ficha,
   política de privacidade e classificação → envie para revisão.

O Google costuma aprovar rápido apps com bom desempenho.

## 5. iOS (só no macOS)

```bash
cd web
VITE_API_URL=https://app.seudominio.com.br npm run build
npx cap add ios               # gera web/ios/ (só no Mac, primeira vez)
npx cap sync ios
npm run cap:open:ios          # abre no Xcode
```

No Xcode:
1. Selecione o **Team** (sua conta Apple Developer) em *Signing & Capabilities*.
2. Ajuste o **Bundle Identifier** se quiser (padrão `com.ballisticpro.app`).
3. **Product → Archive** → **Distribute App** → App Store Connect.
4. No **App Store Connect**, preencha a ficha, capturas e privacidade → envie
   para revisão.

### Diretriz 4.2 da Apple (importante)

A Apple rejeita apps que são "só um site embrulhado". A nosso favor: os assets
já rodam localmente (não é um WebView remoto) e o app é instalável/rápido. Para
reduzir risco de rejeição, considere agregar algo nativo de verdade antes de
enviar (ex.: notificações, biometria via plugin do Capacitor). Descreva bem, na
ficha, as funcionalidades offline e de cálculo balístico.

## 6. A cada atualização

```bash
cd web
VITE_API_URL=https://app.seudominio.com.br npm run build
npx cap sync                  # atualiza android e ios com o novo build
# depois: Android Studio (novo .aab) e/ou Xcode (novo Archive)
```

Lembre de subir o `versionCode`/`versionName` (Android) e o *build number*
(iOS) a cada envio.

## Comandos — resumo

| Ação | Comando |
|------|---------|
| Build apontando p/ API | `VITE_API_URL=... npm run build` |
| Sincronizar nativo | `npx cap sync` |
| Adicionar iOS (Mac) | `npx cap add ios` |
| Abrir Android Studio | `npm run cap:open:android` |
| Abrir Xcode | `npm run cap:open:ios` |
| Gerar ícones | `npx @capacitor/assets generate` |

---

O PWA no EasyPanel já atende iPhone e Android pelo navegador (instalável na
tela inicial). As lojas são um passo a mais, opcional, para distribuição e
descoberta.
