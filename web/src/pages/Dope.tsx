import { useState } from "react";
import { api, type DopeEntry, type TrajectoryResponse } from "../api.ts";

type Unit = "MIL" | "MOA";

const CLICKS: Record<Unit, { label: string; value: number }[]> = {
  MIL: [
    { label: "0.1 mil (padrão)", value: 0.1 },
    { label: "0.05 mil", value: 0.05 },
  ],
  MOA: [
    { label: "1/4 MOA (padrão)", value: 0.25 },
    { label: "1/8 MOA", value: 0.125 },
    { label: "1/2 MOA", value: 0.5 },
  ],
};

function num(v: string, fallback = 0): number {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : fallback;
}

export function Dope() {
  const [weight, setWeight] = useState("168");
  const [bc, setBc] = useState("0.462");
  const [mv, setMv] = useState("2650");
  const [zero, setZero] = useState("100");
  const [max, setMax] = useState("500");
  const [step, setStep] = useState("100");
  const [windKmh, setWindKmh] = useState("0");

  const [unit, setUnit] = useState<Unit>("MIL");
  const [click, setClick] = useState(0.1);
  const [incline, setIncline] = useState(0);

  // Correções de tiro longo (opcionais).
  const [advOpen, setAdvOpen] = useState(false);
  const [lat, setLat] = useState("");
  const [azimuth, setAzimuth] = useState("0");
  const [twist, setTwist] = useState("");
  const [twistDir, setTwistDir] = useState<"right" | "left">("right");
  const [bulletLen, setBulletLen] = useState("");
  const [diamMm, setDiamMm] = useState("");

  const [res, setRes] = useState<TrajectoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function calc() {
    setError(null);
    setBusy(true);
    try {
      const body = {
        projectile: {
          weight_grains: num(weight, 150),
          bc_g1: num(bc, 0.4),
          muzzle_velocity_fps: num(mv, 2600),
          diameter_mm: num(diamMm),
        },
        zero_range_m: num(zero, 100),
        max_range_m: num(max, 500),
        step_m: num(step, 100),
        wind_speed_ms: num(windKmh) / 3.6,
        wind_angle_deg: 90,
        latitude_deg: lat.trim() !== "" ? num(lat) : null,
        azimuth_deg: num(azimuth),
        twist_rate_in: num(twist),
        twist_dir: twistDir,
        bullet_length_in: num(bulletLen),
        dope: { unit, click_value: click, incline_deg: incline },
      };
      setRes(await api.trajectory(body));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no cálculo.");
      setRes(null);
    } finally {
      setBusy(false);
    }
  }

  function downloadCard(entries: DopeEntry[]) {
    const rows = entries
      .map((e) => {
        const wind = e.windage_dir === "-" ? "—" : `${e.windage.toFixed(1)} ${e.windage_dir}`;
        return `<tr><td>${Math.round(e.range_m)}</td><td class="up">${e.elevation.toFixed(
          1,
        )}<span>${e.elevation_clicks} clk</span></td><td class="wd">${wind}<span>${
          e.windage_clicks
        } clk</span></td><td>${Math.round(e.velocity_fps)}</td><td>${e.time_of_flight_s.toFixed(
          2,
        )}</td></tr>`;
      })
      .join("");
    const html = `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cartão de DOPE</title><style>body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:16px}.c{max-width:520px;margin:auto;background:#1e293b;border:1px solid #334155;border-radius:12px;overflow:hidden}h1{font-size:1rem;margin:0;padding:14px 16px;background:#111827;border-bottom:2px solid #f59e0b;text-transform:uppercase;letter-spacing:.04em}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{padding:8px 6px;text-align:center;font-size:.82rem;border-bottom:1px solid #334155}th{font-size:.62rem;text-transform:uppercase;color:#94a3b8;background:#0f172a}td span{display:block;font-size:.6rem;color:#64748b}td.up{color:#fca5a5;font-weight:700}td.wd{color:#fcd34d;font-weight:700}td:first-child{font-weight:700;color:#fff}@media print{body{background:#fff;color:#000}}</style><div class="c"><h1>Cartão de DOPE · Torre ${unit} · Ângulo ${incline}°</h1><table><thead><tr><th>Dist (m)</th><th>Elev (${unit})</th><th>Vento (${unit})</th><th>Vel (fps)</th><th>ToF (s)</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cartao_dope.html";
    a.click();
    URL.revokeObjectURL(url);
  }

  const card = res?.dope_card ?? [];

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Projétil
        </h2>
        <div className="grid grid-cols-3 gap-2">
          <Labeled label="Peso (gr)">
            <input className="field" inputMode="decimal" value={weight} onChange={(e) => setWeight(e.target.value)} />
          </Labeled>
          <Labeled label="BC (G1)">
            <input className="field" inputMode="decimal" value={bc} onChange={(e) => setBc(e.target.value)} />
          </Labeled>
          <Labeled label="V0 (fps)">
            <input className="field" inputMode="decimal" value={mv} onChange={(e) => setMv(e.target.value)} />
          </Labeled>
          <Labeled label="Zero (m)">
            <input className="field" inputMode="decimal" value={zero} onChange={(e) => setZero(e.target.value)} />
          </Labeled>
          <Labeled label="Máx (m)">
            <input className="field" inputMode="decimal" value={max} onChange={(e) => setMax(e.target.value)} />
          </Labeled>
          <Labeled label="Passo (m)">
            <input className="field" inputMode="decimal" value={step} onChange={(e) => setStep(e.target.value)} />
          </Labeled>
          <Labeled label="Vento (km/h)">
            <input className="field" inputMode="decimal" value={windKmh} onChange={(e) => setWindKmh(e.target.value)} />
          </Labeled>
        </div>
      </section>

      <section className="card p-4">
        <button
          type="button"
          onClick={() => setAdvOpen((v) => !v)}
          className="flex w-full items-center justify-between text-sm font-bold uppercase tracking-wide text-[var(--muted)]"
        >
          <span>Tiro longo (spin drift · Coriolis)</span>
          <span>{advOpen ? "−" : "+"}</span>
        </button>
        {advOpen && (
          <div className="mt-3 flex flex-col gap-3">
            <div className="grid grid-cols-3 gap-2">
              <Labeled label="Passo raiam. (1:n pol)">
                <input className="field" inputMode="decimal" placeholder="ex.: 11" value={twist} onChange={(e) => setTwist(e.target.value)} />
              </Labeled>
              <Labeled label="Sentido">
                <select className="field" value={twistDir} onChange={(e) => setTwistDir(e.target.value as "right" | "left")}>
                  <option value="right">Direita</option>
                  <option value="left">Esquerda</option>
                </select>
              </Labeled>
              <Labeled label="Comp. projétil (pol)">
                <input className="field" inputMode="decimal" placeholder="ex.: 1.24" value={bulletLen} onChange={(e) => setBulletLen(e.target.value)} />
              </Labeled>
              <Labeled label="Diâmetro (mm)">
                <input className="field" inputMode="decimal" placeholder="ex.: 7.82" value={diamMm} onChange={(e) => setDiamMm(e.target.value)} />
              </Labeled>
              <Labeled label="Latitude (°)">
                <input className="field" inputMode="decimal" placeholder="ex.: -23" value={lat} onChange={(e) => setLat(e.target.value)} />
              </Labeled>
              <Labeled label="Azimute (°)">
                <input className="field" inputMode="decimal" placeholder="0 = Norte" value={azimuth} onChange={(e) => setAzimuth(e.target.value)} />
              </Labeled>
            </div>
            <p className="text-[0.7rem] leading-relaxed text-[var(--muted)]">
              Spin drift precisa do passo do raiamento + comprimento do projétil (ou o diâmetro,
              já preenchido). Coriolis precisa da latitude do local (negativa no Hemisfério Sul) e
              do azimute do tiro. Efeitos relevantes só além de ~500&nbsp;m.
            </p>
          </div>
        )}
      </section>

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Torre / DOPE
        </h2>
        <div className="grid grid-cols-3 gap-2">
          <Labeled label="Unidade">
            <select
              className="field"
              value={unit}
              onChange={(e) => {
                const u = e.target.value as Unit;
                setUnit(u);
                setClick(CLICKS[u][0].value);
              }}
            >
              <option value="MIL">MIL</option>
              <option value="MOA">MOA</option>
            </select>
          </Labeled>
          <Labeled label="Clique">
            <select className="field" value={click} onChange={(e) => setClick(num(e.target.value))}>
              {CLICKS[unit].map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </Labeled>
          <Labeled label={`Ângulo ${incline}°`}>
            <input
              type="range"
              min={-60}
              max={60}
              step={5}
              value={incline}
              onChange={(e) => setIncline(num(e.target.value))}
              className="w-full"
            />
          </Labeled>
        </div>
        <button className="btn mt-3" onClick={calc} disabled={busy}>
          {busy ? "Calculando…" : "CALCULAR CARTÃO DE DOPE"}
        </button>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      {card.length > 0 && (
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
              Cartão de DOPE
            </h2>
            <button className="rounded-md border border-[var(--border)] px-3 py-1 text-xs text-[var(--muted)]" onClick={() => downloadCard(card)}>
              📇 Baixar
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full tabnum text-center text-sm">
              <thead>
                <tr className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">
                  <th className="px-2 py-2">Dist (m)</th>
                  <th className="px-2 py-2">Elev ({unit})</th>
                  <th className="px-2 py-2">Cliques</th>
                  <th className="px-2 py-2">Vento ({unit})</th>
                  <th className="px-2 py-2">Cliques</th>
                  <th className="px-2 py-2">Vel</th>
                </tr>
              </thead>
              <tbody>
                {card.map((e) => (
                  <tr key={e.range_m} className="border-t border-[var(--border)]">
                    <td className="px-2 py-2 font-bold text-white">{Math.round(e.range_m)}</td>
                    <td className="px-2 py-2 font-bold text-[var(--up)]">{e.elevation.toFixed(1)}</td>
                    <td className="px-2 py-2 text-[var(--muted)]">{e.elevation_clicks}</td>
                    <td className="px-2 py-2 font-bold text-[var(--wind)]">
                      {e.windage_dir === "-" ? "—" : `${e.windage.toFixed(1)} ${e.windage_dir}`}
                    </td>
                    <td className="px-2 py-2 text-[var(--muted)]">{e.windage_clicks}</td>
                    <td className="px-2 py-2">{Math.round(e.velocity_fps)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="px-4 py-3 text-xs text-[var(--muted)]">
            Vento: <b>E</b> = dial p/ esquerda (tiro foi à direita), <b>D</b> = p/ direita.
            Elevação = subida (come-up). {incline !== 0 && `Compensado para ${incline}°.`}
            {card.some((e) => e.spin_drift_cm !== 0) && (
              <>
                {" "}A correção lateral já inclui a deriva giroscópica
                {" "}(máx {Math.max(...card.map((e) => Math.abs(e.spin_drift_cm))).toFixed(1)}&nbsp;cm)
                {lat.trim() !== "" ? " e Coriolis." : "."}
              </>
            )}
          </p>
        </section>
      )}
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">{label}</span>
      {children}
    </label>
  );
}
