import { useEffect, useMemo, useState } from "react";
import {
  api,
  type Catalog,
  type ChargeEstimate,
  type LoadData,
  type ReloadWarning,
} from "../api.ts";

function num(v: string, fallback = 0): number {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : fallback;
}

export function Reloading() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);

  const [caliber, setCaliber] = useState("");
  const [projectile, setProjectile] = useState("");
  const [powder, setPowder] = useState("");
  const [primer, setPrimer] = useState("");

  const [warnings, setWarnings] = useState<ReloadWarning[]>([]);

  useEffect(() => {
    api
      .catalog()
      .then((c) => {
        setCatalog(c);
        const first = Object.keys(c.calibers)[0] ?? "";
        setCaliber(first);
      })
      .catch((e) => setLoadErr(e instanceof Error ? e.message : "Falha ao carregar o catálogo."));
  }, []);

  const calData = catalog?.calibers[caliber];
  const projectiles = useMemo(
    () => (calData ? Object.keys(calData.projectiles) : []),
    [calData],
  );
  const projData = calData?.projectiles[projectile];
  const powders = useMemo(
    () => (projData ? Object.keys(projData.powders) : []),
    [projData],
  );
  const load: LoadData | undefined = projData?.powders[powder];

  // Ao trocar de calibre, escolhe o primeiro projétil; ao trocar de projétil,
  // a primeira pólvora — para nunca ficar num estado sem seleção válida.
  useEffect(() => {
    if (projectiles.length && !projectiles.includes(projectile)) {
      setProjectile(projectiles[0]);
    }
  }, [projectiles, projectile]);
  useEffect(() => {
    if (powders.length && !powders.includes(powder)) {
      setPowder(powders[0]);
    }
  }, [powders, powder]);

  // Avisos de segurança: recalcula sempre que a combinação muda.
  useEffect(() => {
    if (!caliber) {
      setWarnings([]);
      return;
    }
    let alive = true;
    api
      .reloadWarnings({ caliber, powder, primer })
      .then((r) => alive && setWarnings(r.warnings))
      .catch(() => alive && setWarnings([]));
    return () => {
      alive = false;
    };
  }, [caliber, powder, primer]);

  if (loadErr) {
    return <p className="text-sm text-red-400">{loadErr}</p>;
  }
  if (!catalog) {
    return <p className="text-sm text-[var(--muted)]">Carregando catálogo…</p>;
  }

  const dims: [string, string | undefined][] = [
    ["Comp. máx (OAL)", calData?.max_oal],
    ["Estojo máx", calData?.max_case],
    ["Ø projétil", calData?.proj_dia],
    ["Ø base", calData?.base_dia],
  ];

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Dados de Recarga
        </h2>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <Labeled label="Calibre">
            <select className="field" value={caliber} onChange={(e) => setCaliber(e.target.value)}>
              {Object.keys(catalog.calibers).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </Labeled>
          <Labeled label="Projétil">
            <select className="field" value={projectile} onChange={(e) => setProjectile(e.target.value)}>
              {projectiles.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </Labeled>
          <Labeled label="Pólvora">
            <select className="field" value={powder} onChange={(e) => setPowder(e.target.value)}>
              {powders.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </Labeled>
        </div>
        <div className="mt-3">
          <Labeled label="Espoleta (opcional — verifica o tamanho)">
            <input
              className="field"
              value={primer}
              placeholder="Ex.: Small Pistol"
              onChange={(e) => setPrimer(e.target.value)}
            />
          </Labeled>
        </div>
      </section>

      {warnings.length > 0 && (
        <section className="flex flex-col gap-2">
          {warnings.map((w, i) => (
            <div
              key={i}
              className={
                "rounded-lg border px-3 py-2 text-sm " +
                (w.severity === "erro"
                  ? "border-red-500/50 bg-red-500/10 text-red-200"
                  : "border-amber-500/50 bg-amber-500/10 text-amber-200")
              }
            >
              <b className="mr-1">{w.severity === "erro" ? "⛔" : "⚠️"}</b>
              {w.message}
            </div>
          ))}
        </section>
      )}

      {calData && (
        <section className="card p-4">
          <h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-[var(--muted)]">
            Dimensões do cartucho
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {dims.map(([label, value]) => (
              <div key={label} className="rounded-lg bg-[var(--panel-2)] px-3 py-2">
                <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">{label}</div>
                <div className="tabnum text-sm font-semibold">{value ?? "—"}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {load && <LoadCard powder={powder} load={load} />}

      <Estimator
        defaultGrains={grainsFromProjectile(projectile)}
        defaultVelocity={load?.velocity}
      />
    </div>
  );
}

function LoadCard({ powder, load }: { powder: string; load: LoadData }) {
  const min = load.min ?? 0;
  const max = load.max ?? 0;
  const unit = load.unit ?? "grains";
  const hasRange = max > min && min > 0;

  return (
    <section className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
        <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Carga · {powder}
        </h3>
        {load.velocity != null && (
          <span className="tabnum text-xs text-[var(--wind)]">{load.velocity} fps</span>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-end justify-center gap-6">
          <div className="text-center">
            <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">Mín</div>
            <div className="tabnum text-2xl font-bold text-white">{min}</div>
          </div>
          <div className="pb-1 text-[var(--muted)]">→</div>
          <div className="text-center">
            <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">Máx</div>
            <div className="tabnum text-2xl font-bold text-[var(--up)]">{max}</div>
          </div>
          <div className="pb-1 text-xs text-[var(--muted)]">{unit}</div>
        </div>
        {hasRange && (
          <div className="mt-4">
            <div className="h-2 w-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-red-500" />
            <div className="mt-1 flex justify-between text-[0.62rem] text-[var(--muted)]">
              <span>Comece no mínimo</span>
              <span>Nunca ultrapasse o máximo</span>
            </div>
          </div>
        )}
        {load.note && (
          <p className="mt-3 rounded-lg bg-[var(--panel-2)] px-3 py-2 text-xs text-[var(--muted)]">
            {load.note}
          </p>
        )}
        <p className="mt-3 text-[0.7rem] leading-relaxed text-[var(--muted)]">
          Desenvolva a carga a partir do mínimo, subindo em pequenos passos e observando
          sinais de sobrepressão. Os valores são referência do fabricante — confirme sempre
          na tabela oficial do seu lote.
        </p>
      </div>
    </section>
  );
}

function Estimator({
  defaultGrains,
  defaultVelocity,
}: {
  defaultGrains?: number;
  defaultVelocity?: number;
}) {
  const [grains, setGrains] = useState("");
  const [vel, setVel] = useState("");
  const [calorific, setCalorific] = useState("4000");
  const [eff, setEff] = useState("30");
  const [res, setRes] = useState<ChargeEstimate | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Pré-preenche com o projétil/pólvora selecionados, sem sobrescrever o que o
  // usuário já digitou.
  useEffect(() => {
    if (defaultGrains && !grains) setGrains(String(defaultGrains));
  }, [defaultGrains]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (defaultVelocity && !vel) setVel(String(defaultVelocity));
  }, [defaultVelocity]); // eslint-disable-line react-hooks/exhaustive-deps

  async function run() {
    setBusy(true);
    setErr(null);
    try {
      setRes(
        await api.estimateCharge({
          projectile_grains: num(grains, 0),
          velocity_fps: num(vel, 0),
          calorific_j_per_g: num(calorific, 4000),
          efficiency_percent: num(eff, 30),
        }),
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Falha no cálculo.");
      setRes(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card p-4">
      <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
        Estimador de carga (ordem de grandeza)
      </h3>
      <div className="mb-3 rounded-lg border border-red-500/50 bg-red-500/10 px-3 py-2 text-xs text-red-200">
        <b>⛔ Risco à vida.</b> Balística interna não é linear: esta conta ignora o pico de
        pressão de câmara, o volume e o tempo de queima. Serve só para comparar ordens de
        grandeza — <b>nunca</b> para definir uma carga real. Use tabela oficial (SAAMI/CIP),
        comece 10% abaixo e meça com cronógrafo.
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Labeled label="Projétil (gr)">
          <input className="field" inputMode="decimal" value={grains} onChange={(e) => setGrains(e.target.value)} />
        </Labeled>
        <Labeled label="Velocidade (fps)">
          <input className="field" inputMode="decimal" value={vel} onChange={(e) => setVel(e.target.value)} />
        </Labeled>
        <Labeled label="Poder calor. (J/g)">
          <input className="field" inputMode="decimal" value={calorific} onChange={(e) => setCalorific(e.target.value)} />
        </Labeled>
        <Labeled label="Eficiência (%)">
          <input className="field" inputMode="decimal" value={eff} onChange={(e) => setEff(e.target.value)} />
        </Labeled>
      </div>
      <button className="btn mt-3" onClick={run} disabled={busy}>
        {busy ? "Calculando…" : "ESTIMAR"}
      </button>
      {err && <p className="mt-2 text-sm text-red-400">{err}</p>}
      {res && (
        <div className="mt-3 grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-[var(--panel-2)] px-3 py-2 text-center">
            <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">Energia na boca</div>
            <div className="tabnum text-lg font-bold text-white">{res.energy_j.toFixed(0)} J</div>
            <div className="tabnum text-[0.7rem] text-[var(--muted)]">{res.energy_ftlbs.toFixed(0)} ft·lb</div>
          </div>
          <div className="rounded-lg bg-[var(--panel-2)] px-3 py-2 text-center">
            <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">Carga estimada</div>
            <div className="tabnum text-lg font-bold text-[var(--wind)]">
              {res.estimated_charge_grains.toFixed(2)} gr
            </div>
            <div className="text-[0.7rem] text-[var(--muted)]">ponto de partida teórico</div>
          </div>
        </div>
      )}
    </section>
  );
}

// Tenta ler o peso do projétil pelo nome do catálogo (ex.: "147gr JHP" → 147).
function grainsFromProjectile(name: string): number | undefined {
  const m = name.match(/(\d+(?:\.\d+)?)\s*gr/i);
  return m ? parseFloat(m[1]) : undefined;
}

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">{label}</span>
      {children}
    </label>
  );
}
