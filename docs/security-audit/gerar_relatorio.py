#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o Relatório de Auditoria de Segurança do Ballistic Pro em PDF.

Uso (dentro do venv desta pasta):
    . .venv/bin/activate
    python gerar_relatorio.py

Saída: relatorio-auditoria-seguranca.pdf (nesta mesma pasta).
Dependências: reportlab, matplotlib (instaladas no .venv local).
"""

from __future__ import annotations

import datetime as _dt
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(HERE, "relatorio-auditoria-seguranca.pdf")

PROJETO = "Ballistic Pro"
DATA = _dt.date.today().strftime("%d/%m/%Y")

# ── Paleta por severidade (exigida no enunciado) ─────────────────────────────
SEV = {
    "Crítica": "#B91C1C",
    "Alta": "#EA580C",
    "Média": "#D97706",
    "Baixa": "#2563EB",
    "Ponto forte": "#059669",
}
TXT = "#1f2937"
MUTED = "#6b7280"
LINE = "#e5e7eb"

# ── Achados verificados ──────────────────────────────────────────────────────
# Cada achado: id, sev, cat, file, title, code, why, impact, fix, accept[]
FINDINGS = [
    {
        "id": "F1",
        "sev": "Alta",
        "cat": "Chaves/Segredos",
        "file": "api/security.py:35, 38–47",
        "title": "Segredo do JWT cai para um valor de desenvolvimento embutido, sem rejeição no startup",
        "code": (
            '_DEV_SECRET = "dev-insecure-jwt-secret-change-me"\n\n'
            "def _secret() -> str:\n"
            '    secret = os.getenv("JWT_SECRET") or os.getenv("FERNET_KEY")\n'
            "    if not secret:\n"
            '        warnings.warn("[SECURITY] ... usando segredo de desenvolvimento ...")\n'
            "        return _DEV_SECRET\n"
            "    return secret"
        ),
        "why": (
            "Se JWT_SECRET e FERNET_KEY estiverem ambos ausentes no ambiente do serviço da API, "
            "os tokens passam a ser assinados com uma constante pública presente no código-fonte. "
            "Qualquer pessoa que leia o repositório pode forjar um JWT com sub=<id de qualquer "
            "usuário> e ser autenticado como ele. Só há um warning — não há validação de startup "
            "que recuse o segredo padrão. O gatilho é plausível: a API lê apenas variáveis de "
            "ambiente; um deploy que configure a criptografia via .streamlit/secrets.toml "
            "(device_encryption_key), como sugere o próprio template do projeto, deixa a API sem "
            "FERNET_KEY/JWT_SECRET no ambiente e ativa o fallback silenciosamente."
        ),
        "impact": "Falsificação de token e tomada de conta de qualquer usuário (bypass total de autenticação).",
        "fix": (
            "Exigir JWT_SECRET explícito. No startup, recusar iniciar (raise) se o segredo resolvido "
            "for _DEV_SECRET ou vazio quando o ambiente for de produção (mesma heurística já usada em "
            "get_encryption_suite). Não derivar o segredo do JWT da chave de criptografia (ver F2)."
        ),
        "accept": [
            "A API não inicia em produção sem JWT_SECRET definido (falha explícita, não warning).",
            "O valor _DEV_SECRET nunca é aceito quando DATABASE_URL é postgres ou FERNET_KEY está setada.",
            "Teste automatizado cobre a recusa de startup com segredo ausente/padrão.",
        ],
    },
    {
        "id": "F2",
        "sev": "Média",
        "cat": "Chaves/Segredos",
        "file": "api/security.py:39",
        "title": "Chave de criptografia de PII (FERNET_KEY) reutilizada como segredo de assinatura do JWT",
        "code": 'secret = os.getenv("JWT_SECRET") or os.getenv("FERNET_KEY")',
        "why": (
            "No caminho de produção documentado, define-se FERNET_KEY e não JWT_SECRET; então o mesmo "
            "material de chave que cifra os dados sensíveis (serial, CRAF, GTS, CPF) também assina os "
            "tokens de sessão. Isso viola separação de chaves: vazamento ou rotação de uma quebra a "
            "outra, e amplia o raio de dano de qualquer exposição da FERNET_KEY."
        ),
        "impact": "Acoplamento de segredos: comprometer/rotacionar a chave de cifra afeta também toda a autenticação.",
        "fix": (
            "Definir sempre JWT_SECRET próprio (independente da FERNET_KEY) e remover o fallback para "
            "FERNET_KEY, ou derivar subchaves distintas por HKDF a partir de um segredo mestre."
        ),
        "accept": [
            "JWT_SECRET e FERNET_KEY são valores distintos em produção.",
            "O código não usa FERNET_KEY para assinar/validar JWT.",
            "DEPLOY documenta JWT_SECRET como obrigatória e separada.",
        ],
    },
    {
        "id": "F3",
        "sev": "Média",
        "cat": "Chaves/Segredos",
        "file": "core/models.py:38, 720; docker-compose.yml",
        "title": "Segredos e credenciais padrão embutidos (blind index dev, admin padrão, DB postgres:postgres)",
        "code": (
            '# core/models.py:38  (chave do blind index)\n'
            'raw = "ballistic-pro-dev-blind-index"\n\n'
            '# core/models.py:720  (senha do admin criado no 1º boot)\n'
            'admin_pass = "ballistic_admin_2025!"   # user "atirador_pro"\n\n'
            '# docker-compose.yml  (defaults ${VAR:-...})\n'
            'DATABASE_URL=...postgres:postgres@db:5432/...\n'
            'POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}'
        ),
        "why": (
            "São defaults do tipo ${VAR:-valor} ou constantes de código que viram segredo real se não "
            "forem sobrescritos. A criação do admin padrão e a cifra têm trava de produção "
            "(is_production), mas a chave do blind index e as credenciais do Postgres não são recusadas "
            "no startup. O admin é criado pelo app Streamlit (app.py) e, como API e Streamlit "
            "compartilham o mesmo banco, o usuário 'atirador_pro' com senha conhecida fica logável "
            "também pela API se o app subir em modo não-produção contra um banco alcançável."
        ),
        "impact": (
            "Login com credencial padrão conhecida; se a porta do Postgres for exposta, acesso direto ao "
            "banco com postgres:postgres; blind index previsível enfraquece a unicidade/pesquisa cifrada."
        ),
        "fix": (
            "Recusar startup em produção quando o blind index/DB usarem os defaults; remover a senha de "
            "admin embutida (exigir ADMIN_PASSWORD sempre); documentar POSTGRES_PASSWORD forte e nunca "
            "expor a porta 5432 publicamente."
        ),
        "accept": [
            "Nenhum default de segredo/credencial é aceito quando o ambiente é de produção.",
            "O admin padrão não é criado sem ADMIN_PASSWORD explícito (em qualquer modo).",
            "docker-compose não traz senha de banco default utilizável; .env obrigatório.",
        ],
    },
    {
        "id": "F4",
        "sev": "Baixa",
        "cat": "XSS",
        "file": "web/src/pages/Places.tsx:132; Events.tsx:112; Documents.tsx:209; Acervo.tsx:164,170",
        "title": "URLs controladas pelo usuário em href sem allowlist de protocolo (self-XSS)",
        "code": (
            "// Places.tsx\n"
            '<a href={p.url} target="_blank" rel="noreferrer">site</a>\n'
            "// Acervo.tsx\n"
            '<a href={f.craf_doc_url} ...>CRAF</a>   <a href={f.gts_doc_url} ...>GTS</a>\n'
            "// Documents.tsx: href={d.file_url}   // Events.tsx: href={ev.url}"
        ),
        "why": (
            "O React escapa texto, mas não sanitiza o protocolo de href. O usuário pode salvar "
            "'javascript:...' nos campos de link (site do local, URL do evento, link do documento/CRAF/"
            "GTS). Ao clicar, o script executa na origem do app. Hoje esses registros são exibidos apenas "
            "na sessão do próprio dono (dados de um único inquilino), então é self-XSS."
        ),
        "impact": (
            "Execução de script na origem do app ao clicar no link. Baixa por ser self-XSS; sobe para "
            "stored-XSS contra terceiros se os registros passarem a ser compartilhados (ex.: acervo de "
            "clube) ou exibidos em telas administrativas/relatórios de outro usuário."
        ),
        "fix": (
            "Criar um helper safeHref(url) que só aceita http/https/tel/mailto e devolve undefined caso "
            "contrário; aplicar em todos os href de dado do usuário. Opcional: validar o protocolo também "
            "no backend ao salvar."
        ),
        "accept": [
            "Um helper de saneamento de URL é aplicado em todos os href de dado do usuário.",
            "Links com esquema javascript:/data: não são renderizados como href navegável.",
            "Teste cobre que um valor 'javascript:...' não vira href ativo.",
        ],
    },
    {
        "id": "F5",
        "sev": "Baixa",
        "cat": "Configuração/CORS",
        "file": "api/main.py:43–50",
        "title": "CORS liberado com '*' por padrão",
        "code": (
            '_origins = os.getenv("API_CORS_ORIGINS", "*")\n'
            'allow_origins = ["*"] if _origins.strip() == "*" else [...]\n'
            'app.add_middleware(CORSMiddleware, allow_origins=allow_origins,\n'
            '    allow_credentials=_origins.strip() != "*", allow_methods=["*"], ...)'
        ),
        "why": (
            "O default abre a API para qualquer origem. O risco é limitado porque a autenticação é por "
            "Bearer token (não cookie) e allow_credentials fica desligado quando origem é '*', então um "
            "site malicioso não lê o token da vítima. Ainda assim, expõe a superfície da API a chamadas "
            "de qualquer origem e é uma configuração insegura por padrão."
        ),
        "impact": "Superfície de API acessível de qualquer origem no navegador; hardening pendente.",
        "fix": "Definir API_CORS_ORIGINS com a lista de origens do frontend em produção e recusar '*' quando em produção.",
        "accept": [
            "Em produção, API_CORS_ORIGINS traz apenas as origens confiáveis do app.",
            "O default '*' é recusado (ou logado como erro) quando o ambiente é de produção.",
        ],
    },
]

STRENGTHS = [
    ("Isolamento por dono em todos os routers de dados",
     "data.py, activities.py, documents.py, events.py, places.py, dope.py, backup.py, insights.py e "
     "reports.py filtram toda listagem/agregação por filter_by(user_id=current['id']). Não há RLS "
     "(não é Supabase); o mecanismo é filtro manual por user_id + helper _owned_or_404."),
    ("IDOR fechado no padrão _owned_or_404",
     "Toda rota que busca/edita/apaga objeto por ID (PUT/DELETE de firearms, documents, events, places, "
     "dope-cards; download de documento e etiqueta de logbook) verifica posse e responde 404 para objeto "
     "alheio. Referências cruzadas (firearm_id em activities/dope/logbook) revalidam a posse da arma."),
    ("Cobertura de testes de isolamento",
     "Há testes test_*_isolation / firearm_must_belong_to_user em test_api_data, _activities, _documents, "
     "_events, _places, _dope, _backup, _reports — cross-user PUT/DELETE retorna 404."),
    ("Sem superfície de privilégio no cliente",
     "Não há operação administrativa/por papel no app. is_premium é apenas rótulo de exibição "
     "(Profile.tsx). Logo, não existe gate de permissão só-no-navegador a ser burlado (categoria 2 = N/A)."),
    ("Recuperação de senha robusta",
     "PasswordReset guarda só o hash SHA-256 do token, com expiração de 1h e uso único; resposta sempre "
     "genérica (anti-enumeração). Senhas via bcrypt; lockout de força-bruta persistido no servidor."),
    ("PII cifrada em repouso, com trava de produção",
     "EncryptedString (Fernet) cifra serial/CRAF/GTS/CPF/e-mail; get_encryption_suite RECUSA iniciar em "
     "produção sem chave. Campos pesquisáveis usam blind index HMAC."),
    ("WebAuthn correto",
     "Servidor guarda apenas a chave pública; desafio de uso único com TTL de 10 min; sign_count "
     "verificado; login/complete confere credential_id + user_id."),
    ("Sem segredos versionados e sem chave no bundle",
     ".env.example e secrets.toml.template só têm placeholders; nenhuma FERNET/JWT/AWS/Resend real no "
     "histórico git; o bundle do frontend não embute chaves (usa VITE_API_URL para a base)."),
    ("Sem vetores clássicos de XSS",
     "Nenhum dangerouslySetInnerHTML/innerHTML/eval no frontend; React escapa por padrão. E-mails são "
     "enviados como texto puro (services/mailer.py), sem HTML com input do usuário."),
]

RECS = [
    ("P1", "Alta",
     "Tornar JWT_SECRET obrigatório e recusar startup com o segredo de desenvolvimento (F1). "
     "Parar de reutilizar FERNET_KEY para assinar JWT (F2)."),
    ("P2", "Média",
     "Eliminar defaults de segredo/credencial (F3): remover senha de admin embutida, recusar blind "
     "index/DB padrão em produção, senha forte de Postgres e porta não exposta."),
    ("P3", "Baixa",
     "Sanear URLs de usuário em href com allowlist de protocolo (F4) e restringir CORS a origens "
     "confiáveis em produção (F5)."),
]

# ── Gráficos (matplotlib) ────────────────────────────────────────────────────
def _fig_donut(path: str) -> None:
    order = ["Crítica", "Alta", "Média", "Baixa"]
    counts = {k: sum(1 for f in FINDINGS if f["sev"] == k) for k in order}
    labels = [k for k in order if counts[k] > 0]
    vals = [counts[k] for k in labels]
    cols = [SEV[k] for k in labels]
    fig, ax = plt.subplots(figsize=(3.6, 3.6), dpi=200)
    wedges, _ = ax.pie(vals, colors=cols, startangle=90,
                       wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
    ax.text(0, 0, f"{sum(vals)}\nachados", ha="center", va="center",
            fontsize=13, fontweight="bold", color=TXT)
    ax.legend(wedges, [f"{k} ({counts[k]})" for k in labels],
              loc="center", bbox_to_anchor=(0.5, -0.12), ncol=2,
              frameon=False, fontsize=8)
    ax.set(aspect="equal")
    fig.tight_layout()
    fig.savefig(path, transparent=True, bbox_inches="tight")
    plt.close(fig)


def _fig_bars(path: str) -> None:
    cats = ["Isolamento", "Perm. navegador", "IDOR", "Chaves/Segredos", "XSS", "Config./CORS"]
    keymap = {
        "Isolamento": 0, "Perm. navegador": 0, "IDOR": 0,
        "Chaves/Segredos": sum(1 for f in FINDINGS if f["cat"] == "Chaves/Segredos"),
        "XSS": sum(1 for f in FINDINGS if f["cat"] == "XSS"),
        "Config./CORS": sum(1 for f in FINDINGS if f["cat"] == "Configuração/CORS"),
    }
    vals = [keymap[c] for c in cats]
    fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=200)
    bars = ax.bar(cats, vals, color=["#059669", "#059669", "#059669", "#D97706", "#2563EB", "#2563EB"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, str(v),
                ha="center", va="bottom", fontsize=9, fontweight="bold", color=TXT)
    ax.set_ylim(0, max(vals) + 1)
    ax.set_ylabel("Achados", fontsize=9)
    ax.tick_params(axis="x", labelsize=8, rotation=20)
    ax.tick_params(axis="y", labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=LINE, linewidth=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, transparent=True, bbox_inches="tight")
    plt.close(fig)


# ── Estilos ──────────────────────────────────────────────────────────────────
def _styles():
    ss = getSampleStyleSheet()
    base = "Helvetica"
    styles = {
        "h1": ParagraphStyle("h1", parent=ss["Title"], fontName="Helvetica-Bold",
                             fontSize=22, textColor=colors.HexColor(TXT), leading=26, spaceAfter=6),
        "sub": ParagraphStyle("sub", fontName=base, fontSize=11, textColor=colors.HexColor(MUTED),
                              leading=15, alignment=TA_CENTER),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14,
                             textColor=colors.HexColor("#111827"), leading=18, spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11,
                             textColor=colors.HexColor(TXT), leading=14, spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", fontName=base, fontSize=9.3, textColor=colors.HexColor(TXT),
                               leading=13, alignment=TA_LEFT, spaceAfter=3),
        "small": ParagraphStyle("small", fontName=base, fontSize=8, textColor=colors.HexColor(MUTED),
                                leading=11),
        "cell": ParagraphStyle("cell", fontName=base, fontSize=8.2, textColor=colors.HexColor(TXT),
                               leading=10.5),
        "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.2,
                                textColor=colors.HexColor(TXT), leading=10.5),
        "chip": ParagraphStyle("chip", fontName="Helvetica-Bold", fontSize=8,
                               textColor=colors.white, alignment=TA_CENTER, leading=10),
        "code": ParagraphStyle("code", fontName="Courier", fontSize=7.4,
                               textColor=colors.HexColor("#111827"), leading=9.4),
    }
    return styles


def _chip(sev, styles):
    t = Table([[Paragraph(sev, styles["chip"])]], colWidths=[2.1 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(SEV[sev])),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


# ── Cabeçalho/rodapé ─────────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(2 * cm, h - 1.15 * cm, f"Relatório de Auditoria de Segurança — {PROJETO}")
    canvas.drawRightString(w - 2 * cm, h - 1.15 * cm, DATA)
    canvas.setStrokeColor(colors.HexColor(LINE))
    canvas.line(2 * cm, h - 1.3 * cm, w - 2 * cm, h - 1.3 * cm)
    canvas.line(2 * cm, 1.3 * cm, w - 2 * cm, 1.3 * cm)
    canvas.drawString(2 * cm, 1.0 * cm, "Confidencial")
    canvas.drawRightString(w - 2 * cm, 1.0 * cm, f"Página {doc.page}")
    canvas.restoreState()


def build():
    donut = os.path.join(HERE, "_donut.png")
    bars = os.path.join(HERE, "_bars.png")
    _fig_donut(donut)
    _fig_bars(bars)

    styles = _styles()
    doc = BaseDocTemplate(
        OUT_PDF, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Relatório de Auditoria de Segurança — {PROJETO}", author="Auditoria automatizada",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=_header_footer)])

    from reportlab.platypus import Image, PageBreak
    story = []

    # ── a) CAPA ──
    story += [Spacer(1, 3.2 * cm)]
    story += [Paragraph(f"Relatório de Auditoria de Segurança — {PROJETO}", styles["h1"])]
    story += [Spacer(1, 0.3 * cm)]
    story += [Paragraph(f"Data: {DATA}", styles["sub"])]
    story += [Spacer(1, 0.8 * cm)]
    escopo = (
        "<b>Escopo auditado:</b> API FastAPI (api/), núcleo compartilhado (core/, services/, schemas.py), "
        "app Streamlit (app.py) e frontend React/PWA (web/), além dos arquivos de deploy "
        "(Dockerfile*, docker-compose.yml) e do pipeline de CI (.github/workflows/ci.yml)."
    )
    story += [Paragraph(escopo, styles["body"])]
    story += [Spacer(1, 0.3 * cm)]
    metod = (
        "<b>Nota metodológica — stack detectada e mapeamento das categorias:</b><br/>"
        "Backend Python <b>FastAPI</b> + <b>SQLAlchemy</b> (ORM), auth por <b>JWT</b> (PyJWT/HS256) sobre "
        "<b>bcrypt</b>, PII cifrada com <b>Fernet</b> e blind index HMAC. Frontend <b>React 18 + Vite + "
        "TypeScript</b> (PWA). Deploy <b>Docker/EasyPanel</b>; CI em GitHub Actions. Não há Supabase/RLS.<br/>"
        "1) <b>Banco sem tranca</b> → isolamento é filtro manual por <b>user_id</b> (+ helper _owned_or_404); "
        "verificou-se sua presença em toda listagem/agregação/exportação. "
        "2) <b>Permissão no navegador</b> → cruzou-se todo gate de UI com o endpoint; não há operação por "
        "papel (is_premium é só rótulo). "
        "3) <b>IDOR</b> → percorreu-se todo handler que recebe ID (path/body). "
        "4) <b>Chaves expostas</b> → código, configs, docker-compose, CI, templates e histórico git. "
        "5) <b>XSS</b> → href/innerHTML/eval no frontend e HTML/e-mail no backend."
    )
    story += [Paragraph(metod, styles["body"])]
    story += [PageBreak()]

    # ── b) RESUMO EXECUTIVO ──
    story += [Paragraph("Resumo executivo", styles["h2"])]
    n = len(FINDINGS)
    by = {k: sum(1 for f in FINDINGS if f["sev"] == k) for k in ["Crítica", "Alta", "Média", "Baixa"]}
    resumo = (
        f"A auditoria cobriu as 5 categorias solicitadas, arquivo por arquivo. Foram confirmados "
        f"<b>{n} achados</b>: {by['Crítica']} crítica(s), {by['Alta']} alta(s), {by['Média']} média(s) e "
        f"{by['Baixa']} baixa(s). As categorias de <b>isolamento de dono</b>, <b>permissão no servidor</b> "
        f"e <b>IDOR</b> não geraram achados — o backend aplica filtro por user_id e o padrão _owned_or_404 "
        f"de forma consistente e testada. Os riscos concentram-se em <b>gestão de segredos/defaults</b> "
        f"(assinatura do JWT) e em <b>hardening</b> (URLs em href e CORS)."
    )
    story += [Paragraph(resumo, styles["body"])]
    story += [Spacer(1, 0.2 * cm)]

    imgs = Table(
        [[Image(donut, width=7.0 * cm, height=7.0 * cm),
          Image(bars, width=9.2 * cm, height=4.3 * cm)]],
        colWidths=[7.6 * cm, 9.4 * cm])
    imgs.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [imgs]
    story += [Paragraph("Esquerda: achados por severidade. Direita: achados por categoria auditada.",
                        styles["small"])]
    story += [PageBreak()]

    # ── c) PONTOS FORTES / FRACOS ──
    story += [Paragraph("Pontos fortes (o que está protegido)", styles["h2"])]
    for titulo, desc in STRENGTHS:
        story += [Paragraph(f"<font color='{SEV['Ponto forte']}'>✓</font> <b>{titulo}</b>", styles["h3"])]
        story += [Paragraph(desc, styles["body"])]
    story += [Spacer(1, 0.2 * cm)]
    story += [Paragraph("Pontos fracos (riscos centrais)", styles["h2"])]
    fracos = (
        "O eixo de maior risco é a <b>assinatura do JWT</b>: há um segredo de desenvolvimento embutido como "
        "fallback silencioso (F1) e, no caminho de produção documentado, a própria chave de criptografia é "
        "reutilizada para assinar tokens (F2). Em segundo plano, há <b>defaults de segredo/credencial</b> "
        "(F3) que só não viram brecha porque dependem de sobrescrita. Por fim, itens de <b>hardening</b>: "
        "URLs de usuário em href sem allowlist (F4, hoje self-XSS) e CORS '*' padrão (F5)."
    )
    story += [Paragraph(fracos, styles["body"])]
    story += [PageBreak()]

    # ── d) TABELA DE ACHADOS ──
    story += [Paragraph("Achados detalhados", styles["h2"])]
    header = [Paragraph("Sev.", styles["cellb"]), Paragraph("Arquivo:linha", styles["cellb"]),
              Paragraph("Descrição", styles["cellb"])]
    rows = [header]
    for f in FINDINGS:
        rows.append([
            _chip(f["sev"], styles),
            Paragraph(f"<b>{f['id']}</b><br/>{f['file']}", styles["cell"]),
            Paragraph(f"<b>{f['title']}</b>", styles["cell"]),
        ])
    tbl = Table(rows, colWidths=[2.4 * cm, 5.3 * cm, 9.3 * cm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(LINE)),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [tbl, Spacer(1, 0.3 * cm)]

    # Detalhe por achado (categoria, por quê, impacto, evidência, correção)
    for f in FINDINGS:
        story += [Paragraph(f"{f['id']} — {f['title']}", styles["h3"])]
        meta = Table([[_chip(f["sev"], styles),
                       Paragraph(f"<b>Categoria:</b> {f['cat']} &nbsp;·&nbsp; <b>Local:</b> {f['file']}",
                                 styles["cell"])]], colWidths=[2.4 * cm, 14.6 * cm])
        meta.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story += [meta]
        story += [Paragraph(f"<b>Por que é explorável:</b> {f['why']}", styles["body"])]
        story += [Paragraph(f"<b>Impacto:</b> {f['impact']}", styles["body"])]
        story += [Paragraph("<b>Evidência:</b>", styles["body"])]
        story += [_code_block(f["code"], styles)]
        story += [Paragraph(f"<b>Correção sugerida:</b> {f['fix']}", styles["body"])]
        story += [Spacer(1, 0.25 * cm)]
    story += [PageBreak()]

    # ── e) RECOMENDAÇÕES PRIORIZADAS ──
    story += [Paragraph("Recomendações priorizadas", styles["h2"])]
    rr = [[Paragraph("Prioridade", styles["cellb"]), Paragraph("Sev.", styles["cellb"]),
           Paragraph("Ação", styles["cellb"])]]
    for pri, sev, txt in RECS:
        rr.append([Paragraph(f"<b>{pri}</b>", styles["cell"]), _chip(sev, styles),
                   Paragraph(txt, styles["cell"])])
    tr = Table(rr, colWidths=[2.3 * cm, 2.4 * cm, 12.3 * cm], repeatRows=1)
    tr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(LINE)),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [tr, PageBreak()]

    # ── f) ISSUES PARA O GITHUB ──
    story += [Paragraph("Issues para o GitHub", styles["h2"])]
    story += [Paragraph(
        "Cada bloco abaixo é o texto completo de uma issue, pronto para copiar e colar. Achados de "
        "segredos afins (F1–F3) foram agrupados numa issue única para não gerar spam.", styles["body"])]
    for md in _issues_markdown():
        story += [_code_block(md, styles, bg="#f8fafc")]
        story += [Spacer(1, 0.3 * cm)]

    doc.build(story)
    for p in (donut, bars):
        try:
            os.remove(p)
        except OSError:
            pass


def _wrap(text: str, width: int = 96):
    out = []
    for line in text.split("\n"):
        while len(line) > width:
            cut = line.rfind(" ", 0, width)
            cut = cut if cut > 40 else width
            out.append(line[:cut])
            line = line[cut:].lstrip()
        out.append(line)
    return "\n".join(out)


def _code_block(text, styles, bg="#f3f4f6"):
    pf = Preformatted(_wrap(text), styles["code"])
    t = Table([[pf]], colWidths=[17.0 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor(LINE)),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _issues_markdown():
    blocks = []
    # Issue 1: agrupa F1, F2, F3 (segredos)
    b1 = f"""--- ISSUE 1 ---
