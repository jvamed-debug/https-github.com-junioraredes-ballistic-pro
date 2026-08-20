import { useEffect, useState } from "react";
import { api, type Firearm, type FirearmAlert } from "../api.ts";
import { EmptyState, ErrorState, Loading } from "../ui.tsx";

const COLLECTIONS: Array<{ id: "pessoal" | "clube"; label: string }> = [
  { id: "pessoal", label: "Pessoal" },
  { id: "clube", label: "Clube" },
];

// dd/mm/aaaa a partir de ISO (aaaa-mm-dd).
function br(iso?: string | null): string {
  return iso ? iso.split("-").reverse().join("/") : "—";
}

// Estado de validade de um documento, para colorir o selo.
function docTone(iso?: string | null): "none" | "ok" | "soon" | "expired" {
  if (!iso) return "none";
  const days = Math.round((new Date(iso + "T00:00:00").getTime() - Date.now()) / 86400000);
  if (days < 0) return "expired";
  if (days <= 60) return "soon";
  return "ok";
}

function DocBadge({ label, iso }: { label: string; iso?: string | null }) {
  if (!iso) return null;
  const tone = docTone(iso);
  const cls = {
    ok: "bg-[var(--panel-2)] text-[var(--muted)]",
    soon: "bg-[var(--wind)]/20 text-[var(--wind)]",
    expired: "bg-red-500/20 text-red-400",
    none: "",
  }[tone];
  return (
    <span className={"rounded-full px-2 py-0.5 text-[0.6rem] uppercase " + cls}>
      {label} {br(iso)}{tone === "expired" ? " · vencido" : tone === "soon" ? " · vence" : ""}
    </span>
  );
}

const EMPTY = {
  model: "", collection: "pessoal" as "pessoal" | "clube", serial: "", craf: "",
  expiration: "", gts: "", gts_expiration: "", craf_doc_url: "", gts_doc_url: "",
};

