"use client";

import { CopilotPanel } from "@/features/copilot/components/copilot-panel";
import { useCopilot } from "@/features/copilot/hooks/use-copilot";

export function CopilotLauncher() {
  const controller = useCopilot();
  const { open, setOpen, persona, personaLabel } = controller;

  if (!persona) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 z-50 flex flex-col items-start gap-3">
      {open ? <CopilotPanel controller={controller} onClose={() => setOpen(false)} /> : null}
      <button
        type="button"
        className="btn-primary rounded-full px-4 py-3 shadow-lg"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        aria-controls="copilot-panel-title"
        aria-label={open ? "Close copilot" : `Open ${personaLabel}`}
      >
        {open ? "Hide Copilot" : "Copilot"}
      </button>
    </div>
  );
}
