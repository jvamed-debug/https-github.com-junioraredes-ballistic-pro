import { useEffect, useState } from "react";
import {
  api,
  type DopeCard,
  type DopeEntry,
  type Firearm,
  type TrajectoryPoint,
  type TrajectoryResponse,
} from "../api.ts";

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

  // Atmosfera (opcional): pode ser puxada do clima por localização.
  const [atmOpen, setAtmOpen] = useState(false);
  const [temp, setTemp] = useState("15");
  const [pressure, setPressure] = useState("1013");
  const [humidity, setHumidity] = useState("50");
  const [altitude, setAltitude] = useState("0");
  const [weatherBusy, setWeatherBusy] = useState(false);
  const [weatherMsg, setWeatherMsg] = useState<string | null>(null);

  function pullWeather() {
    if (!navigator.geolocation) {
      setWeatherMsg("Geolocalização indisponível neste dispositivo.");
      return;
    }
    setWeatherBusy(true);
    setWeatherMsg(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const w = await api.weather(pos.coords.latitude, pos.coords.longitude);
          setTemp(String(w.temperature_c));
          setPressure(String(w.pressure_hpa));
          setHumidity(String(w.humidity_pct));
          setAltitude(String(w.altitude_m));
          if (!lat.trim()) setLat(pos.coords.latitude.toFixed(2)); // aproveita p/ Coriolis
          setAtmOpen(true);
          setWeatherMsg("Atmosfera atualizada pelo clima local.");
        } catch (e) {
          setWeatherMsg(e instanceof Error ? e.message : "Falha ao obter o clima.");
        } finally {
          setWeatherBusy(false);
        }
      },
      (err) => {
        setWeatherBusy(false);
        setWeatherMsg(err.code === err.PERMISSION_DENIED ? "Permissão de localização negada." : "Não foi possível obter a localização.");
      },
      { timeout: 10000 },
    );
  }

  const [res, setRes] = useState<TrajectoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Cartões salvos + armas, para salvar/reabrir a receita por arma.
  const [cards, setCards] = useState<DopeCard[]>([]);
  const [guns, setGuns] = useState<Firearm[]>([]);
  const [cardName, setCardName] = useState("");
  const [saveGun, setSaveGun] = useState("");
  const [cardMsg, setCardMsg] = useState<string | null>(null);

  async function loadCards() {
    try {
      const [cs, gs] = await Promise.all([api.listDopeCards(), api.listFirearms()]);
      setCards(cs);
      setGuns(gs);
    } catch {
      /* silencioso: tela funciona sem cartões */
    }
  }
  useEffect(() => { loadCards(); }, []);

  const str = (v: number | null | undefined) => (v != null ? String(v) : "");

  async function saveCard() {
    if (!cardName.trim()) {
      setCardMsg("Dê um nome ao cartão.");
      return;
    }
    setCardMsg(null);
    try {
      await api.createDopeCard({
        name: cardName.trim(),
        firearm_id: saveGun ? parseInt(saveGun) : null,
        weight_grains: num(weight) || null,
        bc_g1: num(bc) || null,
        muzzle_velocity_fps: num(mv) || null,
        diameter_mm: num(diamMm) || null,
        bullet_length_in: num(bulletLen) || null,
        zero_range_m: num(zero) || null,
        max_range_m: num(max) || null,
        step_m: num(step) || null,
        twist_rate_in: num(twist) || null,
        twist_dir: twistDir,
        unit,
        click_value: click,
      });
      setCardName("");
      setSaveGun("");
      setCardMsg("Cartão salvo.");
      await loadCards();
    } catch (e) {
      setCardMsg(e instanceof Error ? e.message : "Falha ao salvar.");
    }
  }

  function openCard(c: DopeCard) {
    if (c.weight_grains != null) setWeight(str(c.weight_grains));
    if (c.bc_g1 != null) setBc(str(c.bc_g1));
    if (c.muzzle_velocity_fps != null) setMv(str(c.muzzle_velocity_fps));
    if (c.zero_range_m != null) setZero(str(c.zero_range_m));
    if (c.max_range_m != null) setMax(str(c.max_range_m));
    if (c.step_m != null) setStep(str(c.step_m));
    if (c.unit === "MIL" || c.unit === "MOA") setUnit(c.unit);
    if (c.click_value != null) setClick(c.click_value);
    setTwist(str(c.twist_rate_in));
    if (c.twist_dir === "left" || c.twist_dir === "right") setTwistDir(c.twist_dir);
    setBulletLen(str(c.bullet_length_in));
    setDiamMm(str(c.diameter_mm));
    if (c.twist_rate_in || c.diameter_mm) setAdvOpen(true);
    setCardMsg(`Cartão "${c.name}" carregado.`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function delCard(id: number) {
    await api.deleteDopeCard(id);
    await loadCards();
  }

  const gunName = (id?: number | null) => guns.find((g) => g.id === id)?.model;

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
        atmosphere: {
          temperature_c: num(temp, 15),
          pressure_hpa: num(pressure, 1013.25),
          humidity_pct: num(humidity, 50),
          altitude_m: num(altitude, 0),
        },
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
          Cartões de DOPE
        </h2>
        {cards.length > 0 ? (
          <ul className="mb-3 flex flex-col gap-2">
            {cards.map((c) => (
              <li key={c.id} className="flex items-center justify-between rounded-lg bg-[var(--panel-2)] px-3 py-2">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">{c.name}</div>
                  <div className="text-[0.65rem] text-[var(--muted)]">
                    {gunName(c.firearm_id) ? `${gunName(c.firearm_id)} · ` : ""}
                    {c.weight_grains ? `${c.weight_grains}gr ` : ""}
                    {c.muzzle_velocity_fps ? `· ${c.muzzle_velocity_fps}fps` : ""}
                  </div>
                </div>
                <div className="flex shrink-0 gap-2">
                  <button onClick={() => openCard(c)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">Abrir</button>
                  <button onClick={() => delCard(c.id)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">×</button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mb-3 text-xs text-[var(--muted)]">Nenhum cartão salvo ainda. Preencha os dados abaixo e salve.</p>
        )}
        <div className="grid grid-cols-[1fr_1fr_auto] gap-2">
          <input className="field" placeholder="Nome do cartão" value={cardName} onChange={(e) => setCardName(e.target.value)} />
          <select className="field" value={saveGun} onChange={(e) => setSaveGun(e.target.value)}>
            <option value="">Sem arma</option>
            {guns.map((g) => <option key={g.id} value={g.id}>{g.model}</option>)}
          </select>
          <button className="btn" style={{ width: "auto", paddingInline: 16 }} onClick={saveCard}>Salvar</button>
        </div>
        {cardMsg && <p className="mt-2 text-xs text-[var(--muted)]">{cardMsg}</p>}
      </section>

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
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setAtmOpen((v) => !v)}
            className="flex flex-1 items-center justify-between text-sm font-bold uppercase tracking-wide text-[var(--muted)]"
          >
            <span>Atmosfera</span>
            <span>{atmOpen ? "−" : "+"}</span>
          </button>
          <button
            type="button"
            onClick={pullWeather}
            disabled={weatherBusy}
            className="ml-3 rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]"
          >
            {weatherBusy ? "…" : "📍 Puxar clima"}
          </button>
        </div>
        {atmOpen && (
          <div className="mt-3 grid grid-cols-4 gap-2">
            <Labeled label="Temp (°C)">
              <input className="field" inputMode="decimal" value={temp} onChange={(e) => setTemp(e.target.value)} />
            </Labeled>
            <Labeled label="Pressão (hPa)">
              <input className="field" inputMode="decimal" value={pressure} onChange={(e) => setPressure(e.target.value)} />
            </Labeled>
            <Labeled label="Umidade (%)">
              <input className="field" inputMode="decimal" value={humidity} onChange={(e) => setHumidity(e.target.value)} />
            </Labeled>
            <Labeled label="Altitude (m)">
              <input className="field" inputMode="decimal" value={altitude} onChange={(e) => setAltitude(e.target.value)} />
            </Labeled>
          </div>
        )}
        {weatherMsg && <p className="mt-2 text-xs text-[var(--muted)]">{weatherMsg}</p>}
        <p className="mt-2 text-[0.65rem] text-[var(--muted)]">
          Pressão = QNH (nível do mar); a altitude corrige a densidade. "Puxar clima" usa
          sua localização e o Open-Meteo (sem cadastro).
        </p>
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

      <LoadCompare
        shared={{
          zero: num(zero, 100),
          max: num(max, 500),
          step: num(step, 100),
          windMs: num(windKmh) / 3.6,
        }}
      />
    </div>
  );
}

const COMPARE_COLORS = ["var(--accent)", "var(--up)", "var(--wind)", "#34d399"];

type LoadRow = { name: string; weight: string; bc: string; mv: string };
type LoadResult = { name: string; color: string; points: TrajectoryPoint[] };

function LoadCompare({
  shared,
}: {
  shared: { zero: number; max: number; step: number; windMs: number };
}) {
  const [open, setOpen] = useState(false);
  const [loads, setLoads] = useState<LoadRow[]>([
    { name: "Carga A", weight: "168", bc: "0.462", mv: "2650" },
    { name: "Carga B", weight: "175", bc: "0.505", mv: "2600" },
  ]);
  const [res, setRes] = useState<LoadResult[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setRow(i: number, patch: Partial<LoadRow>) {
    setLoads((rows) => rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  }
  function addRow() {
    if (loads.length >= 4) return;
    setLoads((rows) => [...rows, { name: `Carga ${String.fromCharCode(65 + rows.length)}`, weight: "150", bc: "0.4", mv: "2700" }]);
  }
  function removeRow(i: number) {
    setLoads((rows) => (rows.length > 1 ? rows.filter((_, j) => j !== i) : rows));
  }

  async function compare() {
    setBusy(true);
    setError(null);
    try {
      const out: LoadResult[] = [];
      for (let i = 0; i < loads.length; i++) {
        const l = loads[i];
        const r = await api.trajectory({
          projectile: {
            weight_grains: num(l.weight, 150),
            bc_g1: num(l.bc, 0.4),
            muzzle_velocity_fps: num(l.mv, 2600),
          },
          zero_range_m: shared.zero,
          max_range_m: shared.max,
          step_m: shared.step,
          wind_speed_ms: shared.windMs,
          wind_angle_deg: 90,
        });
        out.push({ name: l.name || `Carga ${i + 1}`, color: COMPARE_COLORS[i % 4], points: r.points });
      }
      setRes(out);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao comparar.");
      setRes(null);
    } finally {
      setBusy(false);
    }
  }

  const ranges = res?.[0]?.points.map((p) => p.range_m) ?? [];

  return (
    <section className="card p-4">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-sm font-bold uppercase tracking-wide text-[var(--muted)]"
      >
        <span>Comparar cargas</span>
        <span>{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="mt-3 flex flex-col gap-3">
          <p className="text-[0.7rem] text-[var(--muted)]">
            Usa o zero, alcance, passo e vento definidos acima. Cada linha é uma carga (peso, BC G1, V0).
          </p>
          {loads.map((l, i) => (
            <div key={i} className="grid grid-cols-[1fr_auto] items-end gap-2">
              <div className="grid grid-cols-4 gap-2">
                <Labeled label="Nome">
                  <input className="field" value={l.name} onChange={(e) => setRow(i, { name: e.target.value })} />
                </Labeled>
                <Labeled label="Peso (gr)">
                  <input className="field" inputMode="decimal" value={l.weight} onChange={(e) => setRow(i, { weight: e.target.value })} />
                </Labeled>
                <Labeled label="BC (G1)">
                  <input className="field" inputMode="decimal" value={l.bc} onChange={(e) => setRow(i, { bc: e.target.value })} />
                </Labeled>
                <Labeled label="V0 (fps)">
                  <input className="field" inputMode="decimal" value={l.mv} onChange={(e) => setRow(i, { mv: e.target.value })} />
                </Labeled>
              </div>
              <button
                type="button"
                onClick={() => removeRow(i)}
                disabled={loads.length <= 1}
                className="mb-1 rounded-md border border-[var(--border)] px-2 py-2 text-xs text-red-400 disabled:opacity-40"
              >
                ×
              </button>
            </div>
          ))}

          <div className="flex gap-2">
            <button type="button" className="btn btn-ghost" onClick={addRow} disabled={loads.length >= 4}>
              + Adicionar carga
            </button>
            <button type="button" className="btn" onClick={compare} disabled={busy}>
              {busy ? "Comparando…" : "COMPARAR"}
            </button>
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}

          {res && res.length > 0 && (
            <>
              <DropChart results={res} />
              <div className="overflow-x-auto">
                <table className="w-full tabnum text-center text-xs">
                  <thead>
                    <tr className="text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
                      <th className="px-2 py-1">Dist (m)</th>
                      {res.map((r) => (
                        <th key={r.name} className="px-2 py-1" style={{ color: r.color }}>{r.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {ranges.map((rng, ri) => (
                      <tr key={rng} className="border-t border-[var(--border)]">
                        <td className="px-2 py-1 font-bold text-white">{Math.round(rng)}</td>
                        {res.map((r) => {
                          const p = r.points[ri];
                          return (
                            <td key={r.name} className="px-2 py-1">
                              {p ? (
                                <>
                                  <span className="font-semibold" style={{ color: r.color }}>{p.drop_cm.toFixed(0)}</span>
                                  <span className="block text-[0.6rem] text-[var(--muted)]">{Math.round(p.velocity_fps)} fps</span>
                                </>
                              ) : "—"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[0.65rem] text-[var(--muted)]">
                Números = queda (cm) na linha de visada; abaixo, velocidade remanescente. Zero em {shared.zero} m.
              </p>
            </>
          )}
        </div>
      )}
    </section>
  );
}

// Sobreposição das curvas de queda (cm) por distância — SVG, sem dependência.
function DropChart({ results }: { results: LoadResult[] }) {
  const W = 320;
  const H = 150;
  const pad = { l: 34, r: 8, t: 8, b: 18 };
  const all = results.flatMap((r) => r.points);
  if (all.length === 0) return null;
  const maxRange = Math.max(...all.map((p) => p.range_m));
  const drops = all.map((p) => p.drop_cm);
  const minDrop = Math.min(...drops, 0);
  const maxDrop = Math.max(...drops, 0);
  const span = maxDrop - minDrop || 1;

  const x = (r: number) => pad.l + (r / maxRange) * (W - pad.l - pad.r);
  const y = (d: number) => pad.t + ((maxDrop - d) / span) * (H - pad.t - pad.b);

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ minWidth: 280 }}>
        {/* linha de visada (drop = 0) */}
        <line x1={pad.l} y1={y(0)} x2={W - pad.r} y2={y(0)} stroke="var(--border)" strokeDasharray="3 3" />
        <text x={2} y={y(0) + 3} fontSize="8" fill="var(--muted)">0</text>
        <text x={2} y={y(minDrop) + 3} fontSize="8" fill="var(--muted)">{minDrop.toFixed(0)}</text>
        {results.map((r) => (
          <polyline
            key={r.name}
            fill="none"
            stroke={r.color}
            strokeWidth="2"
            points={r.points.map((p) => `${x(p.range_m)},${y(p.drop_cm)}`).join(" ")}
          />
        ))}
        <text x={pad.l} y={H - 4} fontSize="8" fill="var(--muted)">0 m</text>
        <text x={W - pad.r} y={H - 4} fontSize="8" fill="var(--muted)" textAnchor="end">{Math.round(maxRange)} m</text>
      </svg>
      <div className="mt-1 flex flex-wrap gap-3">
        {results.map((r) => (
          <span key={r.name} className="flex items-center gap-1 text-[0.65rem] text-[var(--muted)]">
            <span className="inline-block h-2 w-3 rounded-sm" style={{ background: r.color }} />
            {r.name}
          </span>
        ))}
      </div>
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
