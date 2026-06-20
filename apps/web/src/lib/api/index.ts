import { apiRequest, apiRequestForm, apiRequestText } from "@/lib/api/client";
import type {
  CompleteOnboardingResponse,
  ConceptAncestorsResponse,
  ConceptResponse,
  ExamResponse,
  ExamTreeResponse,
  GoalResponse,
  GoalUpsertRequest,
  LearningGraphActivityResponse,
  LearningGraphOverviewResponse,
  LearningGraphReadinessResponse,
  LearningGraphWeaknessesResponse,
  LoginRequest,
  LogoutRequest,
  MentorCaseResponse,
  MentorDashboardResponse,
  MentorQueueItem,
  RecordAssessmentRequest,
  RecordPyqChangeRequest,
  RecordRevisionRequest,
  RecordStudySessionRequest,
  RefreshRequest,
  RegisterRequest,
  RevisionQueueItem,
  StudentProfileResponse,
  StudyPlanExecutionRequest,
  StudyPlanResponse,
  TokenResponse,
  TwinDashboardResponse,
  TwinRecommendationResponse,
  TwinResponse,
  UpdateStudentGoalsRequest,
  UserResponse,
  KnowledgeIndexingMetricsResponse,
  KnowledgeSourceListResponse,
  KnowledgeSourceResponse,
} from "@/lib/types/api";

function withToken(token: string | null) {
  return { token };
}

export const authApi = {
  register: (body: RegisterRequest) =>
    apiRequest<TokenResponse>("/auth/register", { method: "POST", body }),
  login: (body: LoginRequest) =>
    apiRequest<TokenResponse>("/auth/login", { method: "POST", body }),
  refresh: (refreshToken: string) =>
    apiRequest<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken } satisfies RefreshRequest,
      skipAuthRetry: true,
    }),
  me: (token: string) => apiRequest<UserResponse>("/auth/me", withToken(token)),
  logout: (token: string, refreshToken?: string | null) =>
    apiRequest<void>("/auth/logout", {
      method: "POST",
      ...withToken(token),
      body: refreshToken ? ({ refresh_token: refreshToken } satisfies LogoutRequest) : undefined,
    }),
};

export const catalogApi = {
  listExams: (token?: string | null) =>
    apiRequest<ExamResponse[]>("/exams", token ? withToken(token) : {}),
  getExamTree: (examId: string, token?: string | null) =>
    apiRequest<ExamTreeResponse>(`/syllabus/${examId}/tree`, token ? withToken(token) : {}),
  getConcept: (conceptId: string, token?: string | null) =>
    apiRequest<ConceptResponse>(`/concepts/${conceptId}`, token ? withToken(token) : {}),
  getConceptAncestors: (conceptId: string, token?: string | null) =>
    apiRequest<ConceptAncestorsResponse>(
      `/concepts/${conceptId}/ancestors`,
      token ? withToken(token) : {},
    ),
};

