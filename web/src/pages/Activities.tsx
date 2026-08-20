import { useEffect, useState } from "react";
import { api, type Activity, type ActivitySummaryRow, type Level } from "../api.ts";
import { ErrorState, Loading } from "../ui.tsx";

const GROUPS = ["Pistola", "Revólver", "Carabina", "Espingarda", "Garrucha", "Outro"];

// Início do semestre corrente (1º de jan ou 1º de jul), em ISO — para medir a
// frequência de habitualidades dentro do semestre.
function semesterStartISO(): string {
  const now = new Date();
  const month = now.getMonth() < 6 ? 0 : 6;
  return new Date(now.getFullYear(), month, 1).toISOString().slice(0, 10);
}

export function Activities() {
  const [list, setList] = useState<Activity[]>([]);
  const [summary, setSummary] = useState<ActivitySummaryRow[]>([]);
  const [lvl, setLvl] = useState<Level | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [scope, setScope] = useState<"semester" | "all">("semester");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // form
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [kind, setKind] = useState<"treino" | "competicao">("treino");
  const [category, setCategory] = useState(GROUPS[0]);
  const [caliber, setCaliber] = useState("");
  const [shots, setShots] = useState("");
  const [location, setLocation] = useState("");
  const [value, setValue] = useState("");

  async function load() {
    setLoadErr(null);
    setLoading(true);
    try {
      const since = scope === "semester" ? semesterStartISO() : undefined;
      const [l, s, lv] = await Promise.all([
        api.listActivities(),
        api.activitySummary(since),
        api.level(),
      ]);
      setList(l);
      setSummary(s);
      setLvl(lv);
    } catch (e) {
      setLoadErr(e instanceof Error ? e.message : "Falha ao carregar.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [scope]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createActivity({
        date,
        kind,
        category,
        caliber: caliber || null,
        shots: parseInt(shots) || 0,
        location: location || null,
        value: value ? parseFloat(value) : null,
      });
      setCaliber(""); setShots(""); setLocation(""); setValue("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading rows={4} label="Carregando habitualidades" />;
  if (loadErr) return <ErrorState message={loadErr} onRetry={load} />;

  const totalCount = summary.reduce((s, r) => s + r.count, 0);

  return (
    <div className="flex flex-col gap-4">
      {lvl && (
        <section className="card p-4">
          <div className="mb-2 flex items-end justify-between">
            <div>
              <div className="text-xs uppercase tracking-wide text-[var(--muted)]">Seu nível</div>
              <div className="text-lg font-bold">
                <span className="text-[var(--accent)]">Nível {lvl.level}</span> · {lvl.title}
              </div>
            </div>
            {lvl.next_title && (
              <div className="text-right text-xs text-[var(--muted)]">
                Próximo: <span className="font-semibold text-[var(--fg)]">{lvl.next_title}</span>
                {lvl.next_min != null && (
                  <div>faltam {Math.max(lvl.next_min - lvl.total_activities, 0)} habitualidade(s)</div>
                )}
              </div>
            )}
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--panel-2)]">
            <div
              className="h-full rounded-full bg-[var(--accent)] transition-all"
              style={{ width: `${Math.round(lvl.progress * 100)}%` }}
            />
          </div>
          <div className="mt-3 grid grid-cols-4 gap-2 text-center">
            {[
              ["Habitualidades", lvl.total_activities],
              ["Tiros", lvl.total_shots],
              ["Competições", lvl.competitions],
              ["Categorias", lvl.categories],
            ].map(([label, val]) => (
              <div key={label as string} className="rounded-lg bg-[var(--panel-2)] p-2">
                <div className="tabnum text-base font-bold">{val as number}</div>
                <div className="text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">{label}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
            Frequência por equipamento
          </h2>
          <div className="flex gap-1 text-xs">
            {(["semester", "all"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setScope(s)}
                className={"rounded-md px-2 py-1 " + (scope === s ? "bg-[var(--panel-2)] text-white" : "text-[var(--muted)]")}
              >
                {s === "semester" ? "Semestre" : "Tudo"}
              </button>
            ))}
          </div>
        </div>
        {summary.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            Nenhuma habitualidade {scope === "semester" ? "neste semestre" : "registrada"} ainda.
          </p>
        ) : (
          <>
            <div className="mb-2 text-xs text-[var(--muted)]">
              {totalCount} habitualidade(s) {scope === "semester" ? "no semestre" : "no total"}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full tabnum text-sm">
                <thead>
                  <tr className="text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
                    <th className="px-2 py-1 text-left">Grupo · Calibre</th>
                    <th className="px-2 py-1 text-right">Qtd</th>
                    <th className="px-2 py-1 text-right">Tiros</th>
                    <th className="px-2 py-1 text-right">Última</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.map((r, i) => (
                    <tr key={i} className="border-t border-[var(--border)]">
                      <td className="px-2 py-1">
                        <span className="font-semibold">{r.category}</span>
                        {r.caliber && <span className="text-[var(--muted)]"> · {r.caliber}</span>}
                      </td>
                      <td className="px-2 py-1 text-right font-bold text-[var(--accent)]">{r.count}</td>
                      <td className="px-2 py-1 text-right">{r.shots}</td>
                      <td className="px-2 py-1 text-right text-[var(--muted)]">
                        {r.last_date ? r.last_date.split("-").reverse().join("/") : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Registrar habitualidade
        </h2>
        <form onSubmit={add} className="grid grid-cols-2 gap-2">
          <input className="field" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          <select className="field" value={kind} onChange={(e) => setKind(e.target.value as "treino" | "competicao")}>
            <option value="treino">Treino</option>
            <option value="competicao">Competição</option>
          </select>
          <select className="field" value={category} onChange={(e) => setCategory(e.target.value)}>
            {GROUPS.map((g) => <option key={g}>{g}</option>)}
          </select>
          <input className="field" placeholder="Calibre (ex.: .380)" value={caliber} onChange={(e) => setCaliber(e.target.value)} />
          <input className="field" inputMode="numeric" placeholder="Tiros" value={shots} onChange={(e) => setShots(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Valor (R$, opcional)" value={value} onChange={(e) => setValue(e.target.value)} />
          <input className="field col-span-2" placeholder="Clube / local (opcional)" value={location} onChange={(e) => setLocation(e.target.value)} />
          <button className="btn col-span-2" disabled={busy}>{busy ? "…" : "REGISTRAR"}</button>
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Histórico ({list.length})
        </div>
        {list.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">Nenhuma habitualidade registrada.</p>
        ) : (
          <ul>
            {list.map((a) => (
              <li key={a.id} className="flex items-center justify-between border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                <div>
                  <div className="font-semibold">
                    {a.category}{a.caliber ? ` · ${a.caliber}` : ""}
                    <span className={"ml-2 rounded-full px-2 py-0.5 text-[0.6rem] uppercase " + (a.kind === "competicao" ? "bg-[var(--wind)]/20 text-[var(--wind)]" : "bg-[var(--panel-2)] text-[var(--muted)]")}>
                      {a.kind === "competicao" ? "Competição" : "Treino"}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--muted)]">
                    {a.date.split("-").reverse().join("/")}
                    {a.shots ? ` · ${a.shots} tiros` : ""}
                    {a.location ? ` · ${a.location}` : ""}
                    {a.value ? ` · R$ ${a.value.toFixed(2)}` : ""}
                  </div>
                </div>
                <button
                  onClick={() => api.deleteActivity(a.id).then(load)}
                  aria-label="Remover habitualidade"
                  className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400"
                >
                  Remover
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
