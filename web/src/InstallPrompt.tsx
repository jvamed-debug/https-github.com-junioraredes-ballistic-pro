import { useEffect, useState } from "react";

// Evento não tipado nas libs padrão do TS.
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISS_KEY = "install_dismissed";

function isStandalone(): boolean {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    // iOS Safari
    (window.navigator as unknown as { standalone?: boolean }).standalone === true
  );
}

function isIos(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

// Faixa discreta para instalar o app na tela inicial. No Android/desktop usa o
// evento beforeinstallprompt; no iOS (que não o dispara) mostra a dica do
// "Compartilhar → Adicionar à Tela de Início". Some depois de instalado ou
// dispensado.
export function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [show, setShow] = useState(false);
  const [iosHint, setIosHint] = useState(false);

  useEffect(() => {
    if (isStandalone() || localStorage.getItem(DISMISS_KEY)) return;

    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
      setShow(true);
    };
    window.addEventListener("beforeinstallprompt", onPrompt);

    // iOS não emite o evento — oferece a dica manual.
    if (isIos()) {
      setIosHint(true);
      setShow(true);
    }

    const onInstalled = () => setShow(false);
    window.addEventListener("appinstalled", onInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  function dismiss() {
    setShow(false);
    localStorage.setItem(DISMISS_KEY, "1");
  }

  async function install() {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
    setShow(false);
  }

  if (!show) return null;

  return (
    <div className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--panel-2)] px-4 py-2 text-sm">
      <span className="flex-1 text-[var(--muted)]">
        {iosHint
          ? "Instale o app: toque em Compartilhar e “Adicionar à Tela de Início”."
          : "Instale o Ballistic Pro na tela inicial para abrir como app."}
      </span>
      {!iosHint && (
        <button onClick={install} className="rounded-md bg-[var(--accent)] px-3 py-1 text-xs font-semibold text-white">
          📲 Instalar
        </button>
      )}
      <button onClick={dismiss} className="text-[var(--muted)]" aria-label="Dispensar">×</button>
    </div>
  );
}
