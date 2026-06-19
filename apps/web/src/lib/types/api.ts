export type AppRole = "student" | "faculty" | "institute_admin" | "super_admin";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
}

export interface LoginRequest {
  tenant_slug: string;
  email: string;
  password: string;
}

export interface TwinGoalSummary {
  target_readiness_score: string | null;
  target_date: string | null;
}

export interface TwinMentorCaseSummary {
  case_status: string | null;
  priority: string | null;
  opened_at: string | null;
}

export interface TwinMentorEffectivenessSummary {
  best_action: string | null;
  effectiveness_score: string | null;
  sample_size: number | null;
}

export interface TwinDashboardResponse {
  readiness_score: string | null;
  due_revision_count: number;
  high_risk_concept_count: number;
  recommendation_count: number;
  largest_positive_driver: string | null;
  largest_negative_driver: string | null;
  top_positive_drivers: string[];
  top_negative_drivers: string[];
  total_estimated_gain: string | null;
  today_plan_count: number;
  weekly_plan_count: number;
  completion_rate: string | null;
  skip_rate: string | null;
  projected_readiness: string | null;
  gap_to_goal: string | null;
  on_track: boolean | null;
  expected_score: string | null;
  low_score: string | null;
  high_score: string | null;
  risk_level: string | null;
  milestone_status: string | null;
  expected_weekly_progress: string | null;
  next_milestone_date: string | null;
  next_milestone_target: string | null;
  goal_probability: string | null;
  goal_likelihood: string | null;
  best_case_readiness: string | null;
  worst_case_readiness: string | null;
  current_decision: string | null;
  expected_readiness_gain: string | null;
  expected_score_gain: string | null;
  current_intervention: string | null;
  intervention_urgency: string | null;
  intervention_score: string | null;
  best_intervention: string | null;
  historical_effectiveness: string | null;
  last_effectiveness_score: string | null;
  learning_style: string | null;
  risk_profile: string | null;
  consistency_score: string | null;
  best_activity_type: string | null;
  top_multiplier: string | null;
  mentor_status: string | null;
  top_mentor_message: string | null;
  mentor_action: string | null;
  mentor_action_priority: string | null;
  escalation_level: string | null;
  goal_summary: TwinGoalSummary | null;
  mentor_case: TwinMentorCaseSummary | null;
  mentor_effectiveness: TwinMentorEffectivenessSummary | null;
  generated_at: string | null;
}

export interface TwinResponse {
  profile_version: string;
  projection_version: number;
  readiness_score: string | null;
  average_mastery: string | null;
  average_retention: string | null;
  average_confidence: string | null;
  rated_node_count: number;
  due_revision_count: number;
  high_risk_concept_count: number;
  largest_positive_driver: string | null;
  largest_negative_driver: string | null;
  recommendation_count: number;
  last_recommendation_at: string | null;
  total_estimated_gain: string | null;
  predicted_outcome: Record<string, unknown> | null;
  simulations: Record<string, unknown> | null;
  decision: Record<string, unknown> | null;
  intervention: Record<string, unknown> | null;
  intervention_effectiveness: Record<string, unknown> | null;
  optimization: Record<string, unknown> | null;
  behavior_profile: Record<string, unknown> | null;
  personalization: Record<string, unknown> | null;
  mentor: Record<string, unknown> | null;
  mentor_action: Record<string, unknown> | null;
  escalation: Record<string, unknown> | null;
  twin_payload: Record<string, unknown>;
  generated_at: string | null;
}

export interface TwinRecommendationResponse {
  concept_id: string;
  recommendation_type: string;
  recommendation_score: string;
  importance_score: string;
  weakness_score: string;
  retention_score: string | null;
  readiness_gain: string;
  explanation: string;
}

export interface ConceptProgressNode {
  concept_id: string;
  exam_id: string;
  subject_id: string;
  topic_id: string;
  mastery_score: string;
  mastery_nonmcq_score: string;
  retention_score: string | null;
  confidence_score: string | null;
  importance_score: string;
  overconfidence_flag: boolean;
  mcq_attempt_count: number;
  mcq_correct_count: number;
  nonmcq_attempt_count: number;
  revision_count: number;
  study_minutes: number;
  node_state: string;
  row_version: number;
  last_activity_at: string | null;
  next_review_at: string | null;
}