# [Segurança] Endurecer a gestão de segredos: JWT, chave de cifra e defaults

**Labels:** security, alta

## Problema
Três pontos ligados a segredos/credenciais:
- **F1 (api/security.py:35,38-47):** o segredo do JWT cai para a constante
  embutida `dev-insecure-jwt-secret-change-me` quando `JWT_SECRET` e
  `FERNET_KEY` estao ausentes no ambiente da API — apenas com um warning, sem
  recusar o startup. A API le so variaveis de ambiente; configurar a cifra via
  .streamlit/secrets.toml (como sugere o template) deixa a API sem as chaves e
  ativa o fallback. Com o segredo publico, qualquer um forja um JWT (sub = id de
  qualquer usuario) e assume a conta.
- **F2 (api/security.py:39):** `secret = getenv("JWT_SECRET") or getenv("FERNET_KEY")`
  reutiliza a chave de cifra de PII para assinar o JWT (sem separacao de chaves).
- **F3 (core/models.py:38,720; docker-compose.yml):** defaults embutidos — blind
  index `ballistic-pro-dev-blind-index`, senha do admin `ballistic_admin_2025!`
  (user `atirador_pro`) e Postgres `postgres:postgres`.

## Evidencia
- api/security.py:35  `_DEV_SECRET = "dev-insecure-jwt-secret-change-me"`
- api/security.py:39  `secret = os.getenv("JWT_SECRET") or os.getenv("FERNET_KEY")`
- core/models.py:720  `admin_pass = "ballistic_admin_2025!"`
- docker-compose.yml   `POSTGRES_PASSWORD=${{POSTGRES_PASSWORD:-postgres}}`

