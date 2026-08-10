import { useEffect, useMemo, useState } from "react";
import { api, type InventoryItem } from "../api.ts";

// O custo do acervo é derivado do inventário: quantidade × preço unitário,
// somado por categoria. A API já entrega os itens; a conta mora no cliente.
export function Costs() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listInventory()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Falha ao carregar."));
  }, []);

  const { byCategory, total } = useMemo(() => {
    const map = new Map<string, number>();
    let sum = 0;
    for (const i of items) {
      const value = (i.quantity || 0) * (i.price_unit || 0);
      map.set(i.category, (map.get(i.category) ?? 0) + value);
      sum += value;
    }
    return {
      byCategory: [...map.entries()].sort((a, b) => b[1] - a[1]),
      total: sum,
    };
  }, [items]);

  const brl = (v: number) =>
    v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-5 text-center">
        <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Valor total do acervo
        </div>
        <div className="tabnum mt-1 text-3xl font-bold text-white">{brl(total)}</div>
      </section>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Por categoria
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
