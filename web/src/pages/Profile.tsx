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
