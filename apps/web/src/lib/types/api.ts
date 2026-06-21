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

export interface RegisterRequest {
  tenant_slug: string;
  tenant_name: string;
  email: string;
  password: string;
  full_name: string;
}

export interface UpdateStudentGoalsRequest {
  target_exam?: string;
  target_year?: number;
  daily_study_hours?: number;
  experience_level?: string;
}

export interface CompleteOnboardingResponse {
  student: StudentProfileResponse;
  provisioning: {
    learning_graph_provision_id: string;
    preparation_twin_id: string;
    expected_node_count: number;
    catalog_version: string;
    target_stages: string[];
  };
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token?: string;
}

export interface ExamResponse {
  exam_id: string;
  exam_code: string;
  exam_name: string;
  exam_type: string;
  status: string;
}

export interface ConceptResponse {
  concept_id: string;
  topic_id: string;
  subject_id: string;
  concept_name: string;
  concept_slug: string;
  concept_type: string;
  status: string;
}

export interface TopicResponse {
  topic_id: string;
  subject_id: string;
  topic_name: string;
  topic_slug: string;
  status: string;
}

export interface SubjectResponse {
  subject_id: string;
  subject_name: string;
  subject_slug: string;
  status: string;
}

export interface TopicTreeResponse {
  topic: TopicResponse;
  concepts: ConceptResponse[];
}

export interface SubjectTreeResponse {
  subject: SubjectResponse;
  topics: TopicTreeResponse[];
}

export interface ExamTreeResponse {
  exam: ExamResponse;
  subjects: SubjectTreeResponse[];
  catalog_version: string;
}

export interface ConceptAncestorsResponse {
  concept: ConceptResponse;
  ancestors: ConceptResponse[];
  topic: TopicResponse;
  subject: SubjectResponse;
}

export const CASE_RESOLUTION_REASONS = [
  "STUDENT_CONTACTED",
  "PLAN_UPDATED",
  "RISK_REDUCED",
  "GOAL_ADJUSTED",
  "FALSE_POSITIVE",
] as const;

export type CaseResolutionReason = (typeof CASE_RESOLUTION_REASONS)[number];

export interface ConceptDisplayInfo {
  conceptId: string;
  name: string;
  path: string;
  subjectName: string;
  topicName: string;
}

export interface LearningGraphActivityResponse {
  accepted: boolean;
  event_type: string;
}

export interface RecordStudySessionRequest {
  concept_id: string;
  exam_id: string;
  engaged_minutes: number;
}

export interface RecordRevisionRequest {
  concept_id: string;
  exam_id: string;
  recall_grade: string;
}

export interface RecordAssessmentRequest {
  concept_id: string;
  exam_id: string;
  mcq_correct: boolean;
  self_confidence?: number;
}

