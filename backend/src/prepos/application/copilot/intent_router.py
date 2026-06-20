from __future__ import annotations

import re
from dataclasses import dataclass

from prepos.application.copilot.dto import CopilotPersona

_UNKNOWN_INTENT = "unknown"


@dataclass(frozen=True, slots=True)
class IntentMatch:
    intent: str
    score: int


@dataclass(frozen=True, slots=True)
class IntentDefinition:
    intent: str
    persona: CopilotPersona
    phrases: tuple[str, ...]


_CONTENT_INTENT_DEFINITIONS: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        intent="define_concept",
        persona="student",
        phrases=(
            "define ",
            "definition of",
            "meaning of",
            "what does",
            "what do",
        ),
    ),
    IntentDefinition(
        intent="what_is",
        persona="student",
        phrases=(
            "what is ",
            "what are ",
        ),
    ),
    IntentDefinition(
        intent="explain_topic",
        persona="student",
        phrases=(
            "tell me about",
            "describe the",
            "describe ",
        ),
    ),
    IntentDefinition(
        intent="explain_concept",
        persona="student",
        phrases=(
            "explain the",
            "explain ",
        ),
    ),
)

_STUDENT_PYQ_INTENT_DEFINITIONS: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        intent="show_pyqs",
        persona="student",
        phrases=(
            "show pyqs on",
            "show pyq on",
            "previous year questions on",
            "pyqs on",
            "pyq on",
            "has article",
            "appeared in upsc",
            "asked before on",
        ),
    ),
    IntentDefinition(
        intent="pyq_trends",
        persona="student",
        phrases=(
            "pyq trends",
            "trending pyq",
            "important pyq themes",
            "pyq themes for",
        ),
    ),
    IntentDefinition(
        intent="topic_importance",
        persona="student",
        phrases=(
            "important pyq themes",
            "important questions for",
            "topic importance for",
            "high yield pyq",
        ),
    ),
    IntentDefinition(
        intent="exam_probability",
        persona="student",
        phrases=(
            "exam probability",
            "likely to be asked",
            "probability of",
            "chances of being asked",
        ),
    ),
)

_MENTOR_PYQ_INTENT_DEFINITIONS: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        intent="pyq_revision",
        persona="mentor",
        phrases=(
            "which pyqs should this student revise",
            "pyqs should this student revise",
            "pyq revision for this student",
        ),
    ),
    IntentDefinition(
        intent="high_frequency_weak_concepts",
        persona="mentor",
        phrases=(
            "high-frequency weak concepts",
            "high frequency weak concepts",
            "weak high yield pyq",
            "pyq weak concepts for this student",
        ),
    ),
    IntentDefinition(
        intent="show_pyqs",
        persona="mentor",
        phrases=(
            "show pyqs for this student on",
            "previous year questions for this student",
            "pyqs on",
        ),
    ),
    IntentDefinition(
        intent="pyq_trends",
        persona="mentor",
        phrases=(
            "pyq trends for this student",
            "trending pyq topics",
        ),
    ),
    IntentDefinition(
        intent="topic_importance",
        persona="mentor",
        phrases=(
            "important pyq themes for this student",
            "topic importance for this student",
        ),
    ),
    IntentDefinition(
        intent="exam_probability",
        persona="mentor",
        phrases=(
            "exam probability for this student",
            "likely pyq topics for this student",
        ),
    ),
)

_MENTOR_CONTENT_INTENT_DEFINITIONS: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        intent="explain_student_weakness",
        persona="mentor",
        phrases=(
            "explain this student's weakest concept",
            "student's weakest concept",
            "explain student weakness",
            "weakest concept for this student",
        ),
    ),
    IntentDefinition(
        intent="concept_revision_strategy",
        persona="mentor",
        phrases=(
            "what should this student revise next",
            "what should this student revise",
            "revision strategy for this student",
            "concept revision strategy",
        ),
    ),
    IntentDefinition(
        intent="coaching_guidance",
        persona="mentor",
        phrases=(
            "give coaching guidance for",
            "give coaching guidance",
            "coaching guidance for",
            "coaching guidance",
            "how should i coach",
        ),
    ),
    IntentDefinition(
        intent="explain_topic",
        persona="mentor",
        phrases=(
            "summarize article 356 for mentoring",
            "summarize for mentoring",
            "summarize article",
            "tell me about",
            "describe the",
            "describe ",
        ),
    ),
    IntentDefinition(
        intent="explain_concept",
        persona="mentor",
        phrases=(
            "explain the concept",
            "explain this concept",
            "explain concept",
            "explain the",
            "explain ",
        ),
    ),
)

