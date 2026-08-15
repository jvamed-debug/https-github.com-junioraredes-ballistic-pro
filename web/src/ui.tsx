// Blocos de estado reusáveis: carregando (skeleton), erro (com "tentar
// novamente") e vazio. Padroniza o que antes era "Carregando…" seco e falhas
// silenciosas espalhadas pelas telas.

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />;
}

// Algumas linhas de skeleton dentro de um card — placeholder honesto do que vem.
export function Loading({ rows = 3, label = "Carregando" }: { rows?: number; label?: string }) {
  return (
    <div className="card flex flex-col gap-3 p-4" role="status" aria-label={label}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card p-4" role="alert">
      <p className="text-sm text-red-300">⚠️ {message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-ghost mt-3" style={{ width: "auto", paddingInline: 16 }}>
          Tentar novamente
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon = "📭", title, hint }: { icon?: string; title: string; hint?: string }) {
  return (
    <div className="card p-6 text-center">
      <div className="text-2xl">{icon}</div>
      <p className="mt-2 text-sm font-semibold">{title}</p>
      {hint && <p className="mt-1 text-xs text-[var(--muted)]">{hint}</p>}
    </div>
  );
}