export interface RecordPyqChangeRequest {
  concept_id: string;
  exam_id: string;
  global_importance: number;
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

export type RecommendationConfidence = "high" | "medium" | "low";

export interface ConceptRecommendation {
  concept_id: string;
  concept_name: string;
  impact_score: number;
  reason_codes: string[];
  reasons: string[];
  estimated_readiness_gain: number;
  confidence: RecommendationConfidence;
}

export interface RecommendationsResponse {
  recommendations: ConceptRecommendation[];
  generated_at: string;
}

export interface RecommendationExplainResponse {
  concept_id: string;
  concept_name: string;
  impact_score: number;
  weakness_score: number;
  pyq_frequency_score: number;
  forecast_gain_score: number;
  current_affairs_score: number;
  reason_codes: string[];
  reasons: string[];
  estimated_readiness_gain: number;
  confidence: RecommendationConfidence;
  historical_effectiveness: number | null;
  average_actual_gain: number | null;
}

export interface CompleteRecommendationResponse {
  concept_id: string;
  status: string;
  readiness_gain: number | null;
}

export interface RecommendationEffectivenessResponse {
  recommendation_acceptance_rate: number;
  completion_rate: number;
  average_readiness_gain: number;
  recommendation_effectiveness: number;
}

export interface RecommendationOutcomeListResponse {
  outcomes: Array<Record<string, unknown>>;
  total: number;
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

export interface CopilotPersonaUsage {
  persona: string;
  query_count: number;
  unique_users: number;
  share_of_queries: string;
}

export interface CopilotIntentDistributionItem {
  intent: string;
  count: number;
  share: string;
}

export interface CopilotDailyUsageItem {
  date: string;
  query_count: number;
  unique_users: number;
}

export interface CopilotPromptCountItem {
  query_text: string;
  count: number;
}

export interface CopilotAdoptionFunnelItem {
  stage: string;
  count: number;
  share: string;
}

export interface CopilotSuccessCriteria {
  active_user_adoption_target: string;
  active_user_adoption_actual: string;
  active_user_adoption_met: boolean;
  unknown_intent_rate_target: string;
  unknown_intent_rate_actual: string;
  unknown_intent_rate_met: boolean;
  queries_per_active_user_target: string;
  queries_per_active_user_actual: string;
  queries_per_active_user_met: boolean;
  content_explanation_in_top_five_met: boolean;
  content_explanation_note: string;
}

export interface CopilotConfidenceDistributionItem {
  confidence: string;
  count: number;
  share: string;
}

export interface CopilotContentAnalytics {
  content_questions_today: number;
  content_questions_period: number;
  citation_usage_count: number;
  citation_usage_rate: string;
  confidence_distribution: CopilotConfidenceDistributionItem[];
  content_daily_usage: CopilotDailyUsageItem[];
}

export interface CopilotMentorKnowledgeAnalytics {
  mentor_content_questions_today: number;
  mentor_content_questions_period: number;
  citation_usage_count: number;
  citation_usage_rate: string;
  confidence_distribution: CopilotConfidenceDistributionItem[];
  mentor_content_daily_usage: CopilotDailyUsageItem[];
}

export interface CopilotAnalyticsResponse {
  period_days: number;
  generated_at: string;
  dau: number;
  wau: number;
  total_queries: number;
  unique_copilot_users: number;
  total_tenant_users: number;
  queries_per_user_avg: string;
  unknown_intent_rate: string;
  student_usage: CopilotPersonaUsage;
  mentor_usage: CopilotPersonaUsage;
  admin_usage: CopilotPersonaUsage;
  intent_distribution: CopilotIntentDistributionItem[];
  daily_usage_trend: CopilotDailyUsageItem[];
  top_prompts: CopilotPromptCountItem[];
  unknown_intents: CopilotPromptCountItem[];
  adoption_funnel: CopilotAdoptionFunnelItem[];
  success_criteria: CopilotSuccessCriteria;
  content_analytics: CopilotContentAnalytics;
  mentor_content_analytics: CopilotMentorKnowledgeAnalytics;
}

export interface ApiErrorBody {
  message?: string;
  detail?: string | { msg: string }[];
  details?: Record<string, unknown>;
}

export interface KnowledgeSourceResponse {
  id: string;
  tenant_id: string | null;
  exam_id: string;
  source_type: string;
  title: string;
  external_uri: string | null;
  content_hash: string;
  catalog_version: string | null;
  status: string;
  file_name: string | null;
  mime_type: string | null;
  chunk_count: number;
  indexed_chunk_count: number;
  embedding_failure_count: number;
  ingestion_failure_count: number;
  last_error: string | null;
  ingestion_started_at: string | null;
  ingestion_completed_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSourceListResponse {
  sources: KnowledgeSourceResponse[];
  total: number;
}

export interface KnowledgeIndexingMetricsResponse {
  total_sources: number;
  active_sources: number;
  processing_sources: number;
  failed_sources: number;
  total_chunks: number;
  indexed_chunks: number;
  embedding_failures: number;
  ingestion_failures: number;
}

export interface CurrentAffairsArticleResponse {
  id: string;
  tenant_id: string | null;
  exam_id: string;
  source_type: string;
  title: string;
  status: string;
  published_at: string | null;
  source_authority: string | null;
  exam_stage: string | null;
  importance: string | null;
  chunk_count: number;
  indexed_chunk_count: number;
  concept_ids: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CurrentAffairsArticleListResponse {
  articles: CurrentAffairsArticleResponse[];
  total: number;
}

export interface CurrentAffairsIndexingMetricsResponse {
  total_articles: number;
  active_articles: number;
  processing_articles: number;
  failed_articles: number;
  total_chunks: number;
  indexed_chunks: number;
}

export interface CurrentAffairsAnalyticsResponse {
  current_affairs_qna_count: number;
  article_citation_usage_count: number;
  article_citation_usage_rate: number;
  recency_retrieval_success_rate: number;
  recency_boost_usage_rate: number;
}

export interface PyqQuestionResponse {
  id: string;
  tenant_id: string | null;
  exam_id: string;
  year: number;
  exam_stage: string;
  paper: string;
  question_text: string;
  answer_text: string | null;
  source_reference: string | null;
  difficulty: number | null;
  importance: string | null;
  concept_ids: string[];
  knowledge_source_id: string | null;
  knowledge_chunk_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface PyqUploadResponse {
  knowledge_source_id: string;
  questions_ingested: number;
  questions: PyqQuestionResponse[];
}

export interface PyqTrendItem {
  concept_id: string;
  pyq_count: number;
  first_appearance_year: number | null;
  last_appearance_year: number | null;
  frequency_score: number;
  trend_score: number;
}

export interface PyqTrendsResponse {
  exam_id: string;
  trends: PyqTrendItem[];
  total_questions: number;
}

export interface PyqCoverageResponse {
  exam_id: string;
  total_questions: number;
  mapped_questions: number;
  unmapped_questions: number;
  top_concepts: PyqTrendItem[];
}

export interface PyqMappingReviewItem {
  question: PyqQuestionResponse;
  mappings: Array<{ concept_id: string; confidence_score: number }>;
}

export interface PyqIndexingMetricsResponse {
  total_questions: number;
  indexed_questions: number;
  total_knowledge_chunks: number;
  indexed_knowledge_chunks: number;
}

export interface PyqAnalyticsResponse {
  pyq_queries: number;
  pyq_citation_rate: number;
  pyq_topic_frequency_avg: number;
  pyq_revision_recommendations: number;
}

export interface RetrievalQualityMetrics {
  recall_at_5: number;
  recall_at_8: number;
  precision_at_5: number;
  precision_at_8: number;
  mrr: number;
  ndcg: number;
  evaluation_count: number;
}

export interface FaithfulnessMetrics {
  avg_support_score: number;
  avg_citation_coverage: number;
  evaluation_count: number;
}

export interface HallucinationMetrics {
  avg_hallucination_score: number;
  high_hallucination_rate: number;
  evaluation_count: number;
}

export interface CitationCoverageMetrics {
  avg_citation_coverage: number;
  avg_citation_count: number;
  evaluation_count: number;
}

export interface SourceQualityItem {
  source_type: string;
  query_count: number;
  citation_count: number;
  avg_confidence_score: number;
  avg_support_score: number;
  avg_hallucination_score: number;
}

export interface SourceQualityMetrics {
  sources: SourceQualityItem[];
}

export interface RagQualityTrendPoint {
  date: string;
  avg_support_score: number;
  avg_hallucination_score: number;
  avg_citation_coverage: number;
}

export interface RagQualityResponse {
  retrieval: RetrievalQualityMetrics;
  faithfulness: FaithfulnessMetrics;
  hallucination: HallucinationMetrics;
  citation_coverage: CitationCoverageMetrics;
  source_quality: SourceQualityMetrics;
  trends: RagQualityTrendPoint[];
}

export interface RecommendationEffectivenessItem {
  concept_id: string;
  concept_name: string;
  predicted_gain: number;
  actual_gain: number;
  effectiveness_score: number;
  status: string;
  outcome_count: number;
}

export interface RecommendationEffectivenessAdminResponse {
  average_effectiveness: number;
  average_actual_gain: number;
  completion_rate: number;
  success_rate: number;
  top_performing_concepts: RecommendationEffectivenessItem[];
  lowest_performing_concepts: RecommendationEffectivenessItem[];
  readiness_uplift_trend: Array<{ date: string; average_uplift: number }>;
  forecast_uplift_trend: Array<{ date: string; average_uplift: number }>;
  concept_rankings: RecommendationEffectivenessItem[];
}

export interface MemoryAdminResponse {
  total_memories: number;
  memory_growth_last_30_days: number;
  top_memory_types: Array<{ memory_type: string; count: number }>;
  milestone_count: number;
  last_rebuild_at: string | null;
}

export interface AdaptivePlanItem {
  id: string;
  concept_id: string;
  concept_name: string;
  activity_type: string;
  priority_score: number;
  estimated_minutes: number;
  estimated_readiness_gain: number;
  confidence: string;
  scheduled_date: string;
  source_reason: string;
  completion_status: string;
}

export interface AdaptivePlanResponse {
  plan_id: string;
  exam_id: string;
  generated_at: string;
  valid_from: string;
  valid_to: string;
  readiness_snapshot: number | null;
  forecast_snapshot: number | null;
  status: string;
  today_items: AdaptivePlanItem[];
  week_items: AdaptivePlanItem[];
  next_week_draft: AdaptivePlanItem[];
  total_estimated_gain: number;
  daily_minutes_budget: number;
}

export interface PlanHistoryEntry {
  plan_id: string;
  generated_at: string;
  valid_from: string;
  valid_to: string;
  status: string;
  item_count: number;
  completed_count: number;
}

export interface PlanHistoryResponse {
  plans: PlanHistoryEntry[];
  total: number;
}

export interface PlanExplainResponse {
  concept_id: string;
  concept_name: string;
  priority_score: number;
  estimated_readiness_gain: number;
  estimated_minutes: number;
  confidence: string;
  source_reason: string;
  score_breakdown: Record<string, number>;
  explanations: string[];
}

export interface PlanningAdminResponse {
  total_plans: number;
  active_plans: number;
  plans_generated_last_30_days: number;
  average_completion_rate: number;
  average_adherence: number;
  top_scheduled_concepts: Array<{ concept_id: string; count: number }>;
  event_counts: Array<{ event_type: string; count: number }>;
}

export interface ForecastAdminResponse {
  total_forecasts: number;
  forecasts_last_30_days: number;
  average_probability: number;
  on_track_rate: number;
  average_projected_gain: number;
  scenario_usage: Array<{ scenario_type: string; count: number }>;
  event_counts: Array<{ event_type: string; count: number }>;
}

export interface ForecastScenarioItem {
  id: string;
  scenario_type: string;
  scenario_name: string;
  weekly_minutes: number;
  projected_readiness: number;
  projected_score: number | null;
  probability_of_success: number;
}

export interface GoalForecastResponse {
  forecast_id: string;
  exam_id: string;
  forecast_date: string;
  target_date: string;
  current_readiness: number;
  projected_readiness: number;
  target_readiness: number;
  probability_of_success: number;
  forecast_status: string;
  top_drivers: string[];
  scenarios: ForecastScenarioItem[];
  explanations: string[];
  generated_at: string;
}

export interface ForecastExplainResponse {
  current_readiness: number;
  projected_readiness: number;
  target_readiness: number;
  probability_of_success: number;
  forecast_status: string;
  top_drivers: string[];
  explanations: string[];
  weekly_gain: number;
  adherence_rate: number;
  effectiveness_multiplier: number;
}

export interface ForecastHistoryEntry {
  forecast_id: string;
  forecast_date: string;
  projected_readiness: number;
  probability_of_success: number;
  forecast_status: string;
  created_at: string;
}

export interface ForecastHistoryResponse {
  forecasts: ForecastHistoryEntry[];
  total: number;
}

export interface RecommendedInterventionItem {
  id?: string;
  intervention_type: string;
  concept_id?: string | null;
  concept?: string | null;
  predicted_gain: number;
  priority_score: number;
  impact_score: number;
  confidence: string;
  reason: string;
  forecast_improvement?: number;
}

export interface InterventionRecordItem {
  id: string;
  mentor_id: string;
  student_id: string;
  exam_id: string;
  intervention_type: string;
  concept_id?: string | null;
  concept?: string | null;
  reason: string;
  predicted_gain: number;
  priority_score: number;
  status: string;
  created_at: string;
}

export interface StudentInterventionResponse {
  student_id: string;
  exam_id: string;
  current_readiness?: number | null;
  forecast_status?: string | null;
  recommended_interventions: RecommendedInterventionItem[];
  active_interventions: InterventionRecordItem[];
  generated_at: string;
}

export interface InterventionExplainResponse {
  intervention_id: string;
  intervention_type: string;
  concept_id?: string | null;
  concept?: string | null;
  reason: string;
  predicted_gain: number;
  priority_score: number;
  explanations: string[];
}

export interface InterventionHistoryEntry {
  intervention_id: string;
  intervention_type: string;
  concept_id?: string | null;
  concept?: string | null;
  status: string;
  predicted_gain: number;
  actual_gain?: number | null;
  effectiveness_score?: number | null;
  created_at: string;
  evaluated_at?: string | null;
}

export interface InterventionHistoryResponse {
  interventions: InterventionHistoryEntry[];
  total: number;
}

export interface MentorInterventionQueueItem {
  student_id: string;
  exam_id: string;
  top_intervention_type: string;
  top_concept?: string | null;
  priority_score: number;
  predicted_gain: number;
  forecast_status?: string | null;
  reason: string;
}

export interface MentorInterventionQueueResponse {
  items: MentorInterventionQueueItem[];
  total: number;
}

export interface InterventionAdminResponse {
  total_interventions: number;
  interventions_last_30_days: number;
  average_gain: number;
  average_effectiveness: number;
  mentor_success_rate: number;
  top_interventions: Array<{ intervention_type: string; count: number }>;
  least_effective_interventions: Array<{ intervention_type: string; average_effectiveness: number }>;
  status_counts: Array<{ status: string; count: number }>;
}

export interface CohortMetrics {
  average_readiness: number;
  average_forecast: number;
  average_gain: number;
  goal_attainment_rate: number;
  recommendation_effectiveness: number;
  planning_adherence: number;
  mentor_intervention_success: number;
  pyq_preparedness: number;
  current_affairs_preparedness: number;
  cohort_health_score: number;
}

export interface CohortSummaryResponse {
  cohort_id: string;
  exam_id: string;
  student_count: number;
  segments: Record<string, number>;
  metrics: CohortMetrics;
  top_risks: string[];
  generated_at: string;
}

export interface StudentSegmentItem {
  student_id: string;
  segment_type: string;
  segment_score: number;
  risk_score: number;
  readiness: number;
  forecast_probability: number;
  exam_id: string;
}

export interface CohortStudentsResponse {
  cohort_id: string;
  students: StudentSegmentItem[];
  total: number;
}

export interface CohortSegmentsResponse {
  cohort_id: string;
  distribution: Record<string, number>;
  students: StudentSegmentItem[];
  total: number;
}

export interface CohortRiskItem {
  student_id: string;
  risk_score: number;
  segment_type: string;
  readiness: number;
  forecast_probability: number;
  top_risk_factors: string[];
}

export interface CohortRisksResponse {
  cohort_id: string;
  risks: CohortRiskItem[];
  top_concept_risks: string[];
  total: number;
}

export interface CohortTrendItem {
  concept_id: string;
  concept_name: string;
  trend_direction: string;
  readiness_delta: number;
  period: string;
}

export interface CohortTrendsResponse {
  cohort_id: string;
  trends: CohortTrendItem[];
  readiness_trend: string;
  forecast_trend: string;
  cohort_growth: number;
}

export interface MentorComparisonItem {
  mentor_id: string;
  intervention_success_rate: number;
  student_count: number;
  average_gain: number;
}

export interface CohortAdminResponse {
  total_snapshots: number;
  snapshots_last_30_days: number;
  total_students_segmented: number;
  average_cohort_health: number;
  segment_distribution: Record<string, number>;
  top_risk_concepts: string[];
  mentor_comparisons: MentorComparisonItem[];
  event_counts: Array<{ event_type: string; count: number }>;
}

export interface InstitutionEvidence {
  label: string;
  value: string;
}

export interface InstitutionInsightItem {
  insight_type: string;
  insight_key: string;
  title: string;
  severity: string;
  evidence: InstitutionEvidence[];
  calculation: string;
  source_metrics: Record<string, number | string>;
}

export interface InstitutionInsightsResponse {
  insights: InstitutionInsightItem[];
  total: number;
  generated_at: string;
}

export interface InstitutionRecommendationItem {
  recommendation_type: string;
  title: string;
  expected_impact: number;
  affected_students: number;
  affected_cohorts: string[];
  explanation: string;
  priority_score: number;
}

export interface InstitutionRecommendationsResponse {
  recommendations: InstitutionRecommendationItem[];
  total: number;
  generated_at: string;
}

export interface InstitutionTrendItem {
  trend_type: string;
  trend_key: string;
  trend_direction: string;
  delta_value: number;
  period: string;
  label: string;
}

export interface InstitutionTrendsResponse {
  trends: InstitutionTrendItem[];
  readiness_trend: string;
  forecast_trend: string;
  intervention_roi: number;
  generated_at: string;
}

export interface InstitutionMentorEffectivenessItem {
  mentor_id: string;
  intervention_success_rate: number;
  student_count: number;
  average_gain: number;
  cohort_average_success_rate: number;
  outperformance_pct: number;
}

export interface InstitutionMentorEffectivenessResponse {
  mentors: InstitutionMentorEffectivenessItem[];
  cohort_average_success_rate: number;
  total: number;
  generated_at: string;
}

export interface InstitutionCohortComparisonItem {
  cohort_id: string;
  exam_id: string;
  student_count: number;
  average_readiness: number;
  average_forecast: number;
  cohort_health_score: number;
  at_risk_count: number;
}

export interface InstitutionKpis {
  total_students: number;
  total_cohorts: number;
  average_readiness: number;
  average_forecast: number;
  average_cohort_health: number;
  at_risk_students: number;
  intervention_roi: number;
  institution_health_score: number;
}

export interface InstitutionDashboardResponse {
  kpis: InstitutionKpis;
  cohort_comparisons: InstitutionCohortComparisonItem[];
  weak_concepts: string[];
  top_insights: InstitutionInsightItem[];
  top_recommendations: InstitutionRecommendationItem[];
  generated_at: string;
}

export interface CreateInitiativeRequest {
  initiative_type: string;
  title: string;
  start_date: string;
  end_date?: string | null;
  affected_students: number;
  affected_cohorts?: string[];
  expected_readiness_gain?: number;
  expected_forecast_gain?: number;
  expected_cohort_health_gain?: number;
  expected_risk_reduction?: number;
}

export interface InstitutionInitiativeItem {
  id: string;
  initiative_type: string;
  title: string;
  status: string;
  start_date: string;
  end_date?: string | null;
  affected_students: number;
  affected_cohorts: string[];
  expected_outcomes: Record<string, number>;
  actual_outcomes: Record<string, number>;
  created_at: string;
}

export interface InstitutionInitiativesResponse {
  initiatives: InstitutionInitiativeItem[];
  total: number;
}

export interface InstitutionOutcomeState {
  readiness: number;
  forecast: number;
  cohort_health: number;
  risk_count: number;
}

export interface InstitutionOutcomeItem {
  initiative_id?: string | null;
  outcome_type: string;
  subject_key: string;
  before: InstitutionOutcomeState;
  after: InstitutionOutcomeState;
  actual_gain: number;
  expected_gain: number;
  variance: number;
  readiness_gain: number;
  forecast_gain: number;
  cohort_health_gain: number;
  risk_reduction: number;
}

export interface InstitutionOutcomesResponse {
  outcomes: InstitutionOutcomeItem[];
  total: number;
  average_readiness_uplift: number;
  average_forecast_uplift: number;
  average_risk_reduction: number;
  generated_at: string;
}

export interface InstitutionRoiEvidence {
  label: string;
  value: string;
}

export interface InstitutionRoiItem {
  initiative_id?: string | null;
  subject_key: string;
  initiative_type?: string | null;
  title?: string | null;
  roi_score: number;
  readiness_gain: number;
  forecast_gain: number;
  cohort_health_gain: number;
  risk_reduction: number;
  evidence: InstitutionRoiEvidence[];
  calculation: string;
}

export interface InstitutionRoiResponse {
  items: InstitutionRoiItem[];
  total: number;
  average_roi_score: number;
  best_initiatives: InstitutionRoiItem[];
  failed_initiatives: InstitutionRoiItem[];
  generated_at: string;
}

export interface AgentExecutionSummary {
  execution_id: string;
  agent_type: string;
  persona: string;
  confidence: string;
  success: boolean;
  execution_time_ms: number;
  created_at: string;
}

export interface AgentAdminDashboardResponse {
  total_executions: number;
  executions_last_30_days: number;
  success_rate: number;
  average_confidence_score: number;
  agent_usage: Record<string, number>;
  tool_usage: Record<string, number>;
  workflow_counts: Record<string, number>;
  recent_executions: AgentExecutionSummary[];
  critique_count: number;
  reflection_count: number;
  average_critique_score: number;
  registered_agents: Array<Record<string, unknown>>;
  agent_health: AgentHealthStatus[];
}

export interface AgentHealthStatus {
  agent_type: string;
  success_rate: number;
  average_confidence_score: number;
  execution_count: number;
  status: string;
}

export interface AgentCapability {
  agent_type: string;
  display_name: string;
  description: string;
  capabilities: string[];
  supported_personas: string[];
  tool_names: string[];
}

export interface AgentTraceStep {
  step_number: number;
  agent_name: string;
  tool_name?: string | null;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  latency_ms: number;
  status: string;
}

export interface AgentTraceArtifact {
  artifact_type: string;
  artifact_json: Record<string, unknown>;
}

export interface AgentTraceRecord {
  trace_id: string;
  tenant_id: string;
  execution_id: string;
  user_id: string;
  persona: string;
  question: string;
  answer: string;
  confidence: string;
  latency_ms: number;
  created_at: string;
  steps: AgentTraceStep[];
  artifacts: AgentTraceArtifact[];
}

export interface AgentTraceListResponse {
  items: AgentTraceRecord[];
  total: number;
}

export interface AgentCostDashboardResponse {
  daily_cost: number;
  cost_per_query: number;
  total_queries: number;
  cost_by_agent: Record<string, number>;
  slowest_workflows: Array<Record<string, unknown>>;
  highest_cost_agents: Array<Record<string, unknown>>;
}

export interface AgentHealthDetail {
  agent_type: string;
  executions: number;
  failures: number;
  retries: number;
  average_latency_ms: number;
  average_confidence_score: number;
  satisfaction_score: number;
  estimated_cost: number;
  status: string;
}

export interface AgentHealthLeaderboardResponse {
  agents: AgentHealthDetail[];
  generated_at: string;
}

export interface PendingActionItem {
  action_id: string;
  action_type: string;
  proposed_by_agent: string;
  subject_key: string;
  explanation: string;
  payload: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface PendingActionListResponse {
  items: PendingActionItem[];
  total: number;
}
