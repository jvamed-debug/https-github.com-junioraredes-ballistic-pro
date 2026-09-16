// Saneamento de URL para uso em href (auditoria F4). O React escapa texto, mas
// não valida o protocolo de um href: uma URL "javascript:..." salva pelo
// usuário executaria script na origem do app ao ser clicada. safeHref só deixa
// passar esquemas seguros; para o resto devolve undefined (o <a> fica sem href
// navegável). Links relativos (/, #) e sem esquema são tratados como relativos
// pelo navegador, então são seguros.

const SAFE_SCHEMES = ["http", "https", "tel", "mailto"];

export function safeHref(url?: string | null): string | undefined {
  if (!url) return undefined;
  const t = url.trim();
  if (!t) return undefined;
  //  Relativo (mesma origem) — seguro.
  if (t.startsWith("/") || t.startsWith("#")) return t;
  const m = /^([a-zA-Z][a-zA-Z0-9+.-]*):/.exec(t);
  //  Sem esquema explícito → o navegador trata como caminho relativo; seguro.
  if (!m) return t;
  return SAFE_SCHEMES.includes(m[1].toLowerCase()) ? t : undefined;
}
