# Ballistic Pro

Sistema de gestao de recarga de municoes, controle de acervo e analise de performance com visao computacional.

Construido com **Streamlit**, **SQLAlchemy**, **OpenCV** e **ReportLab**. Suporta PostgreSQL (producao) e SQLite (desenvolvimento). Deploy via Docker no EasyPanel/Hostinger.

## Funcionalidades

### Dados e Recarga
- Catalogo de cargas de referencia (22+ calibres, polvoras CBC 216/219/231 e mais)
- Calculadora manual de carga (pressao, velocidade, energia)
- Diario de recarga com baixa automatica de estoque
- Etiquetas PDF para caixas de municao (100x60mm)

### Trajetoria Balistica
- Calculadora de trajetoria com modelo de arrasto (G1)
- Correcoes atmosfericas (temperatura, pressao, umidade, altitude)
- Deriva de vento, MPBR, queda em MOA/MIL
- Graficos interativos e exportacao CSV

### Visao Computacional
- Deteccao automatica de impactos no alvo via camera
- Calculo de agrupamento (Group Size) e raio medio
- Analise multi-grupo com threshold configuravel

### Gestao de Acervo
- Cadastro de armas com SIGMA, CRAF e numero de serie
- Alertas de vencimento de CR e CRAF
- Controle de estoque (polvora, espoletas, projeteis, estojos)
- Calculo automatico de custo por municao

### Performance e Relatorios
- Dashboard de performance com graficos de tendencia
- Relatorios PDF (inspecao e performance)
- Exportacao CSV de dados balisticos

### Consultor IA
- Abstracoes para Anthropic (Claude) e OpenAI (GPT)
- Modo offline completo (funciona sem chave de API)
- Analise de agrupamento, sugestao de carga e tendencias

### Analise de Custos
- Estimativa de custo por tiro
- Valoracao de inventario por categoria
- Alertas de validade de insumos (90 dias)

### Seguranca
- Autenticacao com bcrypt e WebAuthn/Passkeys
- Criptografia PII com Fernet (AES-128)
- Auditoria de acesso (AuditLog)
- Rate limiting de login (5 tentativas)
- Upload S3 com restricao de MIME type

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Streamlit |
| Backend | Python 3.11+ |
| Banco de dados | PostgreSQL (producao) / SQLite (dev) |
| ORM | SQLAlchemy 2.x |
| Visao computacional | OpenCV |
| PDF | ReportLab |
| Validacao | Pydantic v2 |
| Auth | bcrypt + streamlit-passwordless |
| Storage | AWS S3 (boto3) |
| CI/CD | GitHub Actions |
| Deploy | Docker + EasyPanel |

## Instalacao

### Desenvolvimento local

```bash
# Clonar
git clone https://github.com/jvamed-debug/https-github.com-junioraredes-ballistic-pro.git
cd https-github.com-junioraredes-ballistic-pro

# Instalar dependencias (Python 3.11+)
pip install -r requirements.txt

# Executar
streamlit run app.py
```

### Docker

```bash
# Build e execucao com PostgreSQL
docker compose up -d

# Acesse em http://localhost:8501
```

### Producao (Hostinger + EasyPanel)

Consulte o guia completo em [DEPLOY.md](DEPLOY.md).

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `DATABASE_URL` | Sim | Connection string PostgreSQL |
| `FERNET_KEY` | Sim | Chave para criptografia de dados pessoais |
| `AWS_ACCESS_KEY_ID` | Nao | Upload de imagens para S3 |
| `AWS_SECRET_ACCESS_KEY` | Nao | Secret AWS |
| `S3_BUCKET` | Nao | Bucket para imagens |

Veja `.env.example` para referencia completa.

## Testes

```bash
pip install pytest
pytest tests/ -v
```

44 testes cobrindo: trajetoria balistica, servico de dados, schemas Pydantic, consultor IA (offline) e agrupamento de tiros.

## Estrutura do Projeto

```
app.py                          # Entrada principal (auth + roteamento de tabs)
core/
  auth.py                       # Autenticacao, registro, recuperacao de senha
  config.py                     # Setup do app e PWA
  models.py                     # Modelos SQLAlchemy (User, Firearm, etc.)
modules/
  ai_advisor_tab.py             # UI do consultor IA
  cost_analytics.py             # Dashboard de custos
  performance.py                # Dashboard de performance + CV
  profile.py                    # Perfil, armas, backup, alteracao de senha
  reloading_data.py             # Dados de recarga e calculadora
  trajectory.py                 # UI da trajetoria balistica
services/
  ai_advisor.py                 # Abstracoes LLM + modo offline
  ballistics_service.py         # Acesso ao catalogo de cargas
  reloading_service.py          # Custo e deducao de estoque
  s3_service.py                 # Upload/delete S3
  trajectory_service.py         # Motor de calculo de trajetoria
components/
  logbook_inventory.py          # Logbook de sessoes + inventario
ui/
  styles.py                     # Tema CSS (dark HUD tatico)
schemas.py                      # Validacao Pydantic
cv_utils.py                     # Visao computacional (OpenCV)
bio_auth.py                     # WebAuthn + biometria legada
label_gen.py                    # Etiquetas PDF para caixas
report_gen.py                   # Relatorios PDF
database.json                   # Catalogo de cargas (22+ calibres)
tests/                          # Suite de testes (pytest)
.github/workflows/ci.yml        # CI com Python 3.11/3.12
Dockerfile                      # Multi-stage build
docker-compose.yml              # App + PostgreSQL
DEPLOY.md                       # Guia de deploy EasyPanel
```

## Aviso de Seguranca

A recarga de municoes envolve riscos. Sempre cruze as informacoes deste software com os manuais oficiais dos fabricantes de polvora. Inicie sempre com a carga minima.
