import { useEffect, useMemo, useState } from "react";
import { api, type ExpenseReport, type InventoryItem } from "../api.ts";
import { ErrorState, Loading } from "../ui.tsx";

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

// Períodos do filtro de gastos → janela [since, until] em ISO (ou undefined).
type Period = "mes" | "semestre" | "ano" | "tudo";
function windowFor(p: Period): { since?: string; until?: string } {
  const now = new Date();
  const y = now.getFullYear();
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  if (p === "mes") return { since: iso(new Date(y, now.getMonth(), 1)) };
  if (p === "semestre") return { since: iso(new Date(y, now.getMonth() < 6 ? 0 : 6, 1)) };
  if (p === "ano") return { since: iso(new Date(y, 0, 1)) };
  return {};
}

// "2026-08" → "ago/26" para o eixo do gráfico.
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
function monthLabel(iso: string): string {
  const [y, m] = iso.split("-");
  return `${MESES[Number(m) - 1] ?? m}/${y.slice(2)}`;
}

function BarChart({ data }: { data: Array<{ month: string; total: number }> }) {
  const max = Math.max(...data.map((d) => d.total), 1);
  const W = 320, H = 140, pad = 24;
  const bw = (W - pad * 2) / data.length;
  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label="Gráfico de barras de gastos por mês" style={{ minWidth: data.length * 44 }}>
        {data.map((d, i) => {
          const h = (d.total / max) * (H - pad * 2);
          const x = pad + i * bw;
          const y = H - pad - h;
          return (
            <g key={d.month}>
              <rect x={x + bw * 0.15} y={y} width={bw * 0.7} height={h}
                rx={2} fill="var(--accent)" />
              <text x={x + bw / 2} y={H - pad + 12} textAnchor="middle"
                fontSize="8" fill="var(--muted)">{monthLabel(d.month)}</text>
              <text x={x + bw / 2} y={y - 3} textAnchor="middle"
                fontSize="7.5" fill="var(--muted)">
                {d.total >= 1000 ? `${(d.total / 1000).toFixed(1)}k` : d.total.toFixed(0)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function Costs() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [expenses, setExpenses] = useState<ExpenseReport | null>(null);
  const [period, setPeriod] = useState<Period>("semestre");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const w = windowFor(period);
      const [inv, exp] = await Promise.all([
        api.listInventory(),
        api.activityExpenses(w.since, w.until),
      ]);
      setItems(inv);
      setExpenses(exp);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao carregar.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [period]);

  const { byCategory, total } = useMemo(() => {
    const map = new Map<string, number>();
    let sum = 0;
    for (const i of items) {
      const value = (i.quantity || 0) * (i.price_unit || 0);
      map.set(i.category, (map.get(i.category) ?? 0) + value);
      sum += value;
    }
    return { byCategory: [...map.entries()].sort((a, b) => b[1] - a[1]), total: sum };
  }, [items]);

  if (loading) return <Loading rows={4} label="Carregando custos" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
            Gastos por período
          </h2>
          <div className="flex gap-1 text-xs">
            {(["mes", "semestre", "ano", "tudo"] as const).map((p) => (
              <button key={p} onClick={() => setPeriod(p)}
                className={"rounded-md px-2 py-1 " + (period === p
                  ? "bg-[var(--panel-2)] text-white"
                  : "text-[var(--muted)]")}>
                {{ mes: "Mês", semestre: "Semestre", ano: "Ano", tudo: "Tudo" }[p]}
              </button>
            ))}
          </div>
        </div>
        <div className="mb-3 text-center">
          <div className="tabnum text-3xl font-bold text-white">{brl(expenses?.total ?? 0)}</div>
          <div className="text-xs text-[var(--muted)]">
            {expenses?.count ?? 0} lançamento(s) no período
          </div>
        </div>
        {expenses && expenses.by_month.length > 0 ? (
          <>
            <BarChart data={expenses.by_month} />
            <div className="mt-3 border-t border-[var(--border)] pt-3">
              <div className="mb-2 text-[0.6rem] uppercase tracking-wide text-[var(--muted)]">
                Por categoria
              </div>
              <ul className="flex flex-col gap-2">
                {expenses.by_category.map((c) => {
                  const pct = expenses.total > 0 ? (c.total / expenses.total) * 100 : 0;
                  return (
                    <li key={c.category}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="font-semibold">{c.category}</span>
                        <span className="tabnum">{brl(c.total)}</span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--panel-2)]">
                        <div className="h-full rounded-full bg-[var(--accent)]" style={{ width: `${pct}%` }} />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </>
        ) : (
          <p className="text-center text-sm text-[var(--muted)]">
            Nenhum gasto lançado no período. Registre o valor nas habitualidades para acompanhar aqui.
          </p>
        )}
      </section>

      <section className="card p-5 text-center">
        <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Valor do acervo (inventário)
        </div>
        <div className="tabnum mt-1 text-2xl font-bold text-white">{brl(total)}</div>
      </section>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Acervo por categoria
        </div>
        {byCategory.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">
            Cadastre itens com preço no inventário para ver os custos.
          </p>
        ) : (
          <ul>
            {byCategory.map(([cat, value]) => {
              const pct = total > 0 ? (value / total) * 100 : 0;
              return (
                <li key={cat} className="border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-semibold">{cat}</span>
                    <span className="tabnum">{brl(value)}</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--panel-2)]">
                    <div className="h-full rounded-full bg-[var(--accent)]" style={{ width: `${pct}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
