import { useState } from "react";
import { api } from "../api.ts";

// Tela de "definir nova senha", aberta pelo link ?reset=<token> do e-mail.
export function ResetPassword({ token, onDone }: { token: string; onDone: () => void }) {
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (pw.length < 8) { setError("A senha deve ter ao menos 8 caracteres."); return; }
    if (pw !== pw2) { setError("As senhas não coincidem."); return; }
    setBusy(true);
    try {
      await api.resetPassword(token, pw);
      setOk(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao redefinir a senha.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center p-4">
      <div className="card w-full max-w-sm p-6">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-2 inline-block h-3 w-3 rounded-full bg-[var(--accent)] shadow-[0_0_12px_var(--accent)]" />
          <h1 className="text-lg font-bold tracking-wide">NOVA SENHA</h1>
          <p className="text-xs text-[var(--muted)]">Defina a senha da sua conta</p>
        </div>

        {ok ? (
          <div className="flex flex-col gap-4 text-center">
            <p className="text-sm text-emerald-400">
              Senha redefinida com sucesso. Já pode entrar com a nova senha.
            </p>
            <button className="btn" onClick={onDone}>IR PARA O LOGIN</button>
          </div>
        ) : (
          <form onSubmit={submit} className="flex flex-col gap-3">
            <input className="field" type="password" placeholder="Nova senha (mín. 8)"
              value={pw} onChange={(e) => setPw(e.target.value)} required />
            <input className="field" type="password" placeholder="Repita a nova senha"
              value={pw2} onChange={(e) => setPw2(e.target.value)} required />
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button className="btn" disabled={busy}>{busy ? "…" : "REDEFINIR SENHA"}</button>
            <button type="button" onClick={onDone}
              className="text-xs text-[var(--muted)] underline">
              Cancelar e voltar ao login
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
