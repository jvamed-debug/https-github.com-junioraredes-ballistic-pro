"""Leitura automatica de documentos do CAC enviados em PDF.

Identifica, a partir do PDF, o que e o documento (titulo/pasta), o numero e a
validade — para preencher a etiqueta e agendar o lembrete sem digitacao.

Dois caminhos, nesta ordem:
  1. IA (quando ha ANTHROPIC_API_KEY): manda o PDF direto ao Claude, que le
     ate documentos escaneados e devolve os campos em JSON.
  2. Heuristica (sempre disponivel, sem chave/rede): extrai o texto com pypdf
     e aplica regex/palavras-chave. Cobre PDFs com texto selecionavel.

Nunca levanta excecao: em qualquer falha, devolve o que conseguiu (campos
ausentes = None) para o usuario revisar e completar.
"""

from __future__ import annotations

import base64
import json
import os
import re
from datetime import date

#  Palavras-chave -> (titulo sugerido, pasta). Ordem importa: o primeiro que
#  casar vence, entao os mais especificos vem antes.
_TYPE_HINTS: list[tuple[str, str, str]] = [
    ("craf", "CRAF", "Registro"),
    ("guia de tráfego", "Guia de Tráfego", "Transporte"),
    ("guia de trafego", "Guia de Tráfego", "Transporte"),
    ("certificado de registro", "CR — Certificado de Registro", "Registro"),
    ("apostilamento", "Apostilamento", "Apostilamento"),
    ("filiaç", "Filiação a clube", "Clube"),
    ("filiac", "Filiação a clube", "Clube"),
    ("laudo", "Laudo", "Laudo"),
    ("psicológic", "Laudo psicológico", "Laudo"),
]

_DATE_LABELS_EXP = ("valid", "vencimento", "vence", "até", "ate", "expira")
_DATE_LABELS_ISSUE = ("emiss", "expedi", "emitid")

_ALLOWED_FOLDERS = {"Registro", "Transporte", "Apostilamento", "Clube", "Laudo", "Geral"}


def _parse_br_date(s: str) -> date | None:
    s = s.strip()
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    m = re.match(r"^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _extract_text(pdf_bytes: bytes) -> str:
    try:
        import io

        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""


def parse_text_heuristic(text: str) -> dict:
    """Extrai titulo/pasta/numero/datas de um texto ja lido do PDF."""
    out: dict = {
        "title": None, "folder": "Geral", "number": None,
        "issue_date": None, "expiration": None, "source": "heuristica",
    }
    if not text or not text.strip():
        out["source"] = "vazio"
        return out

    low = text.lower()

    #  Tipo/titulo/pasta por palavra-chave.
    for needle, title, folder in _TYPE_HINTS:
        if needle in low:
            out["title"] = title
            out["folder"] = folder
            break
    if out["title"] is None:
        #  Primeira linha significativa como titulo.
        for line in text.splitlines():
            line = line.strip()
            if len(line) >= 4:
                out["title"] = line[:120]
                break

    #  Datas: coleta todas, tenta rotular por contexto da linha.
    exp: date | None = None
    issue: date | None = None
    all_dates: list[date] = []
    date_re = re.compile(r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2})\b")
    for line in text.splitlines():
        ll = line.lower()
        for token in date_re.findall(line):
            d = _parse_br_date(token)
            if not d:
                continue
            all_dates.append(d)
            if any(k in ll for k in _DATE_LABELS_EXP) and exp is None:
                exp = d
            elif any(k in ll for k in _DATE_LABELS_ISSUE) and issue is None:
                issue = d
    if exp is None and all_dates:
        exp = max(all_dates)          # sem rotulo, a mais distante costuma ser a validade
    if issue is None and all_dates:
        cand = [d for d in all_dates if d != exp]
        issue = min(cand) if cand else None
    out["expiration"] = exp.isoformat() if exp else None
    out["issue_date"] = issue.isoformat() if issue else None

    #  Numero: perto de "nº"/"numero"; o valor precisa conter digito (evita
    #  capturar palavras como REGISTRO/ARMA). Senao, a maior sequencia de
    #  digitos (aceitando prefixo tipo GT-2024-987).
    num = None
    m = re.search(
        r"\b(?:n[ºo°]|n[uú]mero)\b\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9./\-]{3,})",
        text, re.I,
    )
    if m and any(ch.isdigit() for ch in m.group(1)):
        num = m.group(1).strip(" .-")
    if not num:
        seqs = re.findall(r"\b[A-Z]{0,3}-?\d{4,}[\dA-Z./\-]*\b", text)
        if seqs:
            num = max(seqs, key=len).strip(" .-")
    out["number"] = num
    return out


def _extract_with_ai(pdf_bytes: bytes, api_key: str) -> dict | None:
    """Le o PDF com o Claude e devolve os campos, ou None se falhar."""
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        b64 = base64.standard_b64encode(pdf_bytes).decode()
        system = (
            "Você extrai metadados de documentos brasileiros de CAC "
            "(Colecionador, Atirador e Caçador). Responda APENAS com um objeto "
            "JSON, sem texto ao redor, com as chaves: title (o que é o "
            "documento, curto), folder (uma de: Registro, Transporte, "
            "Apostilamento, Clube, Laudo, Geral), number (número do documento "
            "ou null), issue_date (emissão, formato AAAA-MM-DD ou null), "
            "expiration (validade, AAAA-MM-DD ou null). Use null quando não "
            "tiver certeza; não invente."
        )
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            temperature=0,
            system=system,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {
                        "type": "base64", "media_type": "application/pdf", "data": b64,
                    }},
                    {"type": "text", "text": "Extraia os metadados deste documento."},
                ],
            }],
        )
        raw = resp.content[0].text if resp.content else ""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[raw.find("{"):]
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        folder = data.get("folder")
        return {
            "title": (data.get("title") or None),
            "folder": folder if folder in _ALLOWED_FOLDERS else "Geral",
            "number": (data.get("number") or None),
            "issue_date": (data.get("issue_date") or None),
            "expiration": (data.get("expiration") or None),
            "source": "ia",
        }
    except Exception:
        return None


def extract_fields(pdf_bytes: bytes) -> dict:
    """Campos sugeridos a partir do PDF: title, folder, number, issue_date,
    expiration, source. Tenta IA primeiro; cai para heuristica."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        ai = _extract_with_ai(pdf_bytes, api_key)
        if ai is not None:
            #  Se a IA não achou datas, tenta completar pela heurística.
            if not ai.get("expiration") or not ai.get("number"):
                h = parse_text_heuristic(_extract_text(pdf_bytes))
                ai["expiration"] = ai.get("expiration") or h.get("expiration")
                ai["issue_date"] = ai.get("issue_date") or h.get("issue_date")
                ai["number"] = ai.get("number") or h.get("number")
            return ai
    return parse_text_heuristic(_extract_text(pdf_bytes))