## Impacto
Falsificacao de token / tomada de conta (F1); acoplamento de segredos (F2);
login com credencial padrao e acesso ao banco com senha default (F3).

## Correcao sugerida
- Exigir `JWT_SECRET` proprio e distinto; no startup, **recusar iniciar** se o
  segredo resolvido for o default ou vazio em producao (reusar a heuristica
  is_production de get_encryption_suite). Nao derivar o JWT da FERNET_KEY.
- Remover a senha de admin embutida (exigir ADMIN_PASSWORD sempre) e recusar os
  defaults de blind index/Postgres em producao. Nunca expor a porta 5432.

## Criterios de aceite
- [ ] API nao inicia em producao sem JWT_SECRET (falha explicita, nao warning).
- [ ] `_DEV_SECRET` nunca e usado quando ha DATABASE_URL postgres ou FERNET_KEY.
- [ ] JWT_SECRET e FERNET_KEY sao valores distintos; o codigo nao assina JWT com FERNET_KEY.
- [ ] Admin padrao nao e criado sem ADMIN_PASSWORD; sem credenciais default utilizaveis no compose.
- [ ] Teste cobre a recusa de startup com segredo ausente/padrao.
--- FIM ISSUE 1 ---"""
    blocks.append(b1)

    b2 = """--- ISSUE 2 ---