export const studentApi = {
  profile: (token: string) =>
    apiRequest<StudentProfileResponse>("/students/me", withToken(token)),
  getProfile: (token: string, studentId: string) =>
    apiRequest<StudentProfileResponse>(`/students/${studentId}`, withToken(token)),
  updateProfile: (token: string, studentId: string, body: UpdateStudentGoalsRequest) =>
    apiRequest<StudentProfileResponse>(`/students/${studentId}`, {
      method: "PATCH",
      body,
      ...withToken(token),
    }),
  completeOnboarding: (token: string, diagnosticOffered = false) =>
    apiRequest<CompleteOnboardingResponse>("/students/onboarding/complete", {
      method: "POST",
      body: { diagnostic_offered: diagnosticOffered },
      ...withToken(token),
    }),
  twinDashboard: (token: string, studentId?: string) =>
    apiRequest<TwinDashboardResponse>("/twin/dashboard", {
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  twin: (token: string, studentId?: string) =>
    apiRequest<TwinResponse>("/twin", {
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  recommendations: (token: string, studentId?: string, limit = 20) =>
    apiRequest<TwinRecommendationResponse[]>("/twin/recommendations", {
      ...withToken(token),
      query: { limit, ...(studentId ? { student_id: studentId } : {}) },
    }),
  learningGraph: (token: string, studentId?: string, limit = 50) =>
    apiRequest<LearningGraphOverviewResponse>("/learning-graph", {
      ...withToken(token),
      query: { limit, ...(studentId ? { student_id: studentId } : {}) },
    }),
  readiness: (token: string, studentId?: string) =>
    apiRequest<LearningGraphReadinessResponse>("/learning-graph/readiness", {
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  weaknesses: (token: string, studentId?: string, limit = 10) =>
    apiRequest<LearningGraphWeaknessesResponse>("/learning-graph/weaknesses", {
      ...withToken(token),
      query: { limit, ...(studentId ? { student_id: studentId } : {}) },
    }),
  revisionQueue: (token: string, studentId?: string, limit = 100) =>
    apiRequest<RevisionQueueItem[]>("/learning-graph/revisions/queue", {
      ...withToken(token),
      query: { limit, ...(studentId ? { student_id: studentId } : {}) },
    }),
  studyPlan: (token: string, examId?: string, studentId?: string) =>
    apiRequest<StudyPlanResponse>("/study-plan", {
      ...withToken(token),
      query: {
        ...(examId ? { exam_id: examId } : {}),
        ...(studentId ? { student_id: studentId } : {}),
      },
    }),
  completePlanItem: (token: string, body: StudyPlanExecutionRequest, studentId?: string) =>
    apiRequest("/study-plan/items/complete", {
      method: "POST",
      body,
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  skipPlanItem: (token: string, body: StudyPlanExecutionRequest, studentId?: string) =>
    apiRequest("/study-plan/items/skip", {
      method: "POST",
      body,
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  getGoal: (token: string, examId: string, studentId?: string) =>
    apiRequest<GoalResponse | null>("/goals", {
      ...withToken(token),
      query: { exam_id: examId, ...(studentId ? { student_id: studentId } : {}) },
    }),
  createGoal: (token: string, body: GoalUpsertRequest, studentId?: string) =>
    apiRequest<GoalResponse>("/goals", {
      method: "POST",
      body,
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  updateGoal: (token: string, body: GoalUpsertRequest, studentId?: string) =>
    apiRequest<GoalResponse>("/goals", {
      method: "PUT",
      body,
      ...withToken(token),
      query: studentId ? { student_id: studentId } : undefined,
    }),
  submitStudySession: (token: string, body: RecordStudySessionRequest) =>
    apiRequest<LearningGraphActivityResponse>("/learning-graph/activities/study-session", {
      method: "POST",
      body,
      ...withToken(token),
    }),
  submitRevision: (token: string, body: RecordRevisionRequest) =>
    apiRequest<LearningGraphActivityResponse>("/learning-graph/activities/revision", {
      method: "POST",
      body,
      ...withToken(token),
    }),
  submitAssessment: (token: string, body: RecordAssessmentRequest) =>
    apiRequest<LearningGraphActivityResponse>("/learning-graph/activities/assessment", {
      method: "POST",
      body,
      ...withToken(token),
    }),
  submitPyqChange: (token: string, body: RecordPyqChangeRequest) =>
    apiRequest<LearningGraphActivityResponse>("/learning-graph/activities/pyq-change", {
      method: "POST",
      body,
      ...withToken(token),
    }),
  generatePlan: (token: string, examId?: string, dailyMinutes?: number) =>
    apiRequest<import("@/lib/types/api").AdaptivePlanResponse>("/planning/generate", {
      method: "POST",
      body: { exam_id: examId ?? "upsc_cse", daily_minutes: dailyMinutes },
      ...withToken(token),
    }),
  currentPlan: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").AdaptivePlanResponse>("/planning/current", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  planHistory: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").PlanHistoryResponse>("/planning/history", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  completeAdaptivePlanItem: (token: string, itemId: string) =>
    apiRequest<{ item_id: string; completion_status: string }>(
      `/planning/item/${itemId}/complete`,
      { method: "POST", ...withToken(token) },
    ),
  explainPlanConcept: (token: string, conceptId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").PlanExplainResponse>(`/planning/explain/${conceptId}`, {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  generateForecast: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").GoalForecastResponse>("/forecasting/generate", {
      method: "POST",
      body: { exam_id: examId ?? "upsc_cse" },
      ...withToken(token),
    }),
  currentForecast: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").GoalForecastResponse>("/forecasting/current", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  forecastScenarios: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").ForecastScenarioItem[]>("/forecasting/scenarios", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  simulateCustomScenario: (token: string, weeklyMinutes: number, examId?: string) =>
    apiRequest<import("@/lib/types/api").ForecastScenarioItem>("/forecasting/scenario/custom", {
      method: "POST",
      body: { exam_id: examId ?? "upsc_cse", weekly_minutes: weeklyMinutes },
      ...withToken(token),
    }),
  explainForecast: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").ForecastExplainResponse>("/forecasting/explain", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  forecastHistory: (token: string, examId?: string, limit = 20) =>
    apiRequest<import("@/lib/types/api").ForecastHistoryResponse>("/forecasting/history", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse", limit },
    }),
  myInterventionHistory: (token: string, examId?: string, limit = 20) =>
    apiRequest<import("@/lib/types/api").InterventionHistoryResponse>("/interventions/my-history", {
      ...withToken(token),
      query: examId ? { exam_id: examId, limit } : { limit },
    }),
};

export const mentorApi = {
  dashboard: (token: string) =>
    apiRequest<MentorDashboardResponse>("/mentor/dashboard", withToken(token)),
  queue: (token: string, limit = 50) =>
    apiRequest<MentorQueueItem[]>("/mentor/queue", {
      ...withToken(token),
      query: { limit },
    }),
  getCase: (token: string, caseId: string) =>
    apiRequest<MentorCaseResponse>(`/mentor/cases/${caseId}`, withToken(token)),
  addNote: (token: string, caseId: string, note: string) =>
    apiRequest<MentorCaseResponse>(`/mentor/cases/${caseId}/notes`, {
      method: "POST",
      body: { note },
      ...withToken(token),
    }),
  resolveCase: (token: string, caseId: string, resolutionReason: string) =>
    apiRequest<MentorCaseResponse>(`/mentor/cases/${caseId}/resolve`, {
      method: "POST",
      body: { resolution_reason: resolutionReason },
      ...withToken(token),
    }),
  studentPlan: (token: string, studentId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").AdaptivePlanResponse>(`/planning/student/${studentId}`, {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  regenerateStudentPlan: (token: string, studentId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").AdaptivePlanResponse>(
      `/planning/student/${studentId}/regenerate`,
      {
        method: "POST",
        body: { exam_id: examId ?? "upsc_cse" },
        ...withToken(token),
      },
    ),
  studentForecast: (token: string, studentId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").GoalForecastResponse>(
      `/forecasting/student/${studentId}`,
      {
        ...withToken(token),
        query: { exam_id: examId ?? "upsc_cse" },
      },
    ),
  simulateStudentForecast: (token: string, studentId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").GoalForecastResponse>(
      `/forecasting/student/${studentId}/simulate`,
      {
        method: "POST",
        body: { exam_id: examId ?? "upsc_cse" },
        ...withToken(token),
      },
    ),
  interventionQueue: (token: string, limit = 20) =>
    apiRequest<import("@/lib/types/api").MentorInterventionQueueResponse>("/interventions/queue", {
      ...withToken(token),
      query: { limit },
    }),
  studentInterventions: (token: string, studentId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").StudentInterventionResponse>(
      `/interventions/student/${studentId}`,
      {
        ...withToken(token),
        query: { exam_id: examId ?? "upsc_cse" },
      },
    ),
  generateStudentInterventions: (token: string, studentId: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").StudentInterventionResponse>(
      `/interventions/student/${studentId}/generate`,
      {
        method: "POST",
        body: { exam_id: examId ?? "upsc_cse" },
        ...withToken(token),
      },
    ),
  executeIntervention: (token: string, interventionId: string) =>
    apiRequest<import("@/lib/types/api").InterventionRecordItem>(
      `/interventions/${interventionId}/execute`,
      { method: "POST", ...withToken(token) },
    ),
  completeIntervention: (token: string, interventionId: string) =>
    apiRequest<import("@/lib/types/api").InterventionHistoryResponse>(
      `/interventions/${interventionId}/complete`,
      { method: "POST", ...withToken(token) },
    ),
  explainIntervention: (token: string, interventionId: string) =>
    apiRequest<import("@/lib/types/api").InterventionExplainResponse>(
      `/interventions/${interventionId}/explain`,
      withToken(token),
    ),
  cohortSummary: (token: string, examId?: string, refresh = false) =>
    apiRequest<import("@/lib/types/api").CohortSummaryResponse>("/cohort/summary", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse", refresh },
    }),
  cohortStudents: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").CohortStudentsResponse>("/cohort/students", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  cohortSegments: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").CohortSegmentsResponse>("/cohort/segments", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  cohortRisks: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").CohortRisksResponse>("/cohort/risks", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  cohortTrends: (token: string, examId?: string, period = "weekly") =>
    apiRequest<import("@/lib/types/api").CohortTrendsResponse>("/cohort/trends", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse", period },
    }),
};

export const copilotApi = {
  query: (
    token: string,
    body: import("@/features/copilot/types").CopilotQueryRequest,
  ) =>
    apiRequest<import("@/features/copilot/types").CopilotQueryResponse>("/copilot/query", {
      method: "POST",
      body,
      ...withToken(token),
    }),
};

export const adminCopilotApi = {
  analytics: (token: string, days = 30) =>
    apiRequest<import("@/lib/types/api").CopilotAnalyticsResponse>(
      "/admin/copilot/analytics",
      { query: { days }, ...withToken(token) },
    ),
  exportCsv: (token: string, days = 30) =>
    apiRequestText("/admin/copilot/analytics/export", {
      query: { days },
      ...withToken(token),
    }),
};

export const adminKnowledgeApi = {
  listSources: (
    token: string,
    query?: { exam_id?: string; limit?: number; offset?: number },
  ) =>
    apiRequest<KnowledgeSourceListResponse>("/knowledge/sources", {
      query,
      ...withToken(token),
    }),
  getSource: (token: string, sourceId: string) =>
    apiRequest<KnowledgeSourceResponse>(`/knowledge/sources/${sourceId}`, withToken(token)),
  uploadSource: (token: string, formData: FormData) =>
    apiRequestForm<KnowledgeSourceResponse>("/knowledge/sources", {
      method: "POST",
      formData,
      ...withToken(token),
    }),
  metrics: (token: string) =>
    apiRequest<KnowledgeIndexingMetricsResponse>("/admin/knowledge/metrics", withToken(token)),
};

export const adminCurrentAffairsApi = {
  listArticles: (
    token: string,
    query?: { exam_id?: string; limit?: number; offset?: number },
  ) =>
    apiRequest<import("@/lib/types/api").CurrentAffairsArticleListResponse>("/current-affairs", {
      query,
      ...withToken(token),
    }),
  getArticle: (token: string, articleId: string) =>
    apiRequest<import("@/lib/types/api").CurrentAffairsArticleResponse>(
      `/current-affairs/${articleId}`,
      withToken(token),
    ),
  uploadArticle: (token: string, formData: FormData) =>
    apiRequestForm<import("@/lib/types/api").CurrentAffairsArticleResponse>("/current-affairs/upload", {
      method: "POST",
      formData,
      ...withToken(token),
    }),
  indexingMetrics: (token: string) =>
    apiRequest<import("@/lib/types/api").CurrentAffairsIndexingMetricsResponse>(
      "/current-affairs/metrics/indexing",
      withToken(token),
    ),
  analytics: (token: string, periodDays = 30) =>
    apiRequest<import("@/lib/types/api").CurrentAffairsAnalyticsResponse>(
      "/current-affairs/metrics/analytics",
      { query: { period_days: periodDays }, ...withToken(token) },
    ),
};

export const adminPyqApi = {
  upload: (token: string, formData: FormData) =>
    apiRequestForm<import("@/lib/types/api").PyqUploadResponse>("/pyq/upload", {
      method: "POST",
      formData,
      ...withToken(token),
    }),
  getQuestion: (token: string, questionId: string) =>
    apiRequest<import("@/lib/types/api").PyqQuestionResponse>(`/pyq/${questionId}`, withToken(token)),
  trends: (token: string, examId = "upsc_cse", limit = 20) =>
    apiRequest<import("@/lib/types/api").PyqTrendsResponse>("/pyq/trends", {
      query: { exam_id: examId, limit },
      ...withToken(token),
    }),
  coverage: (token: string, examId = "upsc_cse") =>
    apiRequest<import("@/lib/types/api").PyqCoverageResponse>("/pyq/coverage", {
      query: { exam_id: examId },
      ...withToken(token),
    }),
  mappingReview: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").PyqMappingReviewItem[]>("/pyq/mappings/review", {
      query: examId ? { exam_id: examId } : undefined,
      ...withToken(token),
    }),
  indexingMetrics: (token: string) =>
    apiRequest<import("@/lib/types/api").PyqIndexingMetricsResponse>(
      "/pyq/metrics/indexing",
      withToken(token),
    ),
  analytics: (token: string, periodDays = 30) =>
    apiRequest<import("@/lib/types/api").PyqAnalyticsResponse>("/pyq/metrics/analytics", {
      query: { period_days: periodDays },
      ...withToken(token),
    }),
};

export const adminRagQualityApi = {
  metrics: (token: string, periodDays = 30) =>
    apiRequest<import("@/lib/types/api").RagQualityResponse>("/admin/rag-quality", {
      query: { period_days: periodDays },
      ...withToken(token),
    }),
  exportCsv: (token: string, periodDays = 30) =>
    apiRequestText("/admin/rag-quality/export", {
      query: { period_days: periodDays },
      ...withToken(token),
    }),
};

export const adminRecommendationsApi = {
  analytics: (token: string, periodDays = 30) =>
    apiRequest<import("@/features/copilot/types").RecommendationAnalyticsResponse>(
      "/admin/recommendations",
      { query: { period_days: periodDays }, ...withToken(token) },
    ),
};

export const adminRecommendationEffectivenessApi = {
  dashboard: (token: string, periodDays = 30) =>
    apiRequest<import("@/lib/types/api").RecommendationEffectivenessAdminResponse>(
      "/admin/recommendation-effectiveness",
      { query: { period_days: periodDays }, ...withToken(token) },
    ),
  exportCsv: (token: string, periodDays = 30) =>
    apiRequestText("/admin/recommendation-effectiveness/export", {
      query: { period_days: periodDays },
      ...withToken(token),
    }),
};

export const adminMemoryApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").MemoryAdminResponse>("/admin/memory", {
      ...withToken(token),
    }),
  exportCsv: (token: string, userId?: string) =>
    apiRequestText("/admin/memory/export", {
      query: userId ? { user_id: userId } : undefined,
      ...withToken(token),
    }),
};

export const adminPlanningApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").PlanningAdminResponse>("/admin/planning", {
      ...withToken(token),
    }),
  exportCsv: (token: string) =>
    apiRequestText("/admin/planning/export", { ...withToken(token) }),
};

export const adminForecastingApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").ForecastAdminResponse>("/admin/forecasting", {
      ...withToken(token),
    }),
  exportCsv: (token: string) =>
    apiRequestText("/admin/forecasting/export", { ...withToken(token) }),
};