_INTENT_DEFINITIONS: tuple[IntentDefinition, ...] = (
    _CONTENT_INTENT_DEFINITIONS
    + _STUDENT_PYQ_INTENT_DEFINITIONS
    + _MENTOR_CONTENT_INTENT_DEFINITIONS
    + _MENTOR_PYQ_INTENT_DEFINITIONS
    + (
    IntentDefinition(
        intent="readiness_low",
        persona="student",
        phrases=(
            "why is my readiness low",
            "readiness low",
            "low readiness",
            "why readiness",
        ),
    ),
    IntentDefinition(
        intent="study_today",
        persona="student",
        phrases=(
            "what should i study today",
            "study today",
            "today plan",
            "today's plan",
        ),
    ),
    IntentDefinition(
        intent="study_next",
        persona="student",
        phrases=(
            "what should i study next",
            "study next",
            "what to study next",
        ),
    ),
    IntentDefinition(
        intent="highest_score_improvement",
        persona="student",
        phrases=(
            "biggest score improvement",
            "highest score improvement",
            "what gives me the biggest score improvement",
            "largest readiness gain",
        ),
    ),
    IntentDefinition(
        intent="weak_concepts_priority",
        persona="student",
        phrases=(
            "which weak concepts matter most",
            "weak concepts matter most",
            "weak concepts priority",
            "prioritize weak concepts",
        ),
    ),
    IntentDefinition(
        intent="important_topics",
        persona="student",
        phrases=(
            "which topics are important for upsc",
            "important topics for upsc",
            "most important topics",
            "high impact topics",
        ),
    ),
    IntentDefinition(
        intent="weekly_focus",
        persona="student",
        phrases=(
            "what should i focus on this week",
            "weekly focus",
            "focus this week",
        ),
    ),
    IntentDefinition(
        intent="pyq_priority_topics",
        persona="student",
        phrases=(
            "pyq priority topics",
            "weak areas in pyqs",
            "pyq weak areas",
            "frequently asked weak topics",
        ),
    ),
    IntentDefinition(
        intent="current_affairs_priority",
        persona="student",
        phrases=(
            "current affairs priority",
            "current affairs linked to my weak concepts",
            "current affairs revision priority",
        ),
    ),
    IntentDefinition(
        intent="weakest_concepts",
        persona="student",
        phrases=(
            "weakest concepts",
            "weak concepts",
            "weaknesses",
            "weakest areas",
        ),
    ),
    IntentDefinition(
        intent="recommendation_why",
        persona="student",
        phrases=(
            "why was this recommendation",
            "why recommendation",
            "recommendation generated",
            "why recommend",
        ),
    ),
    IntentDefinition(
        intent="goal_on_track",
        persona="student",
        phrases=(
            "am i on track",
            "on track for my goal",
            "on track for goal",
            "goal on track",
            "reach my goal",
        ),
    ),
    IntentDefinition(
        intent="next_activities",
        persona="student",
        phrases=(
            "activities should i complete",
            "what activities",
            "next activities",
            "what should i do next",
            "complete next",
        ),
    ),
    IntentDefinition(
        intent="recommendation_progress",
        persona="student",
        phrases=(
            "recommendation progress",
            "did my study improve readiness",
            "how much progress did i make",
        ),
    ),
    IntentDefinition(
        intent="learning_progress",
        persona="student",
        phrases=(
            "learning progress",
            "my learning progress",
            "show my progress",
        ),
    ),
    IntentDefinition(
        intent="best_improvements",
        persona="student",
        phrases=(
            "what helped me most this month",
            "best improvements",
            "which concept improved the most",
        ),
    ),
    IntentDefinition(
        intent="study_effectiveness",
        persona="student",
        phrases=(
            "study effectiveness",
            "which recommendations worked best",
            "recommendation effectiveness",
        ),
    ),
    IntentDefinition(
        intent="progress_summary",
        persona="student",
        phrases=(
            "progress summary",
            "my progress summary",
            "summarize my progress",
        ),
    ),
    IntentDefinition(
        intent="learning_history",
        persona="student",
        phrases=(
            "show my learning history",
            "learning history",
            "what have i improved recently",
        ),
    ),
    IntentDefinition(
        intent="progress_timeline",
        persona="student",
        phrases=(
            "progress timeline",
            "show my progress timeline",
            "learning timeline",
        ),
    ),
    IntentDefinition(
        intent="past_recommendations",
        persona="student",
        phrases=(
            "past recommendations",
            "what recommendations worked best",
            "previous recommendations",
        ),
    ),
    IntentDefinition(
        intent="milestones",
        persona="student",
        phrases=(
            "what milestones have i achieved",
            "show my milestones",
            "milestones achieved",
        ),
    ),
    IntentDefinition(
        intent="generate_week_plan",
        persona="student",
        phrases=(
            "generate my week plan",
            "generate weekly plan",
            "create my study plan for this week",
        ),
    ),
    IntentDefinition(
        intent="today_plan",
        persona="student",
        phrases=(
            "what is my plan for today",
            "today plan",
            "what should i study today plan",
        ),
    ),
    IntentDefinition(
        intent="why_this_plan",
        persona="student",
        phrases=(
            "why this plan",
            "explain my plan",
            "why was this plan generated",
        ),
    ),
    IntentDefinition(
        intent="next_best_topic",
        persona="student",
        phrases=(
            "next best topic",
            "what is my next best topic",
            "top priority topic today",
        ),
    ),
    IntentDefinition(
        intent="plan_progress",
        persona="student",
        phrases=(
            "plan progress",
            "how am i doing on my plan",
            "study plan progress",
        ),
    ),
    IntentDefinition(
        intent="goal_forecast",
        persona="student",
        phrases=(
            "goal forecast",
            "show my goal forecast",
            "what is my readiness forecast",
        ),
    ),
    IntentDefinition(
        intent="target_probability",
        persona="student",
        phrases=(
            "target probability",
            "probability of reaching my goal",
            "chance of hitting my target",
        ),
    ),
    IntentDefinition(
        intent="what_if_scenario",
        persona="student",
        phrases=(
            "what if scenario",
            "what if i study more",
            "simulate study hours",
        ),
    ),
    IntentDefinition(
        intent="readiness_projection",
        persona="student",
        phrases=(
            "readiness projection",
            "where will my readiness be",
            "project my readiness",
        ),
    ),
    IntentDefinition(
        intent="goal_gap",
        persona="student",
        phrases=(
            "goal gap",
            "how far am i from my goal",
            "gap to my target readiness",
        ),
    ),
    IntentDefinition(
        intent="best_improvement_path",
        persona="student",
        phrases=(
            "best improvement path",
            "fastest way to improve readiness",
            "what improves my score most",
        ),
    ),
    IntentDefinition(
        intent="why_did_mentor_assign_this",
        persona="student",
        phrases=(
            "why did mentor assign this",
            "why this intervention",
            "why was this assigned",
        ),
    ),
    IntentDefinition(
        intent="intervention_history",
        persona="student",
        phrases=(
            "intervention history",
            "show my intervention history",
            "mentor intervention history",
        ),
    ),
    IntentDefinition(
        intent="intervention_progress",
        persona="student",
        phrases=(
            "intervention progress",
            "how is my intervention going",
            "track intervention progress",
        ),
    ),
    IntentDefinition(
        intent="summarize_student",
        persona="mentor",
        phrases=(
            "summarize this student",
            "student summary",
            "summarize student",
            "overview of student",
        ),
    ),
    IntentDefinition(
        intent="student_focus_areas",
        persona="mentor",
        phrases=(
            "what should this student focus on",
            "student focus areas",
            "focus areas for this student",
        ),
    ),
    IntentDefinition(
        intent="highest_impact_intervention",
        persona="mentor",
        phrases=(
            "which intervention improves readiness fastest",
            "highest impact intervention",
            "fastest readiness improvement",
        ),
    ),
    IntentDefinition(
        intent="current_affairs_revision",
        persona="mentor",
        phrases=(
            "current affairs revision for this student",
            "current affairs linked to student weaknesses",
        ),
    ),
    IntentDefinition(
        intent="student_priority_plan",
        persona="mentor",
        phrases=(
            "student priority plan",
            "priority plan for this student",
            "weekly plan for this student",
        ),
    ),
    IntentDefinition(
        intent="effective_interventions",
        persona="mentor",
        phrases=(
            "which interventions worked",
            "effective interventions",
            "what improved readiness fastest",
        ),
    ),
    IntentDefinition(
        intent="failed_interventions",
        persona="mentor",
        phrases=(
            "which recommendations failed",
            "failed interventions",
            "underperforming recommendations",
        ),
    ),
    IntentDefinition(
        intent="student_progress_summary",
        persona="mentor",
        phrases=(
            "show student progress summary",
            "student progress summary",
            "progress summary for this student",
        ),
    ),
    IntentDefinition(
        intent="improvement_drivers",
        persona="mentor",
        phrases=(
            "improvement drivers",
            "what drove readiness improvement",
            "largest readiness improvements",
        ),
    ),
    IntentDefinition(
        intent="stagnant_concepts",
        persona="mentor",
        phrases=(
            "which concepts remain weak",
            "stagnant concepts",
            "concepts still weak",
        ),
    ),
    IntentDefinition(
        intent="intervention_history",
        persona="mentor",
        phrases=(
            "show intervention history",
            "intervention history",
            "coaching history for this student",
        ),
    ),
    IntentDefinition(
        intent="coaching_timeline",
        persona="mentor",
        phrases=(
            "coaching timeline",
            "show coaching timeline",
            "intervention timeline",
        ),
    ),
    IntentDefinition(
        intent="successful_interventions",
        persona="mentor",
        phrases=(
            "what coaching worked best",
            "successful interventions",
            "best coaching interventions",
        ),
    ),
    IntentDefinition(
        intent="student_week_plan",
        persona="mentor",
        phrases=(
            "student week plan",
            "show student weekly plan",
            "this student week plan",
        ),
    ),
    IntentDefinition(
        intent="plan_adjustments",
        persona="mentor",
        phrases=(
            "plan adjustments",
            "suggest plan adjustments",
            "what should change in the plan",
        ),
    ),
    IntentDefinition(
        intent="plan_risk_areas",
        persona="mentor",
        phrases=(
            "plan risk areas",
            "which plan items are risky",
            "plan risks for this student",
        ),
    ),
    IntentDefinition(
        intent="recommended_interventions",
        persona="mentor",
        phrases=(
            "show recommended interventions",
            "recommended interventions",
            "recommended interventions from plan",
            "plan recommended interventions",
            "what interventions does the plan suggest",
        ),
    ),
    IntentDefinition(
        intent="student_forecast",
        persona="mentor",
        phrases=(
            "student forecast",
            "show student goal forecast",
            "student readiness forecast",
        ),
    ),
    IntentDefinition(
        intent="intervention_impact",
        persona="mentor",
        phrases=(
            "intervention impact on forecast",
            "how do interventions affect forecast",
            "forecast intervention impact",
        ),
    ),
    IntentDefinition(
        intent="forecast_risk",
        persona="mentor",
        phrases=(
            "forecast risk",
            "forecast risk areas",
            "goal forecast risks",
        ),
    ),
    IntentDefinition(
        intent="goal_attainment_probability",
        persona="mentor",
        phrases=(
            "goal attainment probability",
            "probability student reaches goal",
            "student goal probability",
        ),
    ),
    IntentDefinition(
        intent="student_recovery_plan",
        persona="mentor",
        phrases=(
            "student recovery plan",
            "recovery plan for student",
            "build recovery plan",
        ),
    ),
    IntentDefinition(
        intent="forecast_recovery",
        persona="mentor",
        phrases=(
            "forecast recovery",
            "forecast recovery plan",
            "help student recover forecast",
        ),
    ),
    IntentDefinition(
        intent="coaching_priorities",
        persona="mentor",
        phrases=(
            "coaching priorities",
            "what should i coach first",
            "priority coaching actions",
        ),
    ),
    IntentDefinition(
        intent="at_risk_students",
        persona="mentor",
        phrases=(
            "at risk students",
            "students at risk",
            "who is at risk",
        ),
    ),
    IntentDefinition(
        intent="critical_students",
        persona="mentor",
        phrases=(
            "critical students",
            "critical risk students",
            "students in critical risk",
        ),
    ),
    IntentDefinition(
        intent="top_improvers",
        persona="mentor",
        phrases=(
            "top improvers",
            "fastest improving students",
            "best improving students",
        ),
    ),
    IntentDefinition(
        intent="stagnant_students",
        persona="mentor",
        phrases=(
            "stagnant students",
            "students not improving",
            "who is stagnant",
        ),
    ),
    IntentDefinition(
        intent="cohort_summary",
        persona="mentor",
        phrases=(
            "cohort summary",
            "summarize the cohort",
            "cohort overview",
        ),
    ),
    IntentDefinition(
        intent="cohort_trends",
        persona="mentor",
        phrases=(
            "cohort trends",
            "show cohort trends",
            "how is the cohort trending",
        ),
    ),
    IntentDefinition(
        intent="mentor_effectiveness",
        persona="mentor",
        phrases=(
            "mentor effectiveness",
            "how effective are mentors",
            "intervention success rate",
        ),
    ),
    IntentDefinition(
        intent="escalation_reason",
        persona="mentor",
        phrases=(
            "escalation reason",
            "why escalated",
            "explain escalation",
            "why was this escalated",
        ),
    ),
    IntentDefinition(
        intent="top_risks",
        persona="mentor",
        phrases=(
            "top risks",
            "show risks",
            "student risks",
            "risk factors",
        ),
    ),
    IntentDefinition(
        intent="forecast_summary",
        persona="mentor",
        phrases=(
            "forecast summary",
            "show forecast",
            "goal forecast",
            "readiness forecast",
        ),
    ),
    IntentDefinition(
        intent="draft_coaching_note",
        persona="mentor",
        phrases=(
            "draft coaching note",
            "coaching note",
            "draft note",
            "write coaching note",
        ),
    ),
    IntentDefinition(
        intent="platform_health",
        persona="admin",
        phrases=(
            "platform health",
            "overall health",
            "system health",
            "ops health",
        ),
    ),
    IntentDefinition(
        intent="worker_status",
        persona="admin",
        phrases=(
            "worker status",
            "celery worker",
            "celery status",
            "background worker",
        ),
    ),
    IntentDefinition(
        intent="outbox_status",
        persona="admin",
        phrases=(
            "outbox status",
            "outbox queue",
            "event outbox",
        ),
    ),
    IntentDefinition(
        intent="deployment_readiness",
        persona="admin",
        phrases=(
            "deployment readiness",
            "deployment ready",
            "pilot ready",
            "ready for deployment",
        ),
    ),
    IntentDefinition(
        intent="forecast_summary",
        persona="admin",
        phrases=(
            "forecast summary",
            "forecasting summary",
            "goal forecasting summary",
        ),
    ),
    IntentDefinition(
        intent="forecast_accuracy",
        persona="admin",
        phrases=(
            "forecast accuracy",
            "how accurate are forecasts",
            "forecast quality",
        ),
    ),
    IntentDefinition(
        intent="cohort_projection",
        persona="admin",
        phrases=(
            "cohort projection",
            "cohort forecast",
            "tenant forecast projection",
        ),
    ),
    IntentDefinition(
        intent="intervention_summary",
        persona="admin",
        phrases=(
            "intervention summary",
            "mentor intervention summary",
            "intervention overview",
        ),
    ),
    IntentDefinition(
        intent="intervention_effectiveness",
        persona="admin",
        phrases=(
            "intervention effectiveness",
            "how effective are interventions",
            "intervention roi",
        ),
    ),
    IntentDefinition(
        intent="mentor_performance",
        persona="admin",
        phrases=(
            "mentor performance",
            "mentor intervention performance",
            "mentor effectiveness",
        ),
    ),
    IntentDefinition(
        intent="institution_health",
        persona="admin",
        phrases=(
            "institution health",
            "institutional health",
            "institute health",
        ),
    ),
    IntentDefinition(
        intent="cohort_health",
        persona="admin",
        phrases=(
            "cohort health",
            "overall cohort health",
            "cohort health score",
        ),
    ),
    IntentDefinition(
        intent="segment_distribution",
        persona="admin",
        phrases=(
            "segment distribution",
            "student segment distribution",
            "cohort segment breakdown",
        ),
    ),
    IntentDefinition(
        intent="top_risk_areas",
        persona="admin",
        phrases=(
            "top risk areas",
            "biggest cohort risks",
            "weak concept areas",
        ),
    ),
    IntentDefinition(
        intent="mentor_comparison",
        persona="admin",
        phrases=(
            "mentor comparison",
            "compare mentors",
            "mentor leaderboard",
        ),
    ),
    IntentDefinition(
        intent="institution_summary",
        persona="admin",
        phrases=(
            "institution summary",
            "show institution summary",
            "executive summary",
            "institute overview",
        ),
    ),
    IntentDefinition(
        intent="institution_risks",
        persona="admin",
        phrases=(
            "institution risks",
            "biggest risks",
            "what are our biggest risks",
            "institutional risks",
        ),
    ),
    IntentDefinition(
        intent="institution_recommendations",
        persona="admin",
        phrases=(
            "institution recommendations",
            "executive recommendations",
            "what should we do",
            "recommended actions",
        ),
    ),
    IntentDefinition(
        intent="institution_mentor_effectiveness",
        persona="admin",
        phrases=(
            "which mentors are most effective",
            "institution mentor effectiveness",
            "top mentors",
        ),
    ),
    IntentDefinition(
        intent="weakest_concepts",
        persona="admin",
        phrases=(
            "weakest concepts",
            "weak concepts across cohorts",
            "which concepts are weak",
            "concept weaknesses",
        ),
    ),
    IntentDefinition(
        intent="cohort_comparison",
        persona="admin",
        phrases=(
            "cohort comparison",
            "compare cohorts",
            "cohort benchmark",
        ),
    ),
    IntentDefinition(
        intent="forecast_trends",
        persona="admin",
        phrases=(
            "forecast trends",
            "institution forecast trends",
            "forecast movement",
        ),
    ),
    IntentDefinition(
        intent="institution_intervention_roi",
        persona="admin",
        phrases=(
            "institution intervention roi",
            "best intervention results",
            "what interventions are producing the best results",
            "intervention return on investment",
        ),
    ),
    IntentDefinition(
        intent="institution_outcomes",
        persona="admin",
        phrases=(
            "institution outcomes",
            "show institution outcomes",
            "outcome results",
        ),
    ),
    IntentDefinition(
        intent="initiative_performance",
        persona="admin",
        phrases=(
            "initiative performance",
            "show initiative performance",
            "how are initiatives performing",
        ),
    ),
    IntentDefinition(
        intent="best_initiatives",
        persona="admin",
        phrases=(
            "best initiatives",
            "which initiatives worked best",
            "top initiatives",
            "highest roi initiatives",
        ),
    ),
    IntentDefinition(
        intent="failed_initiatives",
        persona="admin",
        phrases=(
            "failed initiatives",
            "which campaigns failed",
            "underperforming initiatives",
        ),
    ),
    IntentDefinition(
        intent="roi_summary",
        persona="admin",
        phrases=(
            "roi summary",
            "what produced the highest roi",
            "institution roi summary",
        ),
    ),
    IntentDefinition(
        intent="forecast_improvements",
        persona="admin",
        phrases=(
            "forecast improvements",
            "forecast uplift",
            "forecast recovery results",
        ),
    ),
    )
)


