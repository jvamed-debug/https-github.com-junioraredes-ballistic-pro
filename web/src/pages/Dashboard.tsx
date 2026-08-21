import { useCallback, useEffect, useState } from "react";
import { api, type Insights } from "../api.ts";
import { EmptyState, ErrorState, Loading } from "../ui.tsx";
import { Pendencias } from "./Pendencias.tsx";

//  Painel: as pendências do CAC (vencimentos + eventos) sempre no topo, e
//  abaixo os insights de recarga/balística — que podem estar vazios para quem
//  ainda não registrou sessões.
export function Dashboard() {
  return (
    <div className="flex flex-col gap-4">
      <Pendencias />
      <ReloadInsights />
    </div>
  );
}

function ReloadInsights() {
  const [data, setData] = useState<Insights | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    setData(null);
    api
      .insights()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Falha ao carregar."));
  }, []);
  useEffect(() => { load(); }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Loading rows={4} label="Carregando painel" />;

  const t = data.totals;
  if (t.sessions === 0) {
    return (
      <EmptyState
        icon="📊"
        title="Sem dados de recarga ainda"
        hint="Registre sessões no Logbook e insumos no Inventário para o painel de balística ganhar vida."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <section className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <Tile label="Sessões" value={String(t.sessions)} />
        <Tile label="Tiros" value={t.rounds.toLocaleString("pt-BR")} />
        <Tile label="Melhor grupo" value={t.best_group_mm != null ? `${t.best_group_mm} mm` : "—"} accent="up" />
        <Tile label="SD médio" value={t.avg_sd != null ? `${t.avg_sd} fps` : "—"} />
        <Tile label="Valor do estoque" value={`R$ ${t.inventory_value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`} />
        <Tile
          label="Alertas de estoque"
          value={`${t.zero_stock_count + t.low_stock_count}`}
          accent={t.zero_stock_count > 0 ? "bad" : t.low_stock_count > 0 ? "warn" : undefined}
        />
      </section>

      {data.velocity_trend.length >= 2 && (
        <Panel title="Velocidade média (fps)" subtitle="por sessão, em ordem cronológica">
          <LineChart
            values={data.velocity_trend.map((p) => p.velocity_avg ?? 0)}
            color="var(--accent)"
            unit="fps"
          />
        </Panel>
      )}

      {data.cost_trend.length >= 2 && (
        <Panel title="Custo por munição (R$)" subtitle="estimado pelo preço de estoque">
          <LineChart
            values={data.cost_trend.map((p) => p.unit_cost)}
            color="var(--wind)"
            unit=""
            prefix="R$ "
            decimals={2}
          />
        </Panel>
      )}

      {data.best_by_group.length > 0 && (
        <RankTable
          title="Melhores agrupamentos"
          unit="mm"
          rows={data.best_by_group}
          accent="up"
        />
      )}
      {data.best_by_sd.length > 0 && (
        <RankTable
          title="Menores desvios (SD)"
          unit="fps"
          rows={data.best_by_sd}
          accent="accent"
        />
      )}
    </div>
  );
}

function Tile({ label, value, accent }: { label: string; value: string; accent?: "up" | "warn" | "bad" }) {
  const color =
    accent === "up" ? "text-[var(--up)]"
      : accent === "warn" ? "text-amber-400"
      : accent === "bad" ? "text-red-400"
      : "text-white";
  return (
    <div className="card p-3">
      <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div className={`tabnum text-xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function Panel({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <section className="card p-4">
      <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">{title}</h2>
      {subtitle && <p className="mb-2 text-[0.65rem] text-[var(--muted)]">{subtitle}</p>}
      {children}
    </section>
  );
}

// Gráfico de linha de série única — SVG, sem dependência. Uma série só, então
// sem questão de daltonismo: a cor apenas reforça o título que já a nomeia.
function LineChart({
  values,
  color,
  unit,
  prefix = "",
  decimals = 0,
}: {
  values: number[];
  color: string;
  unit: string;
  prefix?: string;
  decimals?: number;
}) {
  const W = 320;
  const H = 130;
  const pad = { l: 6, r: 6, t: 14, b: 6 };
  const n = values.length;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const x = (i: number) => pad.l + (n <= 1 ? 0 : (i / (n - 1)) * (W - pad.l - pad.r));
  const y = (v: number) => pad.t + (1 - (v - min) / span) * (H - pad.t - pad.b);
  const pts = values.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  const last = values[n - 1];
  const fmt = (v: number) => `${prefix}${v.toFixed(decimals)}${unit ? ` ${unit}` : ""}`;

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ minWidth: 260 }}>
        <polyline fill="none" stroke={color} strokeWidth="2" points={pts} strokeLinejoin="round" strokeLinecap="round" />
        {values.map((v, i) => (
          <circle key={i} cx={x(i)} cy={y(v)} r="2.5" fill={color} />
        ))}
        {/* rótulo do último valor, ancorado no ponto — rótulo seletivo, não em todos */}
        <text x={x(n - 1)} y={Math.max(y(last) - 6, 10)} fontSize="9" fill="var(--text)" textAnchor="end" fontWeight="700">
          {fmt(last)}
        </text>
      </svg>
      <div className="flex justify-between text-[0.6rem] text-[var(--muted)]">
        <span>mín {fmt(min)}</span>
        <span>máx {fmt(max)}</span>
      </div>
    </div>
  );
}

function RankTable({
  title,
  unit,
  rows,
  accent,
}: {
  title: string;
  unit: string;
  accent: "up" | "accent";
  rows: { caliber: string | null; powder: string | null; charge: number | null; value: number; velocity_avg: number | null }[];
}) {
  const color = accent === "up" ? "text-[var(--up)]" : "text-[var(--accent)]";
  return (
    <section className="card overflow-hidden">
      <h2 className="border-b border-[var(--border)] px-4 py-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">{title}</h2>
      <table className="w-full tabnum text-sm">
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-[var(--border)] first:border-t-0">
              <td className="px-4 py-2 text-[var(--muted)]">{i + 1}</td>
              <td className="px-2 py-2">
                <div className="font-semibold">{r.caliber}</div>
                <div className="text-[0.65rem] text-[var(--muted)]">
                  {r.powder ?? "—"}{r.charge ? ` · ${r.charge}gr` : ""}
                  {r.velocity_avg ? ` · ${Math.round(r.velocity_avg)} fps` : ""}
                </div>
              </td>
              <td className={`px-4 py-2 text-right font-bold ${color}`}>{r.value} {unit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
