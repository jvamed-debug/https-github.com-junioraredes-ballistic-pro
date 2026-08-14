import { useState } from "react";
import { api, type User } from "../api.ts";

export function Profile({ user, onUpdated }: { user: User; onUpdated: (u: User) => void }) {
  const [name, setName] = useState(user.name ?? "");
  const [email, setEmail] = useState(user.email ?? "");
  const [phone, setPhone] = useState(user.phone ?? "");
  const [cpf, setCpf] = useState(user.cpf ?? "");
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);

  async function downloadReport() {
    setError(null);
    setReportBusy(true);
    try {
      await api.downloadInspectionReport();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao gerar o relatório.");
    } finally {
      setReportBusy(false);
    }
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(false);
    setBusy(true);
    try {
      const updated = await api.updateProfile({
        name: name || null,
        email: email || null,
        phone: phone || null,
        cpf: cpf || null,
      });
      onUpdated(updated);
      setOk(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--panel-2)] text-lg font-bold text-[var(--accent)]">
            {(user.name || user.username).slice(0, 1).toUpperCase()}
          </div>
          <div>
            <div className="font-bold">{user.username}</div>
            <div className="text-xs text-[var(--muted)]">
              {user.is_premium ? "Premium" : "Conta gratuita"}
            </div>
          </div>
        </div>

        <form onSubmit={save} className="flex flex-col gap-3">
          <Labeled label="Nome completo">
            <input className="field" value={name} onChange={(e) => setName(e.target.value)} />
          </Labeled>
          <Labeled label="E-mail">
            <input className="field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </Labeled>
          <Labeled label="Telefone">
            <input className="field" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="(XX) XXXXX-XXXX" />
          </Labeled>
          <Labeled label="CPF">
            <input className="field" value={cpf} onChange={(e) => setCpf(e.target.value)} placeholder="somente números" />
          </Labeled>

          {error && <p className="text-sm text-red-400">{error}</p>}
          {ok && <p className="text-sm text-emerald-400">Perfil atualizado.</p>}

          <button className="btn" disabled={busy}>{busy ? "…" : "SALVAR"}</button>
        </form>
      </section>

      <section className="card p-4">
        <h2 className="mb-1 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Relatório de acervo
        </h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          PDF com seus dados de CAC, o acervo de armas e as últimas sessões de recarga.
        </p>
        <button className="btn btn-ghost" onClick={downloadReport} disabled={reportBusy}>
          {reportBusy ? "Gerando…" : "📄 Baixar relatório (PDF)"}
        </button>
      </section>
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">{label}</span>
      {children}
    </label>
  );
}
