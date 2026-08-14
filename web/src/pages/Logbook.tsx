import { useEffect, useState } from "react";
import { api, type Firearm, type LogEntry, type ReloadWarning } from "../api.ts";
import { downloadCsv, toCsv } from "../csv.ts";

export function Logbook() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [guns, setGuns] = useState<Firearm[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [caliber, setCaliber] = useState("");
  const [quantity, setQuantity] = useState("");
  const [powder, setPowder] = useState("");
  const [charge, setCharge] = useState("");
  const [primer, setPrimer] = useState("");
  const [vel, setVel] = useState("");
  const [group, setGroup] = useState("");
  const [firearmId, setFirearmId] = useState("");
  const [deduct, setDeduct] = useState(true);

  const [warnings, setWarnings] = useState<ReloadWarning[]>([]);
  const [saveInfo, setSaveInfo] = useState<{ deductions: string[]; unit_cost: number | null } | null>(null);

  const [gunModel, setGunModel] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);

  function resetForm() {
    setCaliber(""); setQuantity(""); setPowder(""); setCharge(""); setPrimer(""); setVel(""); setGroup(""); setFirearmId("");
    setEditingId(null);
    setWarnings([]);
  }

  function startEdit(s: LogEntry) {
    setEditingId(s.id);
    setCaliber(s.caliber);
    setQuantity(String(s.quantity));
    setPowder(s.powder ?? "");
    setCharge(s.charge != null ? String(s.charge) : "");
    setPrimer(s.primer ?? "");
    setVel(s.velocity_avg != null ? String(s.velocity_avg) : "");
    setGroup(s.grouping_mm != null ? String(s.grouping_mm) : "");
    setFirearmId(s.firearm_id != null ? String(s.firearm_id) : "");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Avisos de segurança em tempo real, cruzando calibre/pólvora/espoleta — os
  // mesmos alertas que o app Streamlit mostrava ao salvar a sessão.
  useEffect(() => {
    if (!caliber) {
      setWarnings([]);
      return;
    }
    let alive = true;
    const t = setTimeout(() => {
      api
        .reloadWarnings({ caliber, powder, primer })
        .then((r) => alive && setWarnings(r.warnings))
        .catch(() => alive && setWarnings([]));
    }, 300);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [caliber, powder, primer]);

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

  async function submitSession(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaveInfo(null);
    setBusy(true);
    const payload = {
      caliber,
      quantity: parseInt(quantity) || 1,
      powder: powder || null,
      charge: charge ? parseFloat(charge) : null,
      primer: primer || null,
      velocity_avg: vel ? parseFloat(vel) : null,
      grouping_mm: group ? parseFloat(group) : null,
      firearm_id: firearmId ? parseInt(firearmId) : null,
    };
    try {
      if (editingId != null) {
        await api.updateLog(editingId, payload);
      } else {
        const r = await api.createLog(payload, deduct);
        if (deduct) setSaveInfo({ deductions: r.deductions, unit_cost: r.unit_cost });
      }
      resetForm();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar.");
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

  function exportCsv() {
    const csv = toCsv(
      ["Data", "Calibre", "Qtd", "Pólvora", "Carga(gr)", "Vel(fps)", "SD", "Agrup(mm)", "Arma"],
      logs.map((s) => [
        s.date, s.caliber, s.quantity, s.powder ?? "", s.charge ?? "",
        s.velocity_avg ?? "", s.velocity_sd ?? "", s.grouping_mm ?? "",
        gunName(s.firearm_id) ?? "",
      ]),
    );
    downloadCsv("logbook.csv", csv);
  }

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          {editingId != null ? "Editar recarga" : "Registrar recarga"}
        </h2>
        <form onSubmit={submitSession} className="grid grid-cols-2 gap-2">
          <input className="field" placeholder="Calibre (ex.: .308 WIN)" value={caliber} onChange={(e) => setCaliber(e.target.value)} required />
          <input className="field" inputMode="numeric" placeholder="Quantidade" value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
          <input className="field" placeholder="Pólvora" value={powder} onChange={(e) => setPowder(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Carga (gr)" value={charge} onChange={(e) => setCharge(e.target.value)} />
          <input className="field" placeholder="Espoleta (ex.: Small Pistol)" value={primer} onChange={(e) => setPrimer(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Vel. média (fps)" value={vel} onChange={(e) => setVel(e.target.value)} />
          <input className="field" inputMode="decimal" placeholder="Grupamento (mm)" value={group} onChange={(e) => setGroup(e.target.value)} />
          <select className="field" value={firearmId} onChange={(e) => setFirearmId(e.target.value)}>
            <option value="">Sem arma associada</option>
            {guns.map((g) => <option key={g.id} value={g.id}>{g.model}</option>)}
          </select>

          {warnings.length > 0 && (
            <div className="col-span-2 flex flex-col gap-2">
              {warnings.map((w, i) => (
                <div
                  key={i}
                  className={
                    "rounded-lg border px-3 py-2 text-sm " +
                    (w.severity === "erro"
                      ? "border-red-500/50 bg-red-500/10 text-red-200"
                      : "border-amber-500/50 bg-amber-500/10 text-amber-200")
                  }
                >
                  <b className="mr-1">{w.severity === "erro" ? "⛔" : "⚠️"}</b>
                  {w.message}
                </div>
              ))}
            </div>
          )}

          {editingId == null && (
            <label className="col-span-2 flex items-center gap-2 text-sm text-[var(--muted)]">
              <input type="checkbox" checked={deduct} onChange={(e) => setDeduct(e.target.checked)} />
              Deduzir insumos do estoque ao salvar
            </label>
          )}

          {editingId != null ? (
            <div className="col-span-2 flex gap-2">
              <button className="btn" disabled={busy}>{busy ? "…" : "SALVAR"}</button>
              <button type="button" className="btn btn-ghost" onClick={resetForm}>Cancelar</button>
            </div>
          ) : (
            <button className="btn col-span-2" disabled={busy}>{busy ? "…" : "REGISTRAR"}</button>
          )}
        </form>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
        {saveInfo && (
          <div className="mt-3 rounded-lg border border-[var(--border)] bg-[var(--panel-2)] p-3 text-sm">
            <div className="mb-1 font-semibold text-emerald-300">Sessão salva.</div>
            {saveInfo.unit_cost != null && (
              <div className="text-[var(--muted)]">
                Custo estimado:{" "}
                <b className="text-white">R$ {saveInfo.unit_cost.toFixed(2)}/un</b>
              </div>
            )}
            {saveInfo.deductions.length > 0 ? (
              <ul className="mt-1 list-inside list-disc text-xs text-[var(--muted)]">
                {saveInfo.deductions.map((d, i) => <li key={i}>{d}</li>)}
              </ul>
            ) : (
              <div className="mt-1 text-xs text-[var(--muted)]">
                Nenhum insumo correspondente no estoque para deduzir.
              </div>
            )}
          </div>
        )}
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
        <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <span className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
            Histórico ({logs.length})
          </span>
          {logs.length > 0 && (
            <button onClick={exportCsv} className="rounded-md border border-[var(--border)] px-3 py-1 text-xs text-[var(--muted)]">
              ⬇ CSV
            </button>
          )}
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
                <div className="flex gap-2">
                  <button
                    onClick={() => api.downloadLabel(s.id).catch((e) => setError(e instanceof Error ? e.message : "Falha ao gerar etiqueta."))}
                    className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]"
                  >
                    Etiqueta
                  </button>
                  <button onClick={() => startEdit(s)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)]">
                    Editar
                  </button>
                  <button onClick={() => api.deleteLog(s.id).then(load)} className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-red-400">
                    Remover
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