def _normalize_question(question: str) -> str:
    normalized = question.strip().lower()
    normalized = re.sub(r"[^\w\s']", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _score_phrase(normalized_question: str, phrase: str) -> int:
    if phrase in normalized_question:
        return len(phrase.split()) + 2
    tokens = phrase.split()
    if not tokens:
        return 0
    matched = sum(1 for token in tokens if token in normalized_question.split())
    if matched == len(tokens):
        return matched
    return 0


def route_intent(*, persona: CopilotPersona, question: str) -> str:
    normalized = _normalize_question(question)
    best: IntentMatch | None = None

    for definition in _INTENT_DEFINITIONS:
        if definition.persona != persona:
            continue
        score = max(_score_phrase(normalized, phrase) for phrase in definition.phrases)
        if score <= 0:
            continue
        candidate = IntentMatch(intent=definition.intent, score=score)
        if best is None or candidate.score > best.score:
            best = candidate

    if best is None:
        return _UNKNOWN_INTENT
    return best.intent


def suggested_prompts_for_persona(persona: CopilotPersona) -> tuple[str, ...]:
    prompts: list[str] = []
    for definition in _INTENT_DEFINITIONS:
        if definition.persona != persona:
            continue
        prompts.append(definition.phrases[0])
    return tuple(prompts)
