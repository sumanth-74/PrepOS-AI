interface LoadingSkeletonProps {
  rows?: number;
  className?: string;
}

export function LoadingSkeleton({ rows = 3, className = "" }: LoadingSkeletonProps) {
  return (
    <div className={`animate-pulse space-y-3 ${className}`} role="status" aria-live="polite">
      <span className="sr-only">Loading...</span>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="rounded-lg bg-slate-200/80 h-12 w-full" />
      ))}
    </div>
  );
}

export function KpiSkeletonGrid({ count = 4 }: { count?: number }) {
  return (
    <div
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      role="status"
      aria-live="polite"
    >
      <span className="sr-only">Loading...</span>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="card animate-pulse space-y-3">
          <div className="h-3 w-24 rounded bg-slate-200" />
          <div className="h-8 w-16 rounded bg-slate-200" />
        </div>
      ))}
    </div>
  );
}
