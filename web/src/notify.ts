// Notificações do navegador/PWA para os lembretes de vencimento (documentos e
// CRAF/GTS do acervo). Funciona com o app instalado, sem FCM/APNs: quando o app
// abre (ou volta ao foco) e a permissão foi concedida, checamos os alertas e
// disparamos uma notificação — no máximo uma por item por dia, para não repetir.

import { api } from "./api.ts";

const PREF_KEY = "bp.notify";
const SEEN_KEY = "bp.notify.seen"; // { [chave]: "AAAA-MM-DD" }

export function notifySupported(): boolean {
  return typeof window !== "undefined" && "Notification" in window;
}

export function notifyEnabled(): boolean {
  return notifySupported() && localStorage.getItem(PREF_KEY) === "1"
    && Notification.permission === "granted";
}

export function getNotifyPref(): boolean {
  return localStorage.getItem(PREF_KEY) === "1";
}

// Pede permissão e liga a preferência. Retorna true se ficou ativo.
export async function enableNotifications(): Promise<boolean> {
  if (!notifySupported()) return false;
  let perm = Notification.permission;
  if (perm === "default") perm = await Notification.requestPermission();
  const ok = perm === "granted";
  localStorage.setItem(PREF_KEY, ok ? "1" : "0");
  return ok;
}

export function disableNotifications() {
  localStorage.setItem(PREF_KEY, "0");
}

function seenMap(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(SEEN_KEY) || "{}");
  } catch {
    return {};
  }
}

function markSeen(key: string, today: string) {
  const m = seenMap();
  m[key] = today;
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify(m));
  } catch {
    /* storage cheio/indisponível — só não deduplica */
  }
}

function fire(title: string, body: string) {
  try {
    new Notification(title, { body, tag: title, icon: "/pwa-192.png" });
  } catch {
    /* alguns navegadores exigem ServiceWorkerRegistration.showNotification;
       aqui é best-effort e silencioso se não der. */
  }
}

// Verifica os alertas e notifica os que ainda não foram avisados hoje.
export async function runAlertCheck(): Promise<void> {
  if (!notifyEnabled()) return;
  const today = new Date().toISOString().slice(0, 10);
  const seen = seenMap();
  try {
    const [docs, guns] = await Promise.all([
      api.documentAlerts().catch(() => []),
      api.firearmAlerts().catch(() => []),
    ]);
    for (const d of docs) {
      const key = `doc:${d.document_id}`;
      if (seen[key] === today) continue;
      const when = d.days_left < 0 ? `vencido há ${-d.days_left} dia(s)` : `vence em ${d.days_left} dia(s)`;
      fire("Documento a renovar", `${d.title} — ${when}`);
      markSeen(key, today);
    }
    for (const g of guns) {
      const key = `gun:${g.firearm_id}:${g.doc}`;
      if (seen[key] === today) continue;
      const when = g.days_left < 0 ? `vencido há ${-g.days_left} dia(s)` : `vence em ${g.days_left} dia(s)`;
      fire(`${g.doc} a renovar`, `${g.model} — ${when}`);
      markSeen(key, today);
    }
  } catch {
    /* offline ou sem sessão — ignora silenciosamente */
  }
}
