import { useMemo, useState } from "react";
import { LEG_CATEGORIES, LEG_DISCLAIMER, LEG_ITEMS } from "../content/legislacao.ts";

export function Legislacao() {
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  const items = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return LEG_ITEMS.filter((i) => {
      if (cat && i.category !== cat) return false;
      if (!needle) return true;
      return (
        i.title.toLowerCase().includes(needle) ||
        i.summary.toLowerCase().includes(needle) ||
        i.points.some((p) => p.toLowerCase().includes(needle))
      );
    });
  }, [q, cat]);

  return (
    <div className="flex flex-col gap-4">
      <section className="card border border-[var(--wind)]/40 p-3 text-xs text-[var(--muted)]">
        ⚖️ {LEG_DISCLAIMER}
      </section>

      <input
        className="field"
        placeholder="Buscar na legislação (CR, GT, habitualidade…)"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Buscar na legislação"
      />

      <div className="flex flex-wrap gap-1 text-xs">
        <button onClick={() => setCat(null)}
          className={"rounded-md px-2 py-1 " + (cat === null ? "bg-[var(--panel-2)] text-white" : "text-[var(--muted)]")}>
          Tudo
        </button>
        {LEG_CATEGORIES.map((c) => (
          <button key={c} onClick={() => setCat(c)}
            className={"rounded-md px-2 py-1 " + (cat === c ? "bg-[var(--panel-2)] text-white" : "text-[var(--muted)]")}>
            {c}
          </button>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">Nada encontrado para essa busca.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((i) => {
            const isOpen = open === i.id;
            return (
              <li key={i.id} className="card overflow-hidden">
                <button
                  onClick={() => setOpen(isOpen ? null : i.id)}
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between px-4 py-3 text-left"
                >
                  <span>
                    <span className="text-[0.6rem] uppercase tracking-wide text-[var(--accent)]">{i.category}</span>
                    <span className="block font-semibold">{i.title}</span>
                  </span>
                  <span className="text-[var(--muted)]">{isOpen ? "−" : "+"}</span>
                </button>
                {isOpen && (
                  <div className="border-t border-[var(--border)] px-4 py-3">
                    <p className="mb-2 text-sm text-[var(--muted)]">{i.summary}</p>
                    <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
                      {i.points.map((p, k) => <li key={k}>{p}</li>)}
                    </ul>
                    {i.source && (
                      <a href={i.source.url} target="_blank" rel="noreferrer"
                        className="mt-3 inline-block text-xs text-[var(--accent)] underline">
                        📖 {i.source.label}
                      </a>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
