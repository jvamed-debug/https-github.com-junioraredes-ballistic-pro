import { useState } from "react";
import { api, type Advice } from "../api.ts";

type Mode = "load" | "trend";

// Renderiza o texto do consultor (markdown simples: **negrito** e linhas).
function Rendered({ text }: { text: string }) {
  return (
    <div className="flex flex-col gap-1 text-sm leading-relaxed">
      {text.split("\n").map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-1" />;
        const parts = line.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
        return (
          <p key={i} className={line.startsWith("  ") ? "pl-4 text-[var(--muted)]" : ""}>
            {parts.map((p, j) =>
              p.startsWith("**") && p.endsWith("**") ? (
                <strong key={j} className="text-white">{p.slice(2, -2)}</strong>
              ) : (
                <span key={j}>{p}</span>
              ),
            )}
          </p>
        );
      })}
    </div>
  );
}

export function Advisor() {
  const [mode, setMode] = useState<Mode>("load");
  const [caliber, setCaliber] = useState("");
  const [charge, setCharge] = useState("");
  const [vel, setVel] = useState("");
  const [sd, setSd] = useState("");
  const [group, setGroup] = useState("");

  const [advice, setAdvice] = useState<Advice | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const numOrNull = (s: string) => (s.trim() ? parseFloat(s) : null);

  async function run() {
    setError(null);
    setBusy(true);
    setAdvice(null);
    try {
      if (mode === "load") {
        setAdvice(await api.adviseLoad({
          caliber: caliber || "—",
          charge: numOrNull(charge),
          velocity: numOrNull(vel),
          sd: numOrNull(sd),
          grouping: numOrNull(group),
        }));
      } else {
        const logs = await api.listLogbook();
        setAdvice(await api.adviseTrend(
          logs.map((l) => ({
            velocity_avg: l.velocity_avg ?? null,
            velocity_sd: l.velocity_sd ?? null,
            grouping_mm: l.grouping_mm ?? null,
          })),
        ));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha na análise.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <div className="mb-3 grid grid-cols-2 gap-2">
          {(["load", "trend"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setAdvice(null); }}
              className={
                "rounded-md py-2 text-sm font-semibold " +
                (mode === m ? "bg-[var(--panel-2)] text-white" : "text-[var(--muted)]")
              }
            >
              {m === "load" ? "Sugestão de carga" : "Tendência"}
            </button>
          ))}
        </div>

        {mode === "load" ? (
          <div className="grid grid-cols-2 gap-2">
            <input className="field col-span-2" placeholder="Calibre (ex.: .308 WIN)" value={caliber} onChange={(e) => setCaliber(e.target.value)} />
            <input className="field" inputMode="decimal" placeholder="Carga (gr)" value={charge} onChange={(e) => setCharge(e.target.value)} />
            <input className="field" inputMode="decimal" placeholder="Velocidade (fps)" value={vel} onChange={(e) => setVel(e.target.value)} />
            <input className="field" inputMode="decimal" placeholder="SD (fps)" value={sd} onChange={(e) => setSd(e.target.value)} />
            <input className="field" inputMode="decimal" placeholder="Agrupamento (mm)" value={group} onChange={(e) => setGroup(e.target.value)} />
          </div>
        ) : (
          <p className="text-sm text-[var(--muted)]">
            Analisa a tendência de velocidade, consistência (SD) e precisão a partir
            do seu <b>logbook</b>.
          </p>
        )}

        <button className="btn mt-3" onClick={run} disabled={busy}>
          {busy ? "Analisando…" : "ANALISAR"}
        </button>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      {advice && (
        <section className="card p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[var(--panel-2)] px-2 py-0.5 text-[0.65rem] uppercase tracking-wide text-[var(--muted)]">
              {advice.provider === "offline" ? "Análise por regras" : `IA · ${advice.provider}`}
            </span>
            {advice.provider === "offline" && (
              <span className="text-[0.65rem] text-[var(--muted)]">
                modo offline — o administrador pode ligar a IA no servidor
              </span>
            )}
          </div>
          <Rendered text={advice.content} />
          <p className="mt-3 border-t border-[var(--border)] pt-3 text-xs text-[var(--muted)]">
            ⚠️ Estimativas não substituem tabelas oficiais (SAAMI/CIP). Comece sempre pela carga mínima.
          </p>
        </section>
      )}
    </div>
  );
}
