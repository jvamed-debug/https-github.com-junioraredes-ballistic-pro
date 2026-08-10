import { useEffect, useState } from "react";
import { api, type User } from "./api.ts";
import { Login } from "./pages/Login.tsx";
import { Dope } from "./pages/Dope.tsx";

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  // Ao abrir, se há token salvo, tenta recuperar o usuário. Token expirado
  // (401) simplesmente cai para a tela de login.
  useEffect(() => {
    if (!api.hasToken()) {
      setReady(true);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => api.logout())
      .finally(() => setReady(true));
  }, []);

  function onLogout() {
    api.logout();
    setUser(null);
  }

  if (!ready) {
    return (
      <div className="flex h-full items-center justify-center text-[var(--muted)]">
        Carregando…
      </div>
    );
  }

  if (!user) {
    return <Login onAuthed={setUser} />;
  }

  return (
    <div className="mx-auto flex min-h-full max-w-3xl flex-col">
      <header className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-[var(--accent)] shadow-[0_0_10px_var(--accent)]" />
          <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted)]">
            Ballistic Pro
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-[var(--muted)]">
            {user.name || user.username}
          </span>
          <button
            onClick={onLogout}
            className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]"
          >
            Sair
          </button>
        </div>
      </header>
      <main className="flex-1 p-4">
        <Dope />
      </main>
    </div>
  );
}
