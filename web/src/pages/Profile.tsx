import { useEffect, useState } from "react";
import { api, type User } from "../api.ts";
import { startRegistration, supportsWebAuthn } from "../webauthn.ts";
import {
  applyLayout, applyTheme, getTheme, LAYOUTS, THEMES,
  type Layout, type Theme,
} from "../theme.ts";
import {
  disableNotifications, enableNotifications, getNotifyPref,
  notifyEnabled, notifySupported,
} from "../notify.ts";

export function Profile({ user, onUpdated, layout, onLayoutChange }: {
  user: User;
  onUpdated: (u: User) => void;
  layout: Layout;
  onLayoutChange: (l: Layout) => void;
}) {
  const [theme, setTheme] = useState<Theme>(getTheme());
  const [notify, setNotify] = useState<boolean>(() => notifyEnabled());
  const [notifyMsg, setNotifyMsg] = useState<string | null>(null);

  async function toggleNotify() {
    setNotifyMsg(null);
    if (notify || getNotifyPref()) {
      disableNotifications();
      setNotify(false);
      return;
    }
    const ok = await enableNotifications();
    setNotify(ok);
    if (!ok) {
      setNotifyMsg(
        notifySupported()
          ? "Permissão de notificações negada. Habilite nas configurações do navegador."
          : "Este navegador não suporta notificações.",
      );
    }
  }
  const [name, setName] = useState(user.name ?? "");
  const [email, setEmail] = useState(user.email ?? "");
  const [phone, setPhone] = useState(user.phone ?? "");
  const [cpf, setCpf] = useState(user.cpf ?? "");
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);
  const [backupBusy, setBackupBusy] = useState(false);
  const [passkeyOn, setPasskeyOn] = useState(false);
  const [passkeyBusy, setPasskeyBusy] = useState(false);
  const [passkeyMsg, setPasskeyMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!supportsWebAuthn()) return;
    api.webauthnAvailable().then((r) => setPasskeyOn(r.available)).catch(() => {});
  }, []);

  async function enablePasskey() {
    setError(null);
    setPasskeyMsg(null);
    setPasskeyBusy(true);
    try {
      const options = await api.webauthnRegisterBegin();
      const attestation = await startRegistration(options);
      await api.webauthnRegisterComplete(attestation, navigator.userAgent.slice(0, 60));
      setPasskeyMsg("Biometria ativada neste dispositivo. No próximo login, use “Entrar com biometria”.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao ativar biometria.");
    } finally {
      setPasskeyBusy(false);
    }
  }

  function chooseTheme(t: Theme) {
    setTheme(t);
    applyTheme(t);
  }
  function chooseLayout(l: Layout) {
    applyLayout(l);
    onLayoutChange(l);
  }

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

  async function downloadBackup() {
    setError(null);
    setBackupBusy(true);
    try {
      await api.downloadBackup();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao gerar o backup.");
    } finally {
      setBackupBusy(false);
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
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Aparência
        </h2>
        <div className="mb-2 text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">Tema</div>
        <div className="mb-4 flex gap-2">
          {THEMES.map((t) => (
            <button key={t.id} onClick={() => chooseTheme(t.id)}
              aria-pressed={theme === t.id}
              className={"flex flex-1 items-center gap-2 rounded-lg border px-3 py-2 text-sm " +
                (theme === t.id ? "border-[var(--accent)]" : "border-[var(--border)] text-[var(--muted)]")}>
              <span className="inline-block h-4 w-4 rounded-full" style={{ background: t.swatch }} />
              {t.label}
            </button>
          ))}
        </div>
        <div className="mb-2 text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">Layout</div>
        <div className="flex flex-col gap-2">
          {LAYOUTS.map((l) => (
            <button key={l.id} onClick={() => chooseLayout(l.id)}
              aria-pressed={layout === l.id}
              className={"rounded-lg border px-3 py-2 text-left text-sm " +
                (layout === l.id ? "border-[var(--accent)]" : "border-[var(--border)]")}>
              <span className="font-semibold">{l.label}</span>
              <span className="block text-xs text-[var(--muted)]">{l.hint}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="card p-4">
        <h2 className="mb-1 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Alertas de vencimento
        </h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Receba notificações do dispositivo quando um documento, CRAF ou GTS
          estiver perto de vencer — o app avisa ao abrir.
        </p>
        <button className="btn btn-ghost" onClick={toggleNotify}>
          {notify ? "🔔 Notificações ativadas — desativar" : "🔕 Ativar notificações"}
        </button>
        {notifyMsg && <p className="mt-2 text-sm text-[var(--wind)]">{notifyMsg}</p>}
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

      <section className="card p-4">
        <h2 className="mb-1 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Backup dos dados
        </h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Baixa um arquivo JSON com tudo — acervo, documentos, habitualidades,
          eventos, locais e recargas. Guarde em local seguro: contém dados
          sensíveis (série, CRAF, GTS, CPF).
        </p>
        <button className="btn btn-ghost" onClick={downloadBackup} disabled={backupBusy}>
          {backupBusy ? "Gerando…" : "💾 Baixar backup (JSON)"}
        </button>
      </section>

      {passkeyOn && (
        <section className="card p-4">
          <h2 className="mb-1 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
            Login por biometria
          </h2>
          <p className="mb-3 text-xs text-[var(--muted)]">
            Cadastre este dispositivo (Face ID / Touch ID / digital) para entrar sem senha.
          </p>
          <button className="btn btn-ghost" onClick={enablePasskey} disabled={passkeyBusy}>
            {passkeyBusy ? "Ativando…" : "🔐 Ativar biometria neste dispositivo"}
          </button>
          {passkeyMsg && <p className="mt-2 text-sm text-emerald-400">{passkeyMsg}</p>}
        </section>
      )}
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
