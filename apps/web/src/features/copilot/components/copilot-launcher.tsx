"use client";

import { AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";

import { CopilotPanel } from "@/features/copilot/components/copilot-panel";
import { useCopilot } from "@/features/copilot/hooks/use-copilot";
import { cn } from "@/lib/utils/cn";

export function CopilotLauncher() {
  const controller = useCopilot();
  const { open, setOpen, persona, personaLabel } = controller;

  if (!persona) {
    return null;
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      <AnimatePresence mode="wait">
        {open ? (
          <CopilotPanel key="panel" controller={controller} onClose={() => setOpen(false)} />
        ) : null}
      </AnimatePresence>
      <button
        type="button"
        className={cn(
          "group flex items-center gap-2 rounded-full bg-gradient-growth px-4 py-3.5 text-sm font-semibold text-white shadow-glow transition-all duration-300",
          "hover:shadow-glow-lg hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-growth-500 focus-visible:ring-offset-2",
          open && "rounded-2xl",
        )}
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        aria-controls="copilot-panel-title"
        aria-label={open ? "Close copilot" : `Open ${personaLabel}`}
      >
        <Sparkles className={cn("h-5 w-5 transition-transform", open && "rotate-12")} />
        <span className="hidden sm:inline">{open ? "Close" : "AI Copilot"}</span>
      </button>
    </div>
  );
}
