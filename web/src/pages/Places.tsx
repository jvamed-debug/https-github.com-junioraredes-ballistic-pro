import { useEffect, useMemo, useState } from "react";
import { api, type Place, type PlaceKind } from "../api.ts";
import { EmptyState, ErrorState, Loading } from "../ui.tsx";

const KINDS: Array<{ id: PlaceKind; label: string; icon: string }> = [
  { id: "clube", label: "Clube", icon: "🏛️" },
  { id: "loja", label: "Loja", icon: "🛒" },
  { id: "estande", label: "Estande", icon: "🎯" },
  { id: "outro", label: "Outro", icon: "📍" },
];
// Alvo de navegação: usa coordenadas quando houver, senão o endereço/cidade.
function navTarget(p: Place): { hasCoords: boolean; query: string } {
  if (p.lat != null && p.lng != null) {
    return { hasCoords: true, query: `${p.lat},${p.lng}` };
  }
  return { hasCoords: false, query: [p.address, p.city].filter(Boolean).join(", ") || p.name };
}
function mapsUrl(p: Place): string {
  const { query } = navTarget(p);
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}
function wazeUrl(p: Place): string {
  const { hasCoords, query } = navTarget(p);
  return hasCoords
    ? `https://waze.com/ul?ll=${encodeURIComponent(query)}&navigate=yes`
    : `https://waze.com/ul?q=${encodeURIComponent(query)}&navigate=yes`;
}

const EMPTY = {
  name: "", kind: "clube" as PlaceKind, address: "", city: "",
  lat: "", lng: "", phone: "", url: "", notes: "",
};

export function Places() {
  const [list, setList] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY });

  async function load() {
    setLoadErr(null);
    setLoading(true);
    try {
      setList(await api.listPlaces());
    } catch (e) {
      setLoadErr(e instanceof Error ? e.message : "Falha ao carregar.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  function set<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function startEdit(p: Place) {
    setEditing(p.id);
    setForm({
      name: p.name, kind: p.kind, address: p.address ?? "", city: p.city ?? "",
      lat: p.lat != null ? String(p.lat) : "", lng: p.lng != null ? String(p.lng) : "",
      phone: p.phone ?? "", url: p.url ?? "", notes: p.notes ?? "",
    });
    setError(null);
  }

  function cancel() { setEditing(null); setForm({ ...EMPTY }); setError(null); }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const body = {
      name: form.name, kind: form.kind,
      address: form.address || null, city: form.city || null,
      lat: form.lat ? parseFloat(form.lat) : null,
      lng: form.lng ? parseFloat(form.lng) : null,
      phone: form.phone || null, url: form.url || null, notes: form.notes || null,
    };
    try {
      if (editing) await api.updatePlace(editing, body);
      else await api.createPlace(body);
      cancel();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar.");
    } finally {
      setBusy(false);
    }
  }

  const byKind = useMemo(() => {
    return KINDS
      .map((k) => ({ ...k, places: list.filter((p) => p.kind === k.id) }))
      .filter((g) => g.places.length > 0);
  }, [list]);

  if (loading) return <Loading rows={4} label="Carregando locais" />;
  if (loadErr) return <ErrorState message={loadErr} onRetry={load} />;

  return (
    <div className="flex flex-col gap-4">
      {list.length === 0 && (
        <EmptyState icon="🗺️" title="Nenhum local" hint="Cadastre clubes, lojas e estandes para navegar até eles com um toque." />
      )}

      {byKind.map((g) => (
        <section key={g.id} className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
              {g.icon} {g.label}s
            </h2>
            <span className="text-xs text-[var(--muted)]">{g.places.length}</span>
          </div>
          <ul>
            {g.places.map((p) => {
              const loc = [p.address, p.city].filter(Boolean).join(", ");
              const canNav = (p.lat != null && p.lng != null) || !!loc;
              return (
                <li key={p.id} className="border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                  <div className="flex items-start justify-between">
                    <div className="flex flex-col gap-0.5">
                      <div className="font-semibold">{p.name}</div>
                      {loc && <div className="text-xs text-[var(--muted)]">{loc}</div>}
                      {p.phone && (
                        <a href={`tel:${p.phone}`} className="text-xs text-[var(--accent)]">📞 {p.phone}</a>
                      )}
                      {p.url && (
                        <a href={p.url} target="_blank" rel="noreferrer" className="text-xs text-[var(--accent)] underline">
                          🔗 site
                        </a>
                      )}
                      {p.notes && <div className="text-xs text-[var(--muted)]">{p.notes}</div>}
                    </div>
                    <div className="flex gap-1">
                      <button onClick={() => startEdit(p)}
                        className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">
                        Editar
                      </button>
                      <button onClick={() => api.deletePlace(p.id).then(load)}
                        aria-label="Remover local"
                        className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
                        Remover
                      </button>
                    </div>
                  </div>
                  {canNav && (
                    <div className="mt-2 flex gap-2">
                      <a href={mapsUrl(p)} target="_blank" rel="noreferrer"
                        className="flex-1 rounded-md bg-[var(--panel-2)] px-3 py-2 text-center text-xs font-semibold text-[var(--accent)]">
                        🧭 Google Maps
                      </a>
                      <a href={wazeUrl(p)} target="_blank" rel="noreferrer"
                        className="flex-1 rounded-md bg-[var(--panel-2)] px-3 py-2 text-center text-xs font-semibold text-[var(--accent)]">
                        🚗 Waze
                      </a>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ))}

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          {editing ? "Editar local" : "Adicionar local"}
        </h2>
        <form onSubmit={save} className="grid grid-cols-2 gap-2">
          <input className="field col-span-2" placeholder="Nome (ex.: Clube de Tiro Alfa)"
            value={form.name} onChange={(e) => set("name", e.target.value)} required />
          <select className="field col-span-2" value={form.kind}
            onChange={(e) => set("kind", e.target.value as PlaceKind)}>
            {KINDS.map((k) => <option key={k.id} value={k.id}>{k.label}</option>)}
          </select>
          <input className="field col-span-2" placeholder="Endereço (opcional)"
            value={form.address} onChange={(e) => set("address", e.target.value)} />
          <input className="field" placeholder="Cidade"
            value={form.city} onChange={(e) => set("city", e.target.value)} />
          <input className="field" placeholder="Telefone"
            value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Latitude (opcional)"
            value={form.lat} onChange={(e) => set("lat", e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Longitude (opcional)"
            value={form.lng} onChange={(e) => set("lng", e.target.value)} />
          <input className="field col-span-2" placeholder="Site (opcional)"
            value={form.url} onChange={(e) => set("url", e.target.value)} />
          <input className="field col-span-2" placeholder="Observações (opcional)"
            value={form.notes} onChange={(e) => set("notes", e.target.value)} />
          <p className="col-span-2 text-[0.6rem] text-[var(--muted)]">
            Dica: com endereço ou coordenadas, os botões de navegação abrem Google Maps e Waze.
          </p>
          <button className="btn col-span-2" disabled={busy}>
            {busy ? "…" : editing ? "SALVAR" : "ADICIONAR"}
          </button>
          {editing && (
            <button type="button" onClick={cancel}
              className="col-span-2 rounded-md border border-[var(--border)] py-2 text-sm text-[var(--muted)]">
              Cancelar
            </button>
          )}
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>
    </div>
  );
}
