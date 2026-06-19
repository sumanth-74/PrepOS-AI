import { apiRequest } from "@/lib/api/client";
import type {
  GoalResponse,
  GoalUpsertRequest,
  LearningGraphOverviewResponse,
  LearningGraphReadinessResponse,
  LearningGraphWeaknessesResponse,
  LoginRequest,
  MentorCaseResponse,
  MentorDashboardResponse,
  MentorQueueItem,
  RevisionQueueItem,
  StudentProfileResponse,
  StudyPlanExecutionRequest,
  StudyPlanResponse,
  TokenResponse,
  TwinDashboardResponse,
  TwinRecommendationResponse,
  TwinResponse,
  UserResponse,
} from "@/lib/types/api";

function withToken(token: string | null) {
  return { token };
}

export const authApi = {
  login: (body: LoginRequest) =>
    apiRequest<TokenResponse>("/auth/login", { method: "POST", body }),
  me: (token: string) => apiRequest<UserResponse>("/auth/me", withToken(token)),
  logout: (token: string) =>
    apiRequest<void>("/auth/logout", { method: "POST", ...withToken(token) }),
};

export const studentApi = {
  profile: (token: string) =>
    apiRequest<StudentProfileResponse>("/students/me", withToken(token)),
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
};
