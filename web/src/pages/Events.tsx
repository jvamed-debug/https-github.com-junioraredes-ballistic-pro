import { useEffect, useMemo, useState } from "react";
import { api, type Event, type EventKind } from "../api.ts";
import { EmptyState, ErrorState, Loading } from "../ui.tsx";

const KINDS: Array<{ id: EventKind; label: string; icon: string }> = [
  { id: "competicao", label: "Competição", icon: "🏆" },
  { id: "curso", label: "Curso", icon: "🎓" },
  { id: "prova", label: "Prova de nível", icon: "🎯" },
  { id: "treino", label: "Treino", icon: "🔫" },
  { id: "outro", label: "Outro", icon: "📌" },
];
const KIND_MAP = Object.fromEntries(KINDS.map((k) => [k.id, k]));

function br(iso: string): string {
  return iso.split("-").reverse().join("/");
}
function daysFromToday(iso: string): number {
  return Math.round((new Date(iso + "T00:00:00").getTime() - Date.now()) / 86400000);
}
const todayISO = () => new Date().toISOString().slice(0, 10);

const EMPTY = {
  title: "", date: todayISO(), kind: "competicao" as EventKind,
  location: "", url: "", notes: "",
};

export function Events() {
  const [list, setList] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY });

  async function load() {
    setLoadErr(null);
    setLoading(true);
    try {
      setList(await api.listEvents());
    } catch (e) {
      setLoadErr(e instanceof Error ? e.message : "Falha ao carregar.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  function set<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function startEdit(ev: Event) {
    setEditing(ev.id);
    setForm({
      title: ev.title, date: ev.date, kind: ev.kind,
      location: ev.location ?? "", url: ev.url ?? "", notes: ev.notes ?? "",
    });
    setError(null);
  }

  function cancel() { setEditing(null); setForm({ ...EMPTY }); setError(null); }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const body = {
      title: form.title, date: form.date, kind: form.kind,
      location: form.location || null, url: form.url || null, notes: form.notes || null,
    };
    try {
      if (editing) await api.updateEvent(editing, body);
      else await api.createEvent(body);
      cancel();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  const { upcoming, past } = useMemo(() => {
    const t = todayISO();
    return {
      upcoming: list.filter((e) => e.date >= t),
      past: list.filter((e) => e.date < t).reverse(), // mais recentes primeiro
    };
  }, [list]);

  if (loading) return <Loading rows={4} label="Carregando agenda" />;
  if (loadErr) return <ErrorState message={loadErr} onRetry={load} />;

  const row = (ev: Event, faded = false) => {
    const k = KIND_MAP[ev.kind] ?? KIND_MAP.outro;
    const d = daysFromToday(ev.date);
    return (
      <li key={ev.id} className={"flex items-start justify-between border-t border-[var(--border)] px-4 py-3 first:border-t-0 " + (faded ? "opacity-60" : "")}>
        <div className="flex flex-col gap-1">
          <div className="font-semibold">{k.icon} {ev.title}</div>
          <div className="flex flex-wrap items-center gap-1 text-xs text-[var(--muted)]">
            <span className="rounded-full bg-[var(--panel-2)] px-2 py-0.5 text-[0.6rem] uppercase">{k.label}</span>
            <span>{br(ev.date)}</span>
            {!faded && d >= 0 && (
              <span className="text-[var(--accent)]">
                {d === 0 ? "· hoje" : `· em ${d} dia(s)`}
              </span>
            )}
            {ev.location && <span>· {ev.location}</span>}
            {ev.url && (
              <a href={ev.url} target="_blank" rel="noreferrer" className="text-[var(--accent)] underline">
                · inscrição
              </a>
            )}
          </div>
          {ev.notes && <div className="text-xs text-[var(--muted)]">{ev.notes}</div>}
        </div>
        <div className="flex gap-1">
          <button onClick={() => startEdit(ev)}
            className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">
            Editar
          </button>
          <button onClick={() => api.deleteEvent(ev.id).then(load)}
            aria-label="Remover evento"
            className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
            Remover
          </button>
        </div>
      </li>
    );
  };

  return (
    <div className="flex flex-col gap-4">
      {list.length === 0 && (
        <EmptyState icon="📅" title="Agenda vazia" hint="Cadastre competições, cursos e provas para não perder inscrição." />
      )}

      <section className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">Próximos</h2>
          <span className="text-xs text-[var(--muted)]">{upcoming.length}</span>
        </div>
        {upcoming.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">Nenhum evento futuro.</p>
        ) : (
          <ul>{upcoming.map((e) => row(e))}</ul>
        )}
      </section>

      {past.length > 0 && (
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">Passados</h2>
            <span className="text-xs text-[var(--muted)]">{past.length}</span>
          </div>
          <ul>{past.map((e) => row(e, true))}</ul>
        </section>
      )}

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          {editing ? "Editar evento" : "Adicionar à agenda"}
        </h2>
        <form onSubmit={save} className="grid grid-cols-2 gap-2">
          <input className="field col-span-2" placeholder="Título (ex.: Copa Regional IPSC)"
            value={form.title} onChange={(e) => set("title", e.target.value)} required />
          <input className="field" type="date" value={form.date}
            onChange={(e) => set("date", e.target.value)} required />
          <select className="field" value={form.kind}
            onChange={(e) => set("kind", e.target.value as EventKind)}>
            {KINDS.map((k) => <option key={k.id} value={k.id}>{k.label}</option>)}
          </select>
          <input className="field col-span-2" placeholder="Local / clube (opcional)"
            value={form.location} onChange={(e) => set("location", e.target.value)} />
          <input className="field col-span-2" placeholder="Link de inscrição/regulamento (opcional)"
            value={form.url} onChange={(e) => set("url", e.target.value)} />
          <input className="field col-span-2" placeholder="Observações (opcional)"
            value={form.notes} onChange={(e) => set("notes", e.target.value)} />
          <button className="btn col-span-2" disabled={busy}>
            {busy ? "…" : editing ? "SALVAR" : "ADICIONAR"}
          </button>
          {editing && (
            <button type="button" onClick={cancel}
              className="col-span-2 rounded-md border border-[var(--border)] py-2 text-sm text-[var(--muted)]">
              Cancelar
            </button>
          )}
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>
    </div>
  );
}
