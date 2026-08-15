import { useRef, useState } from "react";
import { api, type TargetAnalysis } from "../api.ts";

export function Target() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [widthMm, setWidthMm] = useState("210");
  const [sensitivity, setSensitivity] = useState(155);
  const [center, setCenter] = useState<{ x: number; y: number } | null>(null);

  const [res, setRes] = useState<TargetAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  function pick(f: File | null) {
    setRes(null);
    setError(null);
    setCenter(null);
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : null);
  }

  // Clique no preview define o centro do alvo (para o desvio POI), em pixels da
  // imagem original — escala do tamanho exibido para o tamanho natural.
  function onPreviewClick(e: React.MouseEvent<HTMLImageElement>) {
    const img = imgRef.current;
    if (!img) return;
    const rect = img.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * img.naturalWidth);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * img.naturalHeight);
    setCenter({ x, y });
  }

  function params() {
    return {
      targetWidthMm: parseFloat(widthMm) || 210,
      sensitivity,
      centerX: center?.x ?? null,
      centerY: center?.y ?? null,
    };
  }

  async function analyze() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setRes(await api.analyzeTarget(file, params()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha na análise.");
      setRes(null);
    } finally {
      setBusy(false);
    }
  }

  async function downloadReport() {
    if (!file) return;
    setReportBusy(true);
    setError(null);
    try {
      await api.downloadTargetReport(file, params());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao gerar o relatório.");
    } finally {
      setReportBusy(false);
    }
  }

  const bestGroup = res?.groups.length
    ? Math.min(...res.groups.map((g) => g.group_size_mm))
    : null;

  return (
    <div className="flex flex-col gap-4">
      <section className="card p-4">
        <h2 className="mb-1 text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
          Análise do alvo
        </h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Envie a foto do alvo (de frente, bem iluminada). O app detecta os impactos e
          mede o agrupamento. Calibração pela largura do alvo — o padrão 210&nbsp;mm é a
          largura de uma folha A4.
        </p>

        <label className="btn btn-ghost mb-3 inline-block cursor-pointer text-center">
          {file ? "Trocar foto" : "📷 Escolher / tirar foto"}
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => pick(e.target.files?.[0] ?? null)}
          />
        </label>

        {preview && (
          <div className="mb-3">
            <img
              ref={imgRef}
              src={preview}
              onClick={onPreviewClick}
              className="w-full cursor-crosshair rounded-lg border border-[var(--border)]"
              alt="Prévia do alvo"
            />
            <p className="mt-1 text-[0.7rem] text-[var(--muted)]">
              {center
                ? `Centro definido em (${center.x}, ${center.y}). O desvio (POI) parte daí.`
                : "Toque no centro do alvo para calcular o desvio (POI) — opcional."}
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2">
          <label className="flex flex-col gap-1">
            <span className="text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">Largura do alvo (mm)</span>
            <input className="field" inputMode="decimal" value={widthMm} onChange={(e) => setWidthMm(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[0.7rem] uppercase tracking-wide text-[var(--muted)]">Sensibilidade: {sensitivity}</span>
            <input type="range" min={80} max={220} value={sensitivity} onChange={(e) => setSensitivity(parseInt(e.target.value))} className="w-full" />
          </label>
        </div>

        <button className="btn mt-3" onClick={analyze} disabled={busy || !file}>
          {busy ? "Analisando…" : "ANALISAR"}
        </button>
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </section>

      {res && (
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--muted)]">
              Resultado — {res.shot_count} impacto(s)
            </h3>
            {res.groups.length > 0 && (
              <button
                onClick={downloadReport}
                disabled={reportBusy}
                className="rounded-md border border-[var(--border)] px-3 py-1 text-xs text-[var(--muted)]"
              >
                {reportBusy ? "Gerando…" : "📄 Relatório PDF"}
              </button>
            )}
          </div>

          <img src={res.annotated_image} className="w-full" alt="Alvo analisado" />

          <div className="p-4">
            {res.groups.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">
                Nenhum impacto detectado. Tente uma foto mais nítida, de frente, ou ajuste a
                sensibilidade.
              </p>
            ) : (
              <>
                {bestGroup != null && (
                  <div className="mb-3 rounded-lg bg-[var(--panel-2)] px-3 py-2 text-center">
                    <div className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">Melhor agrupamento</div>
                    <div className="tabnum text-2xl font-bold text-[var(--accent)]">{bestGroup.toFixed(2)} mm</div>
                  </div>
                )}
                <table className="w-full tabnum text-sm">
                  <thead>
                    <tr className="text-[0.62rem] uppercase tracking-wide text-[var(--muted)]">
                      <th className="px-2 py-1 text-left">Grupo</th>
                      <th className="px-2 py-1 text-right">Impactos</th>
                      <th className="px-2 py-1 text-right">Agrup. (mm)</th>
                      <th className="px-2 py-1 text-right">Desvio POI (mm)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {res.groups.map((g) => (
                      <tr key={g.id} className="border-t border-[var(--border)]">
                        <td className="px-2 py-1 font-bold text-white">G{g.id}</td>
                        <td className="px-2 py-1 text-right">{g.shots.length}</td>
                        <td className="px-2 py-1 text-right font-bold text-[var(--up)]">{g.group_size_mm.toFixed(2)}</td>
                        <td className="px-2 py-1 text-right text-[var(--muted)]">
                          {center ? `${g.poi_mm[0] >= 0 ? "+" : ""}${g.poi_mm[0]}, ${g.poi_mm[1] >= 0 ? "+" : ""}${g.poi_mm[1]}` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-3 text-[0.7rem] leading-relaxed text-[var(--muted)]">
                  Medição automática por visão computacional: confira contra a régua se for
                  usar para ajuste fino. Impactos sobrepostos podem contar como um só.
                </p>
              </>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
