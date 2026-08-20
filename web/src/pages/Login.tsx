import { useEffect, useState } from "react";
import { api, type User } from "../api.ts";
import { startAuthentication, supportsWebAuthn } from "../webauthn.ts";

type Mode = "login" | "register";

export function Login({ onAuthed }: { onAuthed: (u: User) => void }) {
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [passkeyOn, setPasskeyOn] = useState(false);
  const [forgot, setForgot] = useState(false);
  const [forgotId, setForgotId] = useState("");
  const [forgotMsg, setForgotMsg] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);

  async function submitForgot(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setForgotMsg(null);
    setDevToken(null);
    setBusy(true);
    try {
      const r = await api.forgotPassword(forgotId);
      setForgotMsg(r.detail);
      if (r.reset_token) setDevToken(r.reset_token); // só em dev (sem SMTP)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao solicitar recuperação.");
    } finally {
      setBusy(false);
    }
  }

  // Só oferece biometria se o navegador suporta e o servidor está configurado.
  useEffect(() => {
    if (!supportsWebAuthn()) return;
    api.webauthnAvailable().then((r) => setPasskeyOn(r.available)).catch(() => {});
  }, []);

  async function loginPasskey() {
    if (!username) {
      setError("Informe o usuário para entrar com biometria.");
      return;
    }
    setError(null);
    setInfo(null);
    setBusy(true);
    try {
      const options = await api.webauthnLoginBegin(username);
      const assertion = await startAuthentication(options);
      await api.webauthnLoginComplete(username, assertion);
      onAuthed(await api.me());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login por biometria.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register({
          username,
          password,
          name: name || null,
          email: email || null,
        });
        setInfo("Conta criada! Faça login.");
        setMode("login");
      } else {
        await api.login(username, password);
        const u = await api.me();
        onAuthed(u);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha inesperada.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center p-4">
      <div className="card w-full max-w-sm p-6">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-2 inline-block h-3 w-3 rounded-full bg-[var(--accent)] shadow-[0_0_12px_var(--accent)]" />
          <h1 className="text-lg font-bold tracking-wide">BALLISTIC PRO</h1>
          <p className="text-xs text-[var(--muted)]">Recarga · Balística · DOPE</p>
        </div>

        {forgot ? (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-[var(--muted)]">
              Informe seu usuário, e-mail ou telefone. Enviaremos um link para
              redefinir a senha.
            </p>
            <form onSubmit={submitForgot} className="flex flex-col gap-3">
              <input className="field" placeholder="Usuário, e-mail ou telefone"
                autoCapitalize="none" value={forgotId}
                onChange={(e) => setForgotId(e.target.value)} required />
              {error && <p className="text-sm text-red-400">{error}</p>}
              {forgotMsg && <p className="text-sm text-emerald-400">{forgotMsg}</p>}
              {devToken && (
                <a href={`/?reset=${devToken}`}
                  className="rounded-md bg-[var(--panel-2)] px-3 py-2 text-center text-sm font-semibold text-[var(--accent)]">
                  Redefinir senha agora →
                </a>
              )}
              <button className="btn" disabled={busy}>{busy ? "…" : "ENVIAR LINK"}</button>
            </form>
            <button type="button"
              onClick={() => { setForgot(false); setError(null); setForgotMsg(null); setDevToken(null); }}
              className="text-xs text-[var(--muted)] underline">
              ← Voltar ao login
            </button>
          </div>
        ) : (
        <>
        <div className="mb-4 grid grid-cols-2 gap-2">
          {(["login", "register"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setError(null); setInfo(null); }}
              className={
                "rounded-md py-2 text-sm font-semibold " +
                (mode === m
                  ? "bg-[var(--panel-2)] text-white"
                  : "text-[var(--muted)]")
              }
            >
              {m === "login" ? "Entrar" : "Cadastro"}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="flex flex-col gap-3">
          <input
            className="field"
            placeholder="Usuário"
            autoCapitalize="none"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          {mode === "register" && (
            <>
              <input
                className="field"
                placeholder="Nome completo (opcional)"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <input
                className="field"
                type="email"
                placeholder="E-mail (opcional)"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </>
          )}
          <input
            className="field"
            type="password"
            placeholder="Senha (mín. 8)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="text-sm text-red-400">{error}</p>}
          {info && <p className="text-sm text-emerald-400">{info}</p>}

          <button className="btn" disabled={busy}>
            {busy ? "…" : mode === "login" ? "ENTRAR" : "CRIAR CONTA"}
          </button>
        </form>

        {mode === "login" && (
          <button type="button"
            onClick={() => { setForgot(true); setError(null); setInfo(null); setForgotId(username); }}
            className="mt-3 w-full text-center text-xs text-[var(--muted)] underline">
            Esqueci minha senha
          </button>
        )}

        {mode === "login" && passkeyOn && (
          <>
            <div className="my-4 flex items-center gap-3 text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">
              <span className="h-px flex-1 bg-[var(--border)]" />
              ou
              <span className="h-px flex-1 bg-[var(--border)]" />
            </div>
            <button type="button" className="btn btn-ghost" onClick={loginPasskey} disabled={busy}>
              🔓 Entrar com biometria
            </button>
          </>
        )}
        </>
        )}
      </div>
    </div>
  );
}
