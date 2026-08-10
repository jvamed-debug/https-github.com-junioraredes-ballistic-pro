import { useEffect, useState } from "react";
import { api, type Firearm, type LogEntry } from "../api.ts";

export function Logbook() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [guns, setGuns] = useState<Firearm[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [caliber, setCaliber] = useState("");
  const [quantity, setQuantity] = useState("");
  const [powder, setPowder] = useState("");
  const [charge, setCharge] = useState("");
  const [vel, setVel] = useState("");
  const [group, setGroup] = useState("");
  const [firearmId, setFirearmId] = useState("");

  const [gunModel, setGunModel] = useState("");

  async function load() {
    try {
      const [l, g] = await Promise.all([api.listLogbook(), api.listFirearms()]);
      setLogs(l);
      setGuns(g);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao carregar.");
    }
  }
  useEffect(() => { load(); }, []);

  async function addSession(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createLog({
        caliber,
        quantity: parseInt(quantity) || 1,
        powder: powder || null,
        charge: charge ? parseFloat(charge) : null,
        velocity_avg: vel ? parseFloat(vel) : null,
        grouping_mm: group ? parseFloat(group) : null,
        firearm_id: firearmId ? parseInt(firearmId) : null,
      });
      setCaliber(""); setQuantity(""); setPowder(""); setCharge(""); setVel(""); setGroup("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao registrar.");
    } finally {
      setBusy(false);
    }
  }

  async function addGun(e: React.FormEvent) {
    e.preventDefault();
    if (!gunModel) return;
    await api.createFirearm({ model: gunModel, serial: null, sigma: null, craf: null, expiration: null });
    setGunModel("");
    await load();
  }

  const gunName = (id?: number | null) => guns.find((g) => g.id === id)?.model;

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Registrar recarga
        </h2>
        <form onSubmit={addSession} className="grid grid-cols-2 gap-2">
          <input className="field" placeholder="Calibre (ex.: .308 WIN)" value={caliber} onChange={(e) => setCaliber(e.target.value)} required />
          <input className="field" inputMode="numeric" placeholder="Quantidade" value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
          <input className="field" placeholder="Pólvora" value={powder} onChange={(e) => setPowder(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Carga (gr)" value={charge} onChange={(e) => setCharge(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Vel. média (fps)" value={vel} onChange={(e) => setVel(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Grupamento (mm)" value={group} onChange={(e) => setGroup(e.target.value)} />
          <select className="field col-span-2" value={firearmId} onChange={(e) => setFirearmId(e.target.value)}>
            <option value="">Sem arma associada</option>
            {guns.map((g) => <option key={g.id} value={g.id}>{g.model}</option>)}
          </select>
          <button className="btn col-span-2" disabled={busy}>{busy ? "…" : "REGISTRAR"}</button>
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Minhas armas ({guns.length})
        </h2>
        <form onSubmit={addGun} className="flex gap-2">
          <input className="field" placeholder="Modelo (ex.: Glock G17)" value={gunModel} onChange={(e) => setGunModel(e.target.value)} />
          <button className="btn" style={{ width: "auto", paddingInline: 16 }}>+</button>
        </form>
        {guns.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-2">
            {guns.map((g) => (
              <li key={g.id} className="flex items-center gap-2 rounded-full border border-[var(--border)] px-3 py-1 text-sm">
                {g.model}
                <button onClick={() => api.deleteFirearm(g.id).then(load)} className="text-red-400">×</button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card overflow-hidden">
        <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Histórico ({logs.length})
        </div>
        {logs.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">Nenhum registro ainda.</p>
        ) : (
          <ul>
            {logs.map((s) => (
              <li key={s.id} className="flex items-center justify-between border-t border-[var(--border)] px-4 py-3 first:border-t-0">
                <div>
                  <div className="font-semibold">
                    {s.caliber} <span className="text-[var(--muted)]">× {s.quantity}</span>
                  </div>
                  <div className="text-xs text-[var(--muted)]">
                    {s.date}
                    {s.powder && ` · ${s.powder}`}
                    {s.charge != null && ` ${s.charge}gr`}
                    {s.velocity_avg != null && ` · ${s.velocity_avg} fps`}
                    {s.grouping_mm != null && ` · ${s.grouping_mm}mm`}
                    {gunName(s.firearm_id) && ` · ${gunName(s.firearm_id)}`}
                  </div>
                </div>
                <button onClick={() => api.deleteLog(s.id).then(load)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
                  Remover
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
