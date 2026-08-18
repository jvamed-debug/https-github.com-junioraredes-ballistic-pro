# Deploy no EasyPanel — App web (React/PWA) + API (FastAPI) + Postgres

Guia da **arquitetura nova** (3 serviços). Se você ainda quer subir o app
Streamlit clássico, veja [`DEPLOY.md`](DEPLOY.md) — os dois podem coexistir,
pois compartilham `core/` e `services/`.

## Arquitetura

```
Navegador (iPhone/Android/desktop)
        │  HTTPS
        ▼
┌──────────────┐   /api/*   ┌──────────────┐   SQL   ┌──────────────┐
│  web (nginx) │──────────▶ │  api (uvicorn)│───────▶ │  db (Postgres)│
│  React + PWA │  proxy     │   FastAPI     │         │              │
│  porta 80    │            │  porta 8000   │         │  porta 5432  │
└──────────────┘            └──────────────┘         └──────────────┘
   público                     interno                   interno
```

- Só o **web** é público (tem domínio + HTTPS). Ele serve o app e faz **proxy
  de `/api`** para a API na mesma origem — por isso o frontend não precisa de
  CORS nem de URL absoluta.
- A **API** cria o schema do banco sozinha ao subir (não há passo de migração
  manual). Usuários se cadastram pela própria tela (`/api/auth/register`).
- Hostname interno no EasyPanel: `NOME_PROJETO_NOME_SERVICO`. Com o projeto
  `ballistic-pro`, os serviços são `ballistic-pro_db`, `ballistic-pro_api`.

## Antes de começar — gere os segredos

```bash
# Chave de criptografia de PII (obrigatória em produção)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Segredo do JWT (use um valor forte e distinto da FERNET_KEY)
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Guarde os dois. **Perder a `FERNET_KEY` inutiliza os dados de PII já gravados**
(e-mail, telefone, CPF, dados da arma) — trate-a como um segredo permanente.

---

## 1. Projeto

EasyPanel → **Create Project** → nome `ballistic-pro`.

## 2. Serviço `db` (Postgres)

**+ Service → Postgres**

| Campo | Valor |
|-------|-------|
| Name | `db` |
| Password | gere uma senha forte |
| Database | `ballistic_db` |

Anote a *Internal Connection URL* (algo como
`postgresql://postgres:SENHA@ballistic-pro_db:5432/ballistic_db`).

## 3. Serviço `api` (FastAPI)

**+ Service → App**

- **Source:** GitHub → repositório `https-github.com-junioraredes-ballistic-pro`, branch `main`
- **Build:** Dockerfile → caminho **`Dockerfile.api`**
- **Port:** `8000` (interno; **não** precisa de domínio público)

### Variáveis de ambiente (`api`)

| Variável | Valor | Obrigatória |
|----------|-------|:-----------:|
| `DATABASE_URL` | `postgresql://postgres:SENHA@ballistic-pro_db:5432/ballistic_db` | ✅ |
| `FERNET_KEY` | a chave gerada acima | ✅ (produção) |
| `JWT_SECRET` | o segredo gerado acima | ✅ |
| `API_CORS_ORIGINS` | `https://app.seudominio.com.br` (ou `*` em teste) | recomendada |

> Como o web serve tudo na mesma origem (proxy `/api`), o CORS quase não é
> exercitado. Ainda assim, defina `API_CORS_ORIGINS` com o seu domínio em vez
> de `*` se um dia consumir a API de outra origem.

Opcionais: `BLIND_INDEX_KEY` (deriva o índice cego; por padrão usa a
`FERNET_KEY`), e `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `S3_BUCKET`
para upload de imagens.

#### Login por biometria (WebAuthn / passkeys) — opcional

Para habilitar o "Entrar com biometria" (Face ID / Touch ID / digital),
defina no serviço `api` — usando o **domínio público do serviço `web`**:

| Variável | Valor | Exemplo |
|----------|-------|---------|
| `WEBAUTHN_RP_ID` | o domínio (sem `https://`) | `app.seudominio.com.br` |
| `WEBAUTHN_RP_ORIGIN` | a origem completa | `https://app.seudominio.com.br` |
| `WEBAUTHN_RP_NAME` | nome exibido (opcional) | `Ballistic Pro` |

> O `RP_ID` precisa ser exatamente o domínio em que o app abre (a passkey fica
> atrelada a ele). Sem essas variáveis o recurso fica **desligado** e o app não
> mostra a opção — o login por senha continua igual. Exige **HTTPS** (já ligado
> no serviço `web`). Depois de ativar, cada usuário registra o dispositivo em
> **Perfil → Ativar biometria**.