export const adminInterventionsApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").InterventionAdminResponse>("/admin/interventions", {
      ...withToken(token),
    }),
  exportCsv: (token: string) =>
    apiRequestText("/admin/interventions/export", { ...withToken(token) }),
};

export const adminCohortApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").CohortAdminResponse>("/admin/cohort", {
      ...withToken(token),
    }),
  summary: (token: string, examId?: string, refresh = true) =>
    apiRequest<import("@/lib/types/api").CohortSummaryResponse>("/admin/cohort/summary", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse", refresh },
    }),
  segments: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").CohortSegmentsResponse>("/admin/cohort/segments", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  trends: (token: string, examId?: string, period = "monthly") =>
    apiRequest<import("@/lib/types/api").CohortTrendsResponse>("/admin/cohort/trends", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse", period },
    }),
  risks: (token: string, examId?: string) =>
    apiRequest<import("@/lib/types/api").CohortRisksResponse>("/admin/cohort/risks", {
      ...withToken(token),
      query: { exam_id: examId ?? "upsc_cse" },
    }),
  exportCsv: (token: string) =>
    apiRequestText("/admin/cohort/export", { ...withToken(token) }),
};

export const adminInstitutionApi = {
  dashboard: (token: string, refresh = false) =>
    apiRequest<import("@/lib/types/api").InstitutionDashboardResponse>("/admin/institution", {
      ...withToken(token),
      query: { refresh },
    }),
  insights: (token: string, refresh = false) =>
    apiRequest<import("@/lib/types/api").InstitutionInsightsResponse>("/admin/institution/insights", {
      ...withToken(token),
      query: { refresh },
    }),
  recommendations: (token: string, refresh = false) =>
    apiRequest<import("@/lib/types/api").InstitutionRecommendationsResponse>(
      "/admin/institution/recommendations",
      {
        ...withToken(token),
        query: { refresh },
      },
    ),
  trends: (token: string, period = "monthly", refresh = false) =>
    apiRequest<import("@/lib/types/api").InstitutionTrendsResponse>("/admin/institution/trends", {
      ...withToken(token),
      query: { period, refresh },
    }),
  mentorEffectiveness: (token: string) =>
    apiRequest<import("@/lib/types/api").InstitutionMentorEffectivenessResponse>(
      "/admin/institution/mentor-effectiveness",
      {
        ...withToken(token),
      },
    ),
  exportCsv: (token: string) =>
    apiRequestText("/admin/institution/export", { ...withToken(token) }),
  initiatives: (token: string, status?: string) =>
    apiRequest<import("@/lib/types/api").InstitutionInitiativesResponse>("/admin/institution/initiatives", {
      ...withToken(token),
      query: status ? { status } : undefined,
    }),
  createInitiative: (token: string, body: import("@/lib/types/api").CreateInitiativeRequest) =>
    apiRequest<import("@/lib/types/api").InstitutionInitiativeItem>("/admin/institution/initiatives", {
      ...withToken(token),
      method: "POST",
      body: JSON.stringify(body),
    }),
  outcomes: (token: string, refresh = false) =>
    apiRequest<import("@/lib/types/api").InstitutionOutcomesResponse>("/admin/institution/outcomes", {
      ...withToken(token),
      query: { refresh },
    }),
  roi: (token: string, refresh = false) =>
    apiRequest<import("@/lib/types/api").InstitutionRoiResponse>("/admin/institution/roi", {
      ...withToken(token),
      query: { refresh },
    }),
  exportRoiCsv: (token: string) =>
    apiRequestText("/admin/institution/roi/export", { ...withToken(token) }),
};

