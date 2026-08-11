# Ballistic Pro — Frontend web (React + PWA)

Fase 2 da migração. App em **React + Vite + Tailwind**, instalável como **PWA**
(abre no navegador do iPhone/Android e vai para a tela inicial). Consome a
[API FastAPI](../api/README.md). É também a base que a Fase 3 empacota para as
lojas com Capacitor.

## Desenvolvimento

```bash
# 1) Suba a API (noutra aba)
uvicorn api.main:app --reload --port 8000

# 2) Suba o frontend
cd web
npm install
npm run dev        # http://localhost:5173 (proxia /api -> :8000)
```

- `npm run build` gera o estático em `dist/` (com service worker do PWA).
- `npm run preview` serve o build para conferência.

### Variáveis

- `VITE_API_URL` — base da API. **Vazio** (padrão) usa a mesma origem (`/api`),
  que é o caso quando o nginx faz o proxy. Defina só se a API estiver em outro
  host (ex.: `https://api.seudominio.com`).

## O que já tem (Fase 2, primeira fatia)

- **Login / Cadastro** contra `/api/auth/*` (token JWT no `localStorage`).
- **Cartão de DOPE**: entra projétil (peso, BC G1, V0), zero/máx/passo e vento,
  escolhe unidade da torre (MIL/MOA), valor do clique e ângulo de tiro, e recebe
  a tabela de correção **em cliques** de `/api/trajectory`. Botão para baixar o
  cartão em HTML imprimível.
- Tema tático escuro, responsivo, com respeito ao *safe area* do iPhone.

## Deploy no EasyPanel

Serviço separado, mesmo repositório:

- **Dockerfile:** `Dockerfile.web` (build Vite → nginx na porta `80`).
- O nginx serve o estático e faz **proxy de `/api`** para a API (uvicorn:8000)
  — mesma origem, sem CORS. O destino é configurável por **`API_UPSTREAM`**
  (`web/nginx.conf.template`, renderizado por envsubst na inicialização):
  padrão `api:8000` (docker-compose local); no EasyPanel use
  `NOME_PROJETO_api:8000` (ex.: `ballistic-pro_api:8000`).
- No `docker-compose.yml` local, o serviço `web` sobe na porta `8080`.
- Guia completo de deploy: [`../DEPLOY_EASYPANEL.md`](../DEPLOY_EASYPANEL.md).

## Próxima fase

- **3:** empacotar este frontend com **Capacitor** e publicar iOS/Android.