export interface LearningGraphOverviewResponse {
  student_id: string;
  exam_id: string;
  total_nodes: number;
  provisioned_nodes: number;
  expected_nodes: number;
  provision_status: string;
  nodes: ConceptProgressNode[];
}

export interface LearningGraphReadinessResponse {
  version: string;
  overall_score: string | null;
  knowledge_subscore: string | null;
  retention_subscore: string | null;
  confidence_subscore: string | null;
  coverage_subscore: string | null;
  rated_node_count: number;
  total_node_count: number;
  unrated: boolean;
}

export interface LearningGraphWeaknessesResponse {
  student_id: string;
  weaknesses: Array<{
    concept_id: string;
    mastery_score: string;
    retention_score: string | null;
    importance_score: string;
    weakness_score: string;
  }>;
}

export interface RevisionQueueItem {
  concept_id: string;
  status: string;
  priority_score: string;
  next_review_at: string;
  retention_score: string | null;
  weakness_score: string | null;
  importance_score: string;
}

export interface DailyPlanItem {
  concept_id: string;
  activity_type: string;
  estimated_minutes: number;
  priority_score: string;
  adaptive_priority: string;
  readiness_gain: string;
  adjustment_explanation: string;
}

export interface WeeklyPlanItem {
  concept_id: string;
  target_sessions: number;
  estimated_minutes: number;
  readiness_gain: string;
}

export interface StudyPlanResponse {
  generated_at: string | null;
  total_estimated_gain: string;
  daily_plan: DailyPlanItem[];
  weekly_plan: WeeklyPlanItem[];
}

export interface StudyPlanExecutionRequest {
  exam_id: string;
  concept_id: string;
  activity_type: string;
  planned_minutes: number;
  actual_minutes?: number;
}

export interface GoalUpsertRequest {
  exam_id: string;
  target_readiness_score: number;
  target_date: string;
  daily_capacity_minutes?: number;
}

export interface GoalResponse {
  exam_id: string;
  target_readiness_score: string;
  target_date: string;
  daily_capacity_minutes: number;
  created_at: string | null;
  updated_at: string | null;
  goal_probability: string | null;
  goal_likelihood: string | null;
  trajectory: {
    required_gain: string;
    expected_daily_progress: string;
    expected_weekly_progress: string;
  } | null;
  milestones: Array<{
    target_date: string;
    target_readiness: string;
    expected_score: string;
  }>;
}

export interface StudentProfileResponse {
  id: string;
  tenant_id: string;
  user_id: string;
  target_exam: string | null;
  target_year: number | null;
  daily_study_hours: string | null;
  experience_level: string | null;
  onboarding_completed: boolean;
  onboarding_completed_at: string | null;
}

export interface MentorDashboardResponse {
  open_cases: number;
  critical_cases: number;
  average_resolution_time_hours: string;
  mentor_effectiveness_score: string;
  best_action: string | null;
  best_action_effectiveness: string;
  average_action_effectiveness: string;
}

export interface MentorQueueItem {
  student_id: string;
  mentor_action: string;
  priority_score: string;
  escalation_level: string;
  case_id: string;
  case_status: string;
  opened_at: string;
}

export interface MentorCaseNote {
  note_id: string;
  mentor_id: string;
  note: string;
  created_at: string;
}

export interface MentorCaseResponse {
  case_id: string;
  student_id: string;
  exam_id: string;
  status: string;
  priority: string;
  mentor_action_type: string;
  escalation_level: string;
  mentor_action_priority: string;
  opened_at: string;
  resolved_at: string | null;
  resolution_reason: string | null;
  notes: MentorCaseNote[];
}

export interface ApiErrorBody {
  message?: string;
  detail?: string | { msg: string }[];
  details?: Record<string, unknown>;
}