export const adminAgentsApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").AgentAdminDashboardResponse>("/admin/agents", {
      ...withToken(token),
    }),
  exportCsv: (token: string) =>
    apiRequestText("/admin/agents/export", { ...withToken(token) }),
  marketplace: (token: string) =>
    apiRequest<import("@/lib/types/api").AgentCapability[]>("/admin/agents/marketplace", {
      ...withToken(token),
    }),
};

export const adminAgentTracesApi = {
  list: (token: string, limit = 50, offset = 0) =>
    apiRequest<import("@/lib/types/api").AgentTraceListResponse>("/admin/agent-traces", {
      ...withToken(token),
      query: { limit, offset },
    }),
  get: (token: string, traceId: string) =>
    apiRequest<import("@/lib/types/api").AgentTraceRecord>(`/admin/agent-traces/${traceId}`, {
      ...withToken(token),
    }),
  exportJson: (token: string, traceId: string) =>
    apiRequest<Record<string, unknown>>(`/admin/agent-traces/${traceId}/export`, {
      ...withToken(token),
    }),
};

export const adminAgentCostsApi = {
  dashboard: (token: string) =>
    apiRequest<import("@/lib/types/api").AgentCostDashboardResponse>("/admin/agent-costs", {
      ...withToken(token),
    }),
};

export const adminAgentHealthApi = {
  leaderboard: (token: string) =>
    apiRequest<import("@/lib/types/api").AgentHealthLeaderboardResponse>("/admin/agents/health", {
      ...withToken(token),
    }),
};

export const adminApprovalsApi = {
  list: (token: string, status = "pending") =>
    apiRequest<import("@/lib/types/api").PendingActionListResponse>("/admin/approvals", {
      ...withToken(token),
      query: { status },
    }),
};

export const copilotApi = {
  feedback: (
    token: string,
    body: { trace_id: string; execution_id: string; rating: string; feedback_text?: string },
  ) =>
    apiRequest<{ feedback_id: string; status: string }>("/copilot/feedback", {
      ...withToken(token),
      method: "POST",
      body: JSON.stringify(body),
    }),
};
