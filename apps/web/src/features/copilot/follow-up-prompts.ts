export const COPILOT_FOLLOW_UPS: Record<string, string[]> = {
  study_next: [
    "Why is this my top priority?",
    "How long should I spend on it today?",
    "What PYQ topics relate to this?",
  ],
  weak_concepts_priority: [
    "Create a revision plan for these",
    "Which has highest PYQ frequency?",
    "Show my readiness gap",
  ],
  highest_score_improvement: [
    "What activity type works best for me?",
    "Schedule this in my study plan",
    "Explain the readiness impact",
  ],
  student_focus_areas: [
    "What intervention should I use?",
    "Forecast their goal probability",
    "Show cohort comparison",
  ],
  default: [
    "What should I do next?",
    "Summarize my progress this week",
    "What am I at risk of missing?",
  ],
};

export function followUpsForIntent(intent?: string): string[] {
  if (!intent) return COPILOT_FOLLOW_UPS.default;
  return COPILOT_FOLLOW_UPS[intent] ?? COPILOT_FOLLOW_UPS.default;
}
