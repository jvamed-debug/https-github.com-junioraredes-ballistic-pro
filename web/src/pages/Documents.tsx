import { useEffect, useMemo, useState } from "react";
import { api, type Document, type DocumentAlert } from "../api.ts";
import { EmptyState, ErrorState, Loading } from "../ui.tsx";

// Pastas sugeridas — o campo é livre, estas só facilitam a escolha.
const FOLDERS = ["Registro", "Clube", "Apostilamento", "Laudo", "Pessoal", "Geral"];

function br(iso?: string | null): string {
  return iso ? iso.split("-").reverse().join("/") : "—";
}

function tone(iso: string | null | undefined, remind: number): "none" | "ok" | "soon" | "expired" {
  if (!iso) return "none";
  const days = Math.round((new Date(iso + "T00:00:00").getTime() - Date.now()) / 86400000);
  if (days < 0) return "expired";
  if (days <= remind) return "soon";
  return "ok";
}

const EMPTY = {
  folder: "Registro", title: "", number: "", issue_date: "",
  expiration: "", remind_days: 30, file_url: "", notes: "",
};

export function Documents() {
  const [list, setList] = useState<Document[]>([]);
  const [alerts, setAlerts] = useState<DocumentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);

  async function onUpload(file: File | null) {
    if (!file) return;
    setUploadMsg(null);
    setError(null);
    setUploading(true);
    try {
      const doc = await api.uploadDocument(file);
      const src = doc.extraction_source === "ia"
        ? "lido com IA"
        : doc.extraction_source === "heuristica"
          ? "lido automaticamente"
          : "sem texto identificável — preencha manualmente";
      const val = doc.expiration ? `, validade ${br(doc.expiration)}` : "";
      setUploadMsg(`“${doc.title}” (${src})${val}. Revise a etiqueta abaixo e ajuste se precisar.`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao enviar o PDF.");
    } finally {
      setUploading(false);
    }
  }

  async function load() {
    setLoadErr(null);
    setLoading(true);
    try {
      const [docs, al] = await Promise.all([api.listDocuments(), api.documentAlerts()]);
      setList(docs);
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

  function startEdit(d: Document) {
    setEditing(d.id);
    setForm({
      folder: d.folder, title: d.title, number: d.number ?? "",
      issue_date: d.issue_date ?? "", expiration: d.expiration ?? "",
      remind_days: d.remind_days, file_url: d.file_url ?? "", notes: d.notes ?? "",
    });
    setError(null);
  }

  function cancel() { setEditing(null); setForm({ ...EMPTY }); setError(null); }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const body = {
      folder: form.folder || "Geral",
      title: form.title,
      number: form.number || null,
      issue_date: form.issue_date || null,
      expiration: form.expiration || null,
      remind_days: Number(form.remind_days) || 0,
      file_url: form.file_url || null,
      notes: form.notes || null,
    };
    try {
      if (editing) await api.updateDocument(editing, body);
      else await api.createDocument(body);
      cancel();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  // Agrupa por pasta, preservando ordem alfabética das pastas.
  const byFolder = useMemo(() => {
    const m = new Map<string, Document[]>();
    for (const d of list) {
      const arr = m.get(d.folder) ?? [];
      arr.push(d);
      m.set(d.folder, arr);
    }
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [list]);

  if (loading) return <Loading rows={4} label="Carregando documentos" />;
  if (loadErr) return <ErrorState message={loadErr} onRetry={load} />;

  return (
    <div className="flex flex-col gap-4">
      {alerts.length > 0 && (
        <section className="card border border-[var(--wind)]/40 p-4">
          <h2 className="mb-2 text-sm font-bold uppercase tracking-wide text-[var(--wind)]">
            ⏰ Lembretes de renovação ({alerts.length})
          </h2>
          <ul className="flex flex-col gap-1 text-sm">
            {alerts.map((a) => (
              <li key={a.document_id} className="flex items-center justify-between">
                <span>
                  <span className="font-semibold">{a.title}</span>
                  <span className="text-[var(--muted)]"> · {a.folder}</span>
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

      <section className="card p-4">
        <h2 className="mb-1 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          📤 Enviar PDF
        </h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Envie o PDF do documento — o app lê número, validade e tipo, guarda o
          arquivo e cria a etiqueta com o lembrete de renovação.
        </p>
        <label className={"btn btn-ghost inline-flex cursor-pointer items-center justify-center " + (uploading ? "opacity-60" : "")}>
          {uploading ? "Lendo documento…" : "Escolher PDF"}
          <input
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            disabled={uploading}
            onChange={(e) => { onUpload(e.target.files?.[0] ?? null); e.target.value = ""; }}
          />
        </label>
        {uploadMsg && <p className="mt-2 text-sm text-emerald-400">{uploadMsg}</p>}
      </section>

      {list.length === 0 && (
        <EmptyState icon="📄" title="Nenhum documento" hint="Envie um PDF acima ou cadastre manualmente — com validade e lembrete." />
      )}

      {byFolder.map(([folder, docs]) => (
        <section key={folder} className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
              📁 {folder}
            </h2>
            <span className="text-xs text-[var(--muted)]">{docs.length} doc(s)</span>
          </div>
          <ul>
            {docs.map((d) => {
              const t = tone(d.expiration, d.remind_days);
              const badge = {
                ok: "bg-[var(--panel-2)] text-[var(--muted)]",
                soon: "bg-[var(--wind)]/20 text-[var(--wind)]",
                expired: "bg-red-500/20 text-red-400",
                none: "",
              }[t];
              return (
                <li key={d.id} className="flex items-start justify-between border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                  <div className="flex flex-col gap-1">
                    <div className="font-semibold">{d.title}</div>
                    <div className="flex flex-wrap items-center gap-1 text-xs text-[var(--muted)]">
                      {d.expiration && (
                        <span className={"rounded-full px-2 py-0.5 text-[0.6rem] uppercase " + badge}>
                          Val. {br(d.expiration)}{t === "expired" ? " · vencido" : t === "soon" ? " · renovar" : ""}
                        </span>
                      )}
                      {d.number && <span>· nº {d.number}</span>}
                      {d.file_url && (
                        <a href={d.file_url} target="_blank" rel="noreferrer"
                          className="rounded-full bg-[var(--panel-2)] px-2 py-0.5 text-[0.6rem] uppercase text-[var(--accent)]">
                          📎 Link
                        </a>
                      )}
                      {d.has_file && (
                        <button onClick={() => api.downloadDocumentFile(d.id, d.file_name)}
                          className="rounded-full bg-[var(--panel-2)] px-2 py-0.5 text-[0.6rem] uppercase text-[var(--accent)]">
                          📎 Baixar PDF
                        </button>
                      )}
                      {d.notes && <span>· {d.notes}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => startEdit(d)}
                      className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">
                      Editar
                    </button>
                    <button onClick={() => api.deleteDocument(d.id).then(load)}
                      aria-label="Remover documento"
                      className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
                      Remover
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      ))}

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          {editing ? "Editar documento" : "Adicionar documento"}
        </h2>
        <form onSubmit={save} className="grid grid-cols-2 gap-2">
          <input className="field col-span-2" placeholder="Título (ex.: CR — Colecionador)"
            value={form.title} onChange={(e) => set("title", e.target.value)} required />
          <input className="field" list="doc-folders" placeholder="Pasta"
            value={form.folder} onChange={(e) => set("folder", e.target.value)} />
          <datalist id="doc-folders">
            {FOLDERS.map((f) => <option key={f} value={f} />)}
          </datalist>
          <input className="field" placeholder="Número (opcional)"
            value={form.number} onChange={(e) => set("number", e.target.value)} />
          <label className="flex flex-col text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
            Emissão
            <input className="field" type="date" value={form.issue_date}
              onChange={(e) => set("issue_date", e.target.value)} />
          </label>
          <label className="flex flex-col text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
            Validade
            <input className="field" type="date" value={form.expiration}
              onChange={(e) => set("expiration", e.target.value)} />
          </label>
          <label className="flex flex-col text-[0.6rem] uppercase tracking-wide text-[var(--muted)] col-span-2">
            Lembrar quantos dias antes
            <input className="field" type="number" min={0} max={365} value={form.remind_days}
              onChange={(e) => set("remind_days", Number(e.target.value))} />
          </label>
          <input className="field col-span-2" placeholder="Link do arquivo digitalizado (opcional)"
            value={form.file_url} onChange={(e) => set("file_url", e.target.value)} />
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
