import { useEffect, useMemo, useState } from "react";
import { api, type LogEntry } from "../api.ts";

// Sparkline SVG: área suave + linha + ponto final destacado. Sem libs.
function Sparkline({ values, color }: { values: number[]; color: string }) {
  const W = 300;
  const H = 64;
  const pad = 6;
  if (values.length < 2) {
    return <div className="py-4 text-center text-xs text-[var(--muted)]">Poucos dados para o gráfico.</div>;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const x = (i: number) => pad + (i / (values.length - 1)) * (W - 2 * pad);
  const y = (v: number) => H - pad - ((v - min) / span) * (H - 2 * pad);

  const line = values.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(values.length - 1).toFixed(1)},${H - pad} L${x(0).toFixed(1)},${H - pad} Z`;
  const lastX = x(values.length - 1);
  const lastY = y(values[values.length - 1]);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" preserveAspectRatio="none" role="img">
      <line x1={pad} y1={H / 2} x2={W - pad} y2={H / 2} stroke="var(--border)" strokeWidth="1" strokeDasharray="2 3" />
      <path d={area} fill={color} opacity="0.12" />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={lastX} cy={lastY} r="3.5" fill={color} />
    </svg>
  );
}

function Metric({
  title, unit, values, color, better,
}: {
  title: string; unit: string; values: number[]; color: string; better?: "lower" | "higher";
}) {
  if (values.length === 0) return null;
  const last = values[values.length - 1];
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  let trend: string | null = null;
  if (values.length >= 4) {
    const half = Math.floor(values.length / 2);
    const early = values.slice(0, half).reduce((a, b) => a + b, 0) / half;
    const recent = values.slice(half).reduce((a, b) => a + b, 0) / (values.length - half);
    const diff = recent - early;
    if (Math.abs(diff) / (avg || 1) > 0.02) {
      const good = better ? (better === "lower" ? diff < 0 : diff > 0) : null;
      const arrow = diff < 0 ? "▼" : "▲";
      const cls = good == null ? "text-[var(--muted)]" : good ? "text-emerald-400" : "text-red-400";
      trend = `${arrow} ${Math.abs(diff).toFixed(1)}`;
      return (
        <MetricCard title={title} unit={unit} last={last} avg={avg} values={values} color={color}
          badge={<span className={cls}>{trend}</span>} />
      );
    }
  }
  return <MetricCard title={title} unit={unit} last={last} avg={avg} values={values} color={color} badge={null} />;
}

function MetricCard({
  title, unit, last, avg, values, color, badge,
}: {
  title: string; unit: string; last: number; avg: number; values: number[]; color: string; badge: React.ReactNode;
}) {
  return (
    <section className="card p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">{title}</h3>
        {badge}
      </div>
      <div className="mb-2 flex items-baseline gap-3">
        <span className="tabnum text-2xl font-bold text-white">{last.toFixed(1)}</span>
        <span className="text-xs text-[var(--muted)]">{unit} · média {avg.toFixed(1)}</span>
      </div>
      <Sparkline values={values} color={color} />
    </section>
  );
}

export function Performance() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listLogbook()
      .then((l) => setLogs([...l].reverse())) // API entrega desc; queremos ordem cronológica
      .catch((e) => setError(e instanceof Error ? e.message : "Falha ao carregar."));
  }, []);

  const series = useMemo(() => {
    const pick = (f: (l: LogEntry) => number | null | undefined) =>
      logs.map(f).filter((v): v is number => typeof v === "number");
    return {
      vel: pick((l) => l.velocity_avg),
      sd: pick((l) => l.velocity_sd),
      group: pick((l) => l.grouping_mm),
    };
  }, [logs]);

  const empty = series.vel.length === 0 && series.sd.length === 0 && series.group.length === 0;

  return (
    <div className="flex flex-col gap-4">
      {error && <p className="text-sm text-red-400">{error}</p>}
      {empty ? (
        <section className="card p-6 text-center text-sm text-[var(--muted)]">
          Registre sessões no <b>Logbook</b> com velocidade, SD e/ou agrupamento
          para acompanhar sua evolução aqui.
        </section>
      ) : (
        <>
          <Metric title="Velocidade média" unit="fps" values={series.vel} color="#3b82f6" />
          <Metric title="Consistência (SD)" unit="fps" values={series.sd} color="#f59e0b" better="lower" />
          <Metric title="Agrupamento" unit="mm" values={series.group} color="#10b981" better="lower" />
        </>
      )}
    </div>
  );
}