# [Seguranca] Sanear URLs de usuario em href (allowlist de protocolo)

**Labels:** security, baixa

## Problema
Campos de link controlados pelo usuario sao renderizados direto em `href`, sem
validar o protocolo. Um valor `javascript:...` executa script na origem do app
ao ser clicado. Hoje os registros sao vistos so pelo proprio dono (self-XSS),
mas vira stored-XSS contra terceiros se houver compartilhamento (ex.: acervo de
clube) ou telas administrativas.

## Evidencia
- web/src/pages/Places.tsx:132   `<a href={p.url}>`
- web/src/pages/Events.tsx:112    `<a href={ev.url}>`
- web/src/pages/Documents.tsx:209 `<a href={d.file_url}>`
- web/src/pages/Acervo.tsx:164,170 `<a href={f.craf_doc_url}>` / `{f.gts_doc_url}`

## Impacto
Execucao de script na origem do app ao clicar; escalada a XSS armazenado se os
dados passarem a ser exibidos para outros usuarios.

## Correcao sugerida
Criar `safeHref(url)` que so aceita `http/https/tel/mailto` (devolve undefined
caso contrario) e aplicar em todos os href de dado do usuario. Opcional: validar
o protocolo tambem no backend ao salvar.

## Criterios de aceite
- [ ] Helper de saneamento aplicado em todos os href de dado do usuario.
- [ ] URLs `javascript:`/`data:` nao viram href navegavel.
- [ ] Teste cobre que `javascript:...` nao gera href ativo.
--- FIM ISSUE 2 ---"""
    blocks.append(b2)

    b3 = """--- ISSUE 3 ---
# [Seguranca] Restringir CORS a origens confiaveis em producao

**Labels:** security, baixa

## Problema
`API_CORS_ORIGINS` tem default `*` (api/main.py:43-50), abrindo a API para
qualquer origem. O risco e limitado porque a auth e por Bearer token (nao
cookie) e allow_credentials fica off com `*`, mas e uma config insegura por
padrao.

## Evidencia
- api/main.py:43  `_origins = os.getenv("API_CORS_ORIGINS", "*")`
- api/main.py:49  `allow_credentials=_origins.strip() != "*"`

## Impacto
Superficie de API acessivel de qualquer origem no navegador; hardening pendente.

## Correcao sugerida
Definir `API_CORS_ORIGINS` com as origens do frontend em producao e recusar `*`
(ou logar como erro) quando o ambiente for de producao.

## Criterios de aceite
- [ ] Em producao, apenas origens confiaveis sao aceitas.
- [ ] O default `*` e recusado/alertado quando o ambiente e de producao.
--- FIM ISSUE 3 ---"""
    blocks.append(b3)
    return blocks


if __name__ == "__main__":
    build()
    print(f"PDF gerado em: {OUT_PDF}")