#### Consultor com IA (Claude) — opcional

O Consultor (aba 🤖 IA) roda por padrão em **modo offline** (análise por regras,
determinística, sem rede). Para ligar a análise com IA, defina no serviço `api`:

| Variável | Valor |
|----------|-------|
| `ANTHROPIC_API_KEY` | sua chave da Anthropic (Claude) |

O SDK `anthropic` já vem instalado. Ao subir, a API faz um *health check* da
chave; se ela falhar (inválida, sem rede), o consultor **continua em offline** —
nunca devolve erro de SDK. Exige que a **política de rede** libere saída para
`api.anthropic.com`, e o uso da API da Anthropic é **cobrado à parte** por elas.
(Alternativa: `OPENAI_API_KEY` — descomente `openai` no `requirements.txt`.)

#### Clima automático no DOPE (Open-Meteo) — opcional

O botão "📍 Puxar clima" na aba DOPE preenche a atmosfera (temperatura, pressão,
umidade, altitude) a partir da localização, via **Open-Meteo** (sem cadastro,
sem chave). Só exige que a **política de rede** do ambiente permita saída HTTPS
para `api.open-meteo.com`. Se a saída estiver bloqueada, o botão apenas retorna
erro e o preenchimento manual continua funcionando — nada quebra.

Healthcheck já vem no Dockerfile: `GET /api/health`.

## 4. Serviço `web` (React/PWA + nginx)

**+ Service → App**

- **Source:** mesmo repositório, branch `main`
- **Build:** Dockerfile → caminho **`Dockerfile.web`**
- **Port:** `80`

### Variável de ambiente (`web`)

| Variável | Valor |
|----------|-------|
| `API_UPSTREAM` | `ballistic-pro_api:8000` |

> **Importante.** É o que faz o proxy `/api` do nginx encontrar a API dentro do
> EasyPanel. O padrão do Dockerfile é `api:8000` (que só resolve no
> docker-compose local); no EasyPanel **sobrescreva** com
> `NOME_PROJETO_api:8000`.

### Domínio e HTTPS (`web`)

1. **Domains** → adicione `app.seudominio.com.br`
2. **Port** → `80`
3. Ative **HTTPS** (Let's Encrypt automático)

---

## 5. Ordem de subida

1. `db` primeiro (aguarde ficar *healthy*).
2. `api` (ao subir, cria as tabelas no banco). Confira em **Logs** que não caiu
   no *fallback* de SQLite — se caiu, a `DATABASE_URL` está errada.
3. `web` por último.

Ative **Auto Deploy** em cada serviço para rebuildar a cada push na `main`.

## 6. Verificação

- `https://app.seudominio.com.br/api/health` → `{"status":"ok"}` (prova que o
  proxy web→api funciona).
- Abra o domínio, crie uma conta na tela de cadastro e faça login.
- No celular, use "Adicionar à tela inicial" para instalar o PWA.

## 7. Backup

O que importa é o **Postgres**. Configure backup do serviço `db` (snapshot do
volume ou `pg_dump` agendado). O `web` e o `api` são *stateless* — sobem de
novo a partir do repositório.

---

## Resumo das variáveis

| Serviço | Variável | Exemplo |
|---------|----------|---------|
| db | `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `postgres` / `••••` / `ballistic_db` |
| api | `DATABASE_URL` | `postgresql://postgres:••••@ballistic-pro_db:5432/ballistic_db` |
| api | `FERNET_KEY` | (Fernet, 44 chars) |
| api | `JWT_SECRET` | (token forte) |
| api | `API_CORS_ORIGINS` | `https://app.seudominio.com.br` |
| web | `API_UPSTREAM` | `ballistic-pro_api:8000` |

## Problemas comuns

- **502 / `/api` não responde** → `API_UPSTREAM` errado (não é
  `NOME_PROJETO_api:8000`) ou a `api` não está *healthy*.
- **API em modo desenvolvimento (sem cifra)** → faltou `FERNET_KEY` no serviço
  `api`. Os logs avisam com `[SECURITY] Chave de criptografia não encontrada`.
- **Login falha logo após deploy** → confira `JWT_SECRET` definido e igual
  entre reinícios (se mudar, todos os tokens antigos deixam de valer).
- **Dados de PII aparecem embaralhados** → a `FERNET_KEY` foi trocada. Restaure
  a chave original.
