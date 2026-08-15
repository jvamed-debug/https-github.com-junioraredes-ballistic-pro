import { useEffect, useState } from "react";

// Avisa quando o aparelho está sem rede — num PWA as chamadas à API falhariam
// em silêncio, e o usuário só veria erros soltos. Some sozinho ao voltar.
export function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="status"
      className="border-b border-amber-500/50 bg-amber-500/15 px-4 py-2 text-center text-sm text-amber-200"
    >
      📴 Sem conexão — algumas ações ficam indisponíveis até a rede voltar.
    </div>
  );
}
