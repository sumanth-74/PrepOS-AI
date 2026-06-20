import type { CopilotPersona } from "@/features/copilot/types";

export const COPILOT_SUGGESTED_PROMPTS: Record<CopilotPersona, string[]> = {
  student: [
    "What should I study next?",
    "What is my plan for today?",
    "Show my goal forecast",
    "What if I study 10 hours per week?",
    "How far am I from my goal?",
    "What milestones have I achieved?",
  ],
  mentor: [
    "What should this student focus on?",
    "Show recommended interventions",
    "Show cohort summary",
    "Which students are at risk?",
    "What coaching worked best?",
    "Summarize this student",
  ],
  admin: [
    "Platform health",
    "Institution health",
    "Segment distribution",
    "Intervention summary",
  ],
};

export const COPILOT_PERSONA_LABELS: Record<CopilotPersona, string> = {
  student: "Student Copilot",
  mentor: "Mentor Copilot",
  admin: "Admin Copilot",
};
