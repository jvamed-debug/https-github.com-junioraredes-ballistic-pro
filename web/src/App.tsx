import { useEffect, useState } from "react";
import { api, type User } from "./api.ts";
import { InstallPrompt } from "./InstallPrompt.tsx";
import { OfflineBanner } from "./OfflineBanner.tsx";
import { Login } from "./pages/Login.tsx";
import { Activities } from "./pages/Activities.tsx";
import { Acervo } from "./pages/Acervo.tsx";
import { Documents } from "./pages/Documents.tsx";
import { Legislacao } from "./pages/Legislacao.tsx";
import { Events } from "./pages/Events.tsx";
import { Places } from "./pages/Places.tsx";
import { ResetPassword } from "./pages/ResetPassword.tsx";
import { Dashboard } from "./pages/Dashboard.tsx";
import { Dope } from "./pages/Dope.tsx";
import { Reloading } from "./pages/Reloading.tsx";
import { Inventory } from "./pages/Inventory.tsx";
import { Logbook } from "./pages/Logbook.tsx";
import { Costs } from "./pages/Costs.tsx";
import { Advisor } from "./pages/Advisor.tsx";
import { Performance } from "./pages/Performance.tsx";
import { Target } from "./pages/Target.tsx";
import { Profile } from "./pages/Profile.tsx";
import { getLayout, type Layout } from "./theme.ts";
import { runAlertCheck } from "./notify.ts";

//  `tech: true` marca as abas de balística/recarga que o layout "Essencial"
//  esconde — o dia a dia do CAC fica sempre visível.
const TABS = [
  { id: "painel", label: "📊 Painel" },
  { id: "hab", label: "📅 Habitualidades" },
  { id: "eventos", label: "🏆 Eventos" },
  { id: "acervo", label: "🔫 Acervo" },
  { id: "docs", label: "📄 Documentos" },
  { id: "locais", label: "🗺️ Locais" },
  { id: "dope", label: "🎯 DOPE", tech: true },
  { id: "reload", label: "📋 Recarga", tech: true },
  { id: "inv", label: "📦 Inventário", tech: true },
  { id: "log", label: "📔 Logbook", tech: true },
  { id: "perf", label: "📈 Performance", tech: true },
  { id: "alvo", label: "🎯 Alvo", tech: true },
  { id: "cost", label: "💰 Custos" },
  { id: "lei", label: "⚖️ Legislação" },
  { id: "ia", label: "🤖 IA", tech: true },
  { id: "profile", label: "👤 Perfil" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState<TabId>("painel");
  const [layout, setLayout] = useState<Layout>(getLayout());
  //  Link de recuperação de senha: ?reset=<token> na URL abre a tela de nova
  //  senha, mesmo sem estar logado.
  const [resetToken, setResetToken] = useState<string | null>(
    () => new URLSearchParams(window.location.search).get("reset"),
  );

  //  No layout Essencial, escondemos as abas técnicas. Se a aba atual for uma
  //  delas, volta ao Painel para não ficar numa tela invisível.
  const visibleTabs = TABS.filter((t) => layout === "full" || !("tech" in t && t.tech));
  useEffect(() => {
    if (!visibleTabs.some((t) => t.id === tab)) setTab("painel");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layout]);

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

  //  Com o usuário logado, checa os vencimentos e dispara as notificações do
  //  navegador (se ativadas) — ao abrir e sempre que o app volta ao foco.
  useEffect(() => {
    if (!user) return;
    runAlertCheck();
    const onFocus = () => runAlertCheck();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [user]);

  function onLogout() {
    api.logout();
    setUser(null);
  }

  if (resetToken) {
    return (
      <ResetPassword
        token={resetToken}
        onDone={() => {
          //  Limpa o ?reset= da URL e volta ao fluxo normal (login).
          window.history.replaceState({}, "", window.location.pathname);
          setResetToken(null);
        }}
      />
    );
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
      <OfflineBanner />
      <InstallPrompt />
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
            aria-label="Sair da conta"
            className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]"
          >
            Sair
          </button>
        </div>
      </header>
      <nav aria-label="Seções" className="sticky top-0 z-10 flex gap-1 overflow-x-auto border-b border-[var(--border)] bg-[var(--bg)] px-2 py-2">
        {visibleTabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            aria-current={tab === t.id ? "page" : undefined}
            className={
              "flex min-h-[44px] items-center whitespace-nowrap rounded-md px-3 text-sm font-semibold " +
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
        {tab === "painel" && <Dashboard />}
        {tab === "hab" && <Activities />}
        {tab === "eventos" && <Events />}
        {tab === "acervo" && <Acervo />}
        {tab === "docs" && <Documents />}
        {tab === "locais" && <Places />}
        {tab === "dope" && <Dope />}
        {tab === "reload" && <Reloading />}
        {tab === "inv" && <Inventory />}
        {tab === "log" && <Logbook />}
        {tab === "perf" && <Performance />}
        {tab === "alvo" && <Target />}
        {tab === "cost" && <Costs />}
        {tab === "lei" && <Legislacao />}
        {tab === "ia" && <Advisor />}
        {tab === "profile" && (
          <Profile user={user} onUpdated={setUser} layout={layout} onLayoutChange={setLayout} />
        )}
      </main>
    </div>
  );
}
