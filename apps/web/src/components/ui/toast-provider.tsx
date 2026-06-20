"use client";

import { useToastStore } from "@/stores/toast-store";

const toneStyles = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  error: "border-red-200 bg-red-50 text-red-900",
  info: "border-slate-200 bg-white text-slate-900",
} as const;

export function ToastProvider() {
  const items = useToastStore((state) => state.items);
  const dismiss = useToastStore((state) => state.dismiss);

  if (items.length === 0) return null;

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      aria-live="polite"
      aria-relevant="additions"
    >
      {items.map((item) => (
        <div
          key={item.id}
          role="status"
          className={`pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-lg ${toneStyles[item.tone]}`}
        >
          <div className="flex items-start justify-between gap-3">
            <p>{item.message}</p>
            <button
              type="button"
              className="text-xs opacity-70 hover:opacity-100"
              onClick={() => dismiss(item.id)}
              aria-label="Dismiss notification"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