export function Acervo() {
  const [list, setList] = useState<Firearm[]>([]);
  const [alerts, setAlerts] = useState<FirearmAlert[]>([]);
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
      const [guns, al] = await Promise.all([api.listFirearms(), api.firearmAlerts()]);
      setList(guns);
      setAlerts(al);
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

  function startEdit(f: Firearm) {
    setEditing(f.id);
    setForm({
      model: f.model, collection: f.collection ?? "pessoal", serial: f.serial ?? "",
      craf: f.craf ?? "", expiration: f.expiration ?? "", gts: f.gts ?? "",
      gts_expiration: f.gts_expiration ?? "", craf_doc_url: f.craf_doc_url ?? "",
      gts_doc_url: f.gts_doc_url ?? "",
    });
    setError(null);
  }

  function cancel() { setEditing(null); setForm({ ...EMPTY }); setError(null); }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const body = {
      model: form.model,
      collection: form.collection,
      serial: form.serial || null,
      craf: form.craf || null,
      expiration: form.expiration || null,
      gts: form.gts || null,
      gts_expiration: form.gts_expiration || null,
      craf_doc_url: form.craf_doc_url || null,
      gts_doc_url: form.gts_doc_url || null,
    };
    try {
      if (editing) await api.updateFirearm(editing, body);
      else await api.createFirearm(body);
      cancel();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading rows={4} label="Carregando acervo" />;
  if (loadErr) return <ErrorState message={loadErr} onRetry={load} />;

  return (
    <div className="flex flex-col gap-4">
      {alerts.length > 0 && (
        <section className="card border border-[var(--wind)]/40 p-4">
          <h2 className="mb-2 text-sm font-bold uppercase tracking-wide text-[var(--wind)]">
            ⚠️ Documentos a renovar ({alerts.length})
          </h2>
          <ul className="flex flex-col gap-1 text-sm">
            {alerts.map((a, i) => (
              <li key={i} className="flex items-center justify-between">
                <span>
                  <span className="font-semibold">{a.model}</span>
                  <span className="text-[var(--muted)]"> · {a.doc}</span>
                </span>
                <span className={a.days_left < 0 ? "text-red-400" : "text-[var(--wind)]"}>
                  {a.days_left < 0
                    ? `vencido há ${-a.days_left} dia(s)`
                    : `vence em ${a.days_left} dia(s)`}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {COLLECTIONS.map(({ id, label }) => {
        const guns = list.filter((f) => (f.collection ?? "pessoal") === id);
        return (
          <section key={id} className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
              <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
                Acervo {label}
              </h2>
              <span className="text-xs text-[var(--muted)]">{guns.length} arma(s)</span>
            </div>
            {guns.length === 0 ? (
              <p className="p-4 text-sm text-[var(--muted)]">Nenhuma arma neste acervo.</p>
            ) : (
              <ul>
                {guns.map((f) => (
                  <li key={f.id} className="flex items-start justify-between border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                    <div className="flex flex-col gap-1">
                      <div className="font-semibold">{f.model}</div>
                      <div className="flex flex-wrap gap-1">
                        <DocBadge label="CRAF" iso={f.expiration} />
                        <DocBadge label="GTS" iso={f.gts_expiration} />
                        {f.craf_doc_url && (
                          <a href={f.craf_doc_url} target="_blank" rel="noreferrer"
                            className="rounded-full bg-[var(--panel-2)] px-2 py-0.5 text-[0.6rem] uppercase text-[var(--accent)]">
                            📎 CRAF
                          </a>
                        )}
                        {f.gts_doc_url && (
                          <a href={f.gts_doc_url} target="_blank" rel="noreferrer"
                            className="rounded-full bg-[var(--panel-2)] px-2 py-0.5 text-[0.6rem] uppercase text-[var(--accent)]">
                            📎 GTS
                          </a>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <button onClick={() => startEdit(f)}
                        className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">
                        Editar
                      </button>
                      <button onClick={() => api.deleteFirearm(f.id).then(load)}
                        aria-label="Remover arma"
                        className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
                        Remover
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      })}

      {list.length === 0 && alerts.length === 0 && (
        <EmptyState icon="🔫" title="Acervo vazio" hint="Cadastre suas armas abaixo para acompanhar CRAF e GTS." />
      )}

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          {editing ? "Editar arma" : "Adicionar ao acervo"}
        </h2>
        <form onSubmit={save} className="grid grid-cols-2 gap-2">
          <input className="field col-span-2" placeholder="Modelo (ex.: Glock G25)"
            value={form.model} onChange={(e) => set("model", e.target.value)} required />
          <select className="field" value={form.collection}
            onChange={(e) => set("collection", e.target.value as "pessoal" | "clube")}>
            {COLLECTIONS.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
          </select>
          <input className="field" placeholder="Nº de série" value={form.serial}
            onChange={(e) => set("serial", e.target.value)} />
          <input className="field" placeholder="CRAF (nº)" value={form.craf}
            onChange={(e) => set("craf", e.target.value)} />
          <label className="flex flex-col text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
            Validade CRAF
            <input className="field" type="date" value={form.expiration}
              onChange={(e) => set("expiration", e.target.value)} />
          </label>
          <input className="field" placeholder="GTS (nº)" value={form.gts}
            onChange={(e) => set("gts", e.target.value)} />
          <label className="flex flex-col text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
            Validade GTS
            <input className="field" type="date" value={form.gts_expiration}
              onChange={(e) => set("gts_expiration", e.target.value)} />
          </label>
          <input className="field col-span-2" placeholder="Link do CRAF digitalizado (opcional)"
            value={form.craf_doc_url} onChange={(e) => set("craf_doc_url", e.target.value)} />
          <input className="field col-span-2" placeholder="Link do GTS digitalizado (opcional)"
            value={form.gts_doc_url} onChange={(e) => set("gts_doc_url", e.target.value)} />
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
