import { useEffect, useMemo, useState } from "react";
import { api, type InventoryItem } from "../api.ts";
import { downloadCsv, toCsv } from "../csv.ts";
import { ErrorState, Loading } from "../ui.tsx";

const CATEGORIES = ["Pólvora", "Projétil", "Espoleta", "Estojo", "Munição", "Outro"];
const UNITS = ["g", "grains", "un"];

// Limite abaixo do qual o insumo entra em "estoque baixo" — mesmos valores do
// app Streamlit. Categorias fora da tabela usam o padrão.
const LOW_STOCK: Record<string, number> = {
  "Pólvora": 100, "Projétil": 50, "Espoleta": 100, "Estojo": 50,
};
const LOW_STOCK_DEFAULT = 20;
const lowThreshold = (cat: string) => LOW_STOCK[cat] ?? LOW_STOCK_DEFAULT;

// Dias até a validade (negativo = vencido). null quando não há data.
function daysToExpiry(iso?: string | null): number | null {
  if (!iso) return null;
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - today.getTime()) / 86_400_000);
}
const EXPIRY_SOON_DAYS = 30;

export function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadErr, setLoadErr] = useState<string | null>(null);

  const [category, setCategory] = useState(CATEGORIES[0]);
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState(UNITS[0]);
  const [price, setPrice] = useState("");
  const [batch, setBatch] = useState("");
  const [expiry, setExpiry] = useState("");

  async function load() {
    setLoadErr(null);
    setLoading(true);
    try {
      setItems(await api.listInventory());
    } catch (e) {
      setLoadErr(e instanceof Error ? e.message : "Falha ao carregar.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createInventory({
        category,
        name,
        quantity: parseFloat(quantity) || 0,
        unit,
        price_unit: parseFloat(price) || 0,
        batch_number: batch || null,
        expiration_date: expiry || null,
      });
      setName(""); setQuantity(""); setPrice(""); setBatch(""); setExpiry("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao adicionar.");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    await api.deleteInventory(id);
    await load();
  }

  const [editing, setEditing] = useState<number | null>(null);
  const [editQty, setEditQty] = useState("");
  const [editPrice, setEditPrice] = useState("");

  function startEdit(i: InventoryItem) {
    setEditing(i.id);
    setEditQty(String(i.quantity));
    setEditPrice(String(i.price_unit ?? 0));
  }

  async function saveEdit(i: InventoryItem) {
    await api.updateInventory(i.id, {
      category: i.category,
      name: i.name,
      quantity: parseFloat(editQty) || 0,
      unit: i.unit,
      price_unit: parseFloat(editPrice) || 0,
      batch_number: i.batch_number ?? null,
      expiration_date: i.expiration_date ?? null,
    });
    setEditing(null);
    await load();
  }

  const [search, setSearch] = useState("");
  const [filterCat, setFilterCat] = useState("Todas");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter(
      (i) =>
        (filterCat === "Todas" || i.category === filterCat) &&
        (!q || i.name.toLowerCase().includes(q)),
    );
  }, [items, search, filterCat]);

  // Alertas de estoque e validade — como o app Streamlit destacava no topo.
  const alerts = useMemo(() => {
    const out: { severity: "erro" | "aviso"; text: string }[] = [];
    for (const i of items) {
      if (i.quantity <= 0) {
        out.push({ severity: "erro", text: `Sem estoque: ${i.name} (${i.category})` });
      } else if (i.quantity <= lowThreshold(i.category)) {
        out.push({ severity: "aviso", text: `Estoque baixo: ${i.name} — ${i.quantity} ${i.unit} restantes` });
      }
      const d = daysToExpiry(i.expiration_date);
      if (d != null && d < 0) {
        out.push({ severity: "erro", text: `Vencido: ${i.name} (validade ${i.expiration_date})` });
      } else if (d != null && d <= EXPIRY_SOON_DAYS) {
        out.push({ severity: "aviso", text: `Vence em ${d} dia(s): ${i.name} (${i.expiration_date})` });
      }
    }
    //  Erros primeiro, para o que é mais grave aparecer no topo.
    return out.sort((a, b) => (a.severity === b.severity ? 0 : a.severity === "erro" ? -1 : 1));
  }, [items]);

  function exportCsv() {
    const csv = toCsv(
      ["Categoria", "Nome", "Quantidade", "Unidade", "Preço/un", "Lote", "Validade"],
      filtered.map((i) => [
        i.category, i.name, i.quantity, i.unit, i.price_unit ?? 0,
        i.batch_number ?? "", i.expiration_date ?? "",
      ]),
    );
    downloadCsv("inventario.csv", csv);
  }

  if (loading) return <Loading rows={4} label="Carregando inventário" />;
  if (loadErr) return <ErrorState message={loadErr} onRetry={load} />;

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Adicionar item
        </h2>
        <form onSubmit={add} className="grid grid-cols-2 gap-2">
          <select className="field" value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
          <input className="field" placeholder="Nome (ex.: CBC 216)" value={name} onChange={(e) => setName(e.target.value)} required />
          <input className="field" inputMode="decimal" placeholder="Quantidade" value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
          <select className="field" value={unit} onChange={(e) => setUnit(e.target.value)}>
            {UNITS.map((u) => <option key={u}>{u}</option>)}
          </select>
          <input className="field col-span-2" inputMode="decimal" placeholder="Preço por unidade (R$)" value={price} onChange={(e) => setPrice(e.target.value)} />
          <input className="field" placeholder="Lote (opcional)" value={batch} onChange={(e) => setBatch(e.target.value)} />
          <label className="flex flex-col gap-1">
            <span className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">Validade (opcional)</span>
            <input className="field" type="date" value={expiry} onChange={(e) => setExpiry(e.target.value)} />
          </label>
          <button className="btn col-span-2" disabled={busy}>{busy ? "…" : "ADICIONAR"}</button>
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      {alerts.length > 0 && (
        <section className="flex flex-col gap-2">
          {alerts.map((a, i) => (
            <div
              key={i}
              className={
                "rounded-lg border px-3 py-2 text-sm " +
                (a.severity === "erro"
                  ? "border-red-500/50 bg-red-500/10 text-red-200"
                  : "border-amber-500/50 bg-amber-500/10 text-amber-200")
              }
            >
              <b className="mr-1">{a.severity === "erro" ? "⛔" : "⚠️"}</b>
              {a.text}
            </div>
          ))}
        </section>
      )}

      <section className="card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] px-4 py-3">
          <span className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
            Inventário ({filtered.length}/{items.length})
          </span>
          {items.length > 0 && (
            <button onClick={exportCsv} className="rounded-md border border-[var(--border)] px-3 py-1 text-xs text-[var(--muted)]">
              ⬇ CSV
            </button>
          )}
        </div>
        {items.length > 0 && (
          <div className="grid grid-cols-2 gap-2 border-b border-[var(--border)] p-3">
            <input className="field" placeholder="Buscar por nome…" value={search} onChange={(e) => setSearch(e.target.value)} />
            <select className="field" value={filterCat} onChange={(e) => setFilterCat(e.target.value)}>
              <option>Todas</option>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        )}
        {items.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">Nenhum item ainda.</p>
        ) : filtered.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">Nenhum item corresponde ao filtro.</p>
        ) : (
          <ul>
            {filtered.map((i) => (
              <li key={i.id} className="border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                {editing === i.id ? (
                  <div className="flex flex-col gap-2">
                    <div className="text-sm font-semibold">{i.name}</div>
                    <div className="grid grid-cols-2 gap-2">
                      <input className="field" inputMode="decimal" value={editQty} onChange={(e) => setEditQty(e.target.value)} placeholder={`Qtd (${i.unit})`} />
                      <input className="field" inputMode="decimal" value={editPrice} onChange={(e) => setEditPrice(e.target.value)} placeholder="Preço/un" />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(i)} className="btn" style={{ paddingBlock: 8 }}>Salvar</button>
                      <button onClick={() => setEditing(null)} className="btn btn-ghost" style={{ paddingBlock: 8 }}>Cancelar</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold">{i.name}</div>
                      <div className="text-xs text-[var(--muted)]">
                        {i.category} ·{" "}
                        <span className={
                          i.quantity <= 0 ? "text-red-400"
                            : i.quantity <= lowThreshold(i.category) ? "text-amber-400"
                            : "text-emerald-400"
                        }>
                          {i.quantity} {i.unit}
                        </span>
                        {i.price_unit > 0 && ` · R$ ${i.price_unit.toFixed(2)}/${i.unit}`}
                        {i.expiration_date && (() => {
                          const d = daysToExpiry(i.expiration_date);
                          const cls = d != null && d < 0 ? "text-red-400"
                            : d != null && d <= EXPIRY_SOON_DAYS ? "text-amber-400"
                            : "text-[var(--muted)]";
                          return <span className={cls}> · val. {i.expiration_date}</span>;
                        })()}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => startEdit(i)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">
                        Editar
                      </button>
                      <button onClick={() => remove(i.id)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
                        Remover
                      </button>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
