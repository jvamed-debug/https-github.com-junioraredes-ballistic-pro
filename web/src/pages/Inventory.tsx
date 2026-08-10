import { useEffect, useState } from "react";
import { api, type InventoryItem } from "../api.ts";

const CATEGORIES = ["Pólvora", "Projétil", "Espoleta", "Estojo", "Munição", "Outro"];
const UNITS = ["g", "grains", "un"];

export function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [category, setCategory] = useState(CATEGORIES[0]);
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState(UNITS[0]);
  const [price, setPrice] = useState("");

  async function load() {
    try {
      setItems(await api.listInventory());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao carregar.");
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
        batch_number: null,
        expiration_date: null,
      });
      setName(""); setQuantity(""); setPrice("");
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
          <button className="btn col-span-2" disabled={busy}>{busy ? "…" : "ADICIONAR"}</button>
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Inventário ({items.length})
        </div>
        {items.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">Nenhum item ainda.</p>
        ) : (
          <ul>
            {items.map((i) => (
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
                        {i.category} · {i.quantity} {i.unit}
                        {i.price_unit > 0 && ` · R$ ${i.price_unit.toFixed(2)}/${i.unit}`}
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
