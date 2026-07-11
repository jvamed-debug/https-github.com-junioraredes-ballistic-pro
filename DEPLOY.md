# Deploy — Hostinger VPS + EasyPanel

## Pré-requisitos

- VPS Hostinger com EasyPanel instalado
- Acesso SSH ao servidor
- Repositório GitHub conectado ao EasyPanel
- Runtime Python 3.11 ou superior; o Dockerfile oficial utiliza Python 3.11

## 1. Configurar o Projeto no EasyPanel

1. Acesse o painel do EasyPanel (`http://SEU_IP:3000`)
2. Clique em **Create Project** → nomeie como `ballistic-pro`

## 2. Criar o Serviço de Banco de Dados

1. Dentro do projeto, clique em **+ Service** → **Postgres**
2. Configure:
   - **Name:** `db`
   - **Password:** gere uma senha forte
   - **Database:** `ballistic_db`
3. Salve e aguarde o container iniciar
4. Copie a connection string interna: `postgresql://postgres:SENHA@db.ballistic-pro.internal:5432/ballistic_db`

## 3. Criar o Serviço da Aplicação

1. Clique em **+ Service** → **App**
2. Configure:
   - **Name:** `app`
   - **Source:** GitHub → selecione o repositório `https-github.com-junioraredes-ballistic-pro`
   - **Branch:** `main`
   - **Build:** Dockerfile (detectado automaticamente)

### Variáveis de Ambiente

Em **Environment**, adicione:

| Variável | Valor |
|----------|-------|
| `DATABASE_URL` | `postgresql://postgres:SENHA@db.ballistic-pro.internal:5432/ballistic_db` |
| `FERNET_KEY` | Gere com: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

Variáveis opcionais (S3, AI):

| Variável | Descrição |
|----------|-----------|
| `AWS_ACCESS_KEY_ID` | Chave AWS para upload de imagens |
| `AWS_SECRET_ACCESS_KEY` | Secret AWS |
| `S3_BUCKET` | Nome do bucket S3 |

### Porta e Domínio

1. Em **Domains**, adicione seu domínio (ex: `app.seudominio.com.br`)
2. Em **Port**, configure `8501`
3. Ative **HTTPS** (Let's Encrypt automático)

## 4. Volumes (Persistência)

Em **Volumes**, adicione:
- **Mount path:** `/app/data` → para backups locais do SQLite

## 5. Deploy

Clique em **Deploy**. O EasyPanel vai:
1. Clonar o repositório
2. Buildar o Dockerfile (multi-stage, ~2min)
3. Iniciar o container com healthcheck

## 6. Deploy Automático

Em **Source** → ative **Auto Deploy** para rebuildar automaticamente em cada push na `main`.

## Monitoramento

- **Logs:** EasyPanel → App → Logs
- **Health:** `https://seudominio.com.br/_stcore/health`
- **Métricas:** EasyPanel → App → Monitoring (CPU/RAM)

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Container reiniciando | Verifique logs; geralmente é `DATABASE_URL` incorreta |
| Erro de conexão DB | Confirme que o serviço `db` está rodando e a connection string usa o hostname interno |
| Build lento | Normal no primeiro build (~3min); builds seguintes usam cache |
| Sem HTTPS | Verifique se o DNS do domínio aponta para o IP da VPS |
