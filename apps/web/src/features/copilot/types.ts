export type CopilotPersona = "student" | "mentor" | "admin";

export interface CopilotSource {
  label: string;
  reference: string;
}

export interface CopilotCitation {
  chunk_id: string;
  source_title: string;
}

export interface CopilotRecommendation {
  concept_id: string;
  concept_name: string;
  impact_score: number;
  reason_codes?: string[];
  reasons?: string[];
  estimated_readiness_gain: number;
  confidence: string;
  explanation?: string | null;
}

export interface CopilotCard {
  card_type: string;
  title: string;
  summary: string;
  explanation?: string | null;
  data?: Record<string, unknown>;
  expanded?: boolean;
}

export interface CopilotQueryRequest {
  persona: CopilotPersona;
  question: string;
  student_id?: string;
  case_id?: string;
  exam_id?: string;
  session_id?: string;
}

export interface CopilotQueryResponse {
  intent: string;
  answer: string;
  sources: CopilotSource[];
  citations?: CopilotCitation[];
  recommendations?: CopilotRecommendation[];
  cards?: CopilotCard[];
  confidence?: string | null;
  student_context_used?: boolean | null;
  session_id?: string | null;
  trace_id?: string | null;
  execution_id?: string | null;
  explanation?: string | null;
}

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  sources?: CopilotSource[];
  citations?: CopilotCitation[];
  recommendations?: CopilotRecommendation[];
  cards?: CopilotCard[];
  confidence?: string | null;
  studentContextUsed?: boolean | null;
  explanation?: string | null;
}

export interface RecommendationAnalyticsResponse {
  recommendation_acceptance_rate: number;
  completion_rate: number;
  average_readiness_gain: number;
  top_recommended_concepts: Array<{ concept_id: string; count: number }>;
  recommendation_effectiveness: number;
}
