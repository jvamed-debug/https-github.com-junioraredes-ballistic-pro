import { useEffect, useState } from "react";
import { api, type DocumentAlert, type Event, type FirearmAlert } from "../api.ts";

// Bloco de pendências do CAC para o topo do Painel: vencimentos (documentos,
// CRAF, GTS) e próximos eventos. Sempre visível — é o que o atirador precisa
// ver ao abrir o app, mesmo sem dados de recarga.

type Row = { key: string; label: string; sub: string; days: number };

function br(iso: string): string {
  return iso.split("-").reverse().join("/");
}
function daysFromToday(iso: string): number {
  return Math.round((new Date(iso + "T00:00:00").getTime() - Date.now()) / 86400000);
}

export function Pendencias() {
  const [docs, setDocs] = useState<DocumentAlert[]>([]);
  const [guns, setGuns] = useState<FirearmAlert[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.all([
      api.documentAlerts().catch(() => []),
      api.firearmAlerts().catch(() => []),
      api.listEvents(true).catch(() => []),
    ]).then(([d, g, e]) => {
      setDocs(d); setGuns(g); setEvents(e.slice(0, 3)); setLoaded(true);
    });
  }, []);

  if (!loaded) return null;

  const vencimentos: Row[] = [
    ...docs.map((d) => ({
      key: `doc:${d.document_id}`, label: d.title, sub: `${d.folder} · vence ${br(d.expiration)}`,
      days: d.days_left,
    })),
    ...guns.map((g) => ({
      key: `gun:${g.firearm_id}:${g.doc}`, label: `${g.model} · ${g.doc}`,
      sub: `vence ${br(g.expiration)}`, days: g.days_left,
    })),
  ].sort((a, b) => a.days - b.days);

  const nada = vencimentos.length === 0 && events.length === 0;

  return (
    <section className="card p-4">
      <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
        Pendências
      </h2>

      {nada ? (
        <p className="text-sm text-[var(--muted)]">✅ Tudo em dia. Nenhum vencimento ou evento próximo.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {vencimentos.length > 0 && (
            <div>
              <div className="mb-2 text-[0.6rem] uppercase tracking-wide text-[var(--wind)]">
                ⏰ Vencimentos
              </div>
              <ul className="flex flex-col gap-2">
                {vencimentos.map((r) => (
                  <li key={r.key} className="flex items-center justify-between text-sm">
                    <span className="min-w-0">
                      <span className="block truncate font-semibold">{r.label}</span>
                      <span className="text-xs text-[var(--muted)]">{r.sub}</span>
                    </span>
                    <span className={"shrink-0 rounded-full px-2 py-0.5 text-[0.6rem] uppercase " +
                      (r.days < 0 ? "bg-red-500/20 text-red-400" : "bg-[var(--wind)]/20 text-[var(--wind)]")}>
                      {r.days < 0 ? `vencido ${-r.days}d` : `${r.days}d`}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {events.length > 0 && (
            <div>
              <div className="mb-2 text-[0.6rem] uppercase tracking-wide text-[var(--accent)]">
                🏆 Próximos eventos
              </div>
              <ul className="flex flex-col gap-2">
                {events.map((e) => {
                  const d = daysFromToday(e.date);
                  return (
                    <li key={e.id} className="flex items-center justify-between text-sm">
                      <span className="min-w-0">
                        <span className="block truncate font-semibold">{e.title}</span>
                        <span className="text-xs text-[var(--muted)]">
                          {br(e.date)}{e.location ? ` · ${e.location}` : ""}
                        </span>
                      </span>
                      <span className="shrink-0 text-xs text-[var(--accent)]">
                        {d === 0 ? "hoje" : `em ${d}d`}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
