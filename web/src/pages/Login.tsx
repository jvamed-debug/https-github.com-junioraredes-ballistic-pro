import { useState } from "react";
import { api, type User } from "../api.ts";

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
      </div>
    </div>
  );
}
