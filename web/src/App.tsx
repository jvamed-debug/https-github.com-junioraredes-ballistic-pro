import { useEffect, useState } from "react";
import { api, type User } from "./api.ts";
import { Login } from "./pages/Login.tsx";
import { Dope } from "./pages/Dope.tsx";
import { Reloading } from "./pages/Reloading.tsx";
import { Inventory } from "./pages/Inventory.tsx";
import { Logbook } from "./pages/Logbook.tsx";
import { Costs } from "./pages/Costs.tsx";
import { Advisor } from "./pages/Advisor.tsx";
import { Performance } from "./pages/Performance.tsx";
import { Profile } from "./pages/Profile.tsx";

const TABS = [
  { id: "dope", label: "🎯 DOPE" },
  { id: "reload", label: "📋 Recarga" },
  { id: "inv", label: "📦 Inventário" },
  { id: "log", label: "📔 Logbook" },
  { id: "perf", label: "📈 Performance" },
  { id: "cost", label: "💰 Custos" },
  { id: "ia", label: "🤖 IA" },
  { id: "profile", label: "👤 Perfil" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState<TabId>("dope");

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
      <nav className="flex gap-1 overflow-x-auto border-b border-[var(--border)] px-2 py-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={
              "whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold " +
              (tab === t.id
                ? "bg-[var(--panel-2)] text-white"
                : "text-[var(--muted)]")
            }
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="flex-1 p-4">
        {tab === "dope" && <Dope />}
        {tab === "reload" && <Reloading />}
        {tab === "inv" && <Inventory />}
        {tab === "log" && <Logbook />}
        {tab === "perf" && <Performance />}
        {tab === "cost" && <Costs />}
        {tab === "ia" && <Advisor />}
        {tab === "profile" && <Profile user={user} onUpdated={setUser} />}
      </main>
    </div>
  );
}
