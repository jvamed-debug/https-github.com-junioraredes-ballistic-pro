# Ballistic Pro — API REST (FastAPI)

Primeira fase da migração para frontend web (React/PWA) e apps de loja
(Capacitor). A API reaproveita a camada de domínio existente (`core/`,
`services/`) — o mesmo motor de balística do app Streamlit — e roda **ao lado**
dele, sem substituí-lo enquanto a migração acontece.

## Rodando localmente

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

- Documentação interativa (OpenAPI): `http://localhost:8000/docs`
- Sonda de saúde: `GET /api/health`

## Endpoints (Fase 1a — stateless, sem auth)

| Método | Rota                          | Descrição                                             |
|--------|-------------------------------|-------------------------------------------------------|
| GET    | `/api/health`                 | Sonda de saúde (healthcheck).                         |
| GET    | `/api/catalog/calibers`       | Lista os nomes dos calibres do catálogo CBC.          |
| GET    | `/api/catalog`                | Catálogo completo (calibres → projéteis → pólvoras).  |
| GET    | `/api/catalog/caliber/{nome}` | Detalhes de um calibre (404 se não existir).          |
| POST   | `/api/trajectory`             | Trajetória externa; inclui o cartão de DOPE se o corpo trouxer `dope`. |

### Exemplo — trajetória + cartão de DOPE

```bash
curl -X POST http://localhost:8000/api/trajectory \
  -H 'Content-Type: application/json' \
  -d '{
    "projectile": {"weight_grains": 168, "bc_g1": 0.462, "muzzle_velocity_fps": 2650},
    "zero_range_m": 100, "max_range_m": 400, "step_m": 100,
    "dope": {"unit": "MIL", "click_value": 0.1, "incline_deg": 0}
  }'
```

A resposta traz `points` (trajetória) e, quando `dope` é enviado, `dope_card`
com a correção de elevação e vento **em cliques de torre**, já compensada por
ângulo de tiro (regra do atirador).

## Deploy no EasyPanel

Um serviço separado do Streamlit, mesmo repositório:

- **Dockerfile:** `Dockerfile.api` (uvicorn na porta `8000`).
- **CORS:** defina `API_CORS_ORIGINS` com a origem do frontend
  (ex.: `https://app.seudominio.com`). O default `*` é só para desenvolvimento.
- No `docker-compose.yml` local, o serviço `api` já sobe junto do `db`.

## Próximas fases

- **1b:** autenticação (JWT sobre `core.auth`) e dados do usuário (perfil,
  inventário, logbook).
- **2:** frontend React + PWA consumindo esta API.
- **3:** empacotamento iOS/Android com Capacitor.
