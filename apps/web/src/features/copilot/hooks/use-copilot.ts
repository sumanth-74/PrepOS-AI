"use client";

import { usePathname } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import {
  COPILOT_PERSONA_LABELS,
  COPILOT_SUGGESTED_PROMPTS,
} from "@/features/copilot/suggested-prompts";
import type {
  CopilotMessage,
  CopilotPersona,
  CopilotQueryRequest,
  CopilotQueryResponse,
} from "@/features/copilot/types";
import { copilotApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { hasAnyRole, isMentorRole, isStudentRole } from "@/lib/auth/roles";
import type { AppRole } from "@/lib/types/api";
import { useAuth } from "@/providers/auth-provider";
import { useAuthStore } from "@/stores";

function resolvePersona(pathname: string, roles: AppRole[]): CopilotPersona | null {
  if (pathname.startsWith("/admin")) {
    return hasAnyRole(roles, ["institute_admin", "super_admin"]) ? "admin" : null;
  }
  if (pathname.startsWith("/mentor")) {
    return isMentorRole(roles) ? "mentor" : null;
  }
  if (pathname.startsWith("/student")) {
    return isStudentRole(roles) ? "student" : null;
  }
  if (isStudentRole(roles)) {
    return "student";
  }
  if (isMentorRole(roles)) {
    return "mentor";
  }
  if (hasAnyRole(roles, ["institute_admin", "super_admin"])) {
    return "admin";
  }
  return null;
}

function resolveContext(pathname: string): { studentId: string | null; caseId: string | null } {
  const studentMatch = pathname.match(/\/mentor\/student\/([^/]+)/);
  const caseMatch = pathname.match(/\/mentor\/cases\/([^/]+)/);
  return {
    studentId: studentMatch?.[1] ?? null,
    caseId: caseMatch?.[1] ?? null,
  };
}

function createMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useCopilot() {
  const pathname = usePathname();
  const { roles, isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const persona = useMemo(
    () => (isAuthenticated ? resolvePersona(pathname, roles) : null),
    [isAuthenticated, pathname, roles],
  );
  const context = useMemo(() => resolveContext(pathname), [pathname]);
  const suggestedPrompts = persona ? COPILOT_SUGGESTED_PROMPTS[persona] : [];
  const personaLabel = persona ? COPILOT_PERSONA_LABELS[persona] : "Copilot";

  const sendQuestion = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || !persona || !accessToken) {
        return;
      }

      setError(null);
      setIsLoading(true);
      setMessages((current) => [
        ...current,
        { id: createMessageId(), role: "user", content: trimmed },
      ]);
      setInput("");

      const body: CopilotQueryRequest = {
        persona,
        question: trimmed,
      };
      if (sessionId) {
        body.session_id = sessionId;
      }
      if (persona === "mentor" && context.studentId) {
        body.student_id = context.studentId;
      }
      if (persona === "mentor" && context.caseId) {
        body.case_id = context.caseId;
      }

      try {
        const response: CopilotQueryResponse = await copilotApi.query(accessToken, body);
        if (response.session_id) {
          setSessionId(response.session_id);
        }
        setMessages((current) => [
          ...current,
          {
            id: createMessageId(),
            role: "assistant",
            content: response.answer,
            intent: response.intent,
            sources: response.sources,
            citations: response.citations,
            recommendations: response.recommendations,
            confidence: response.confidence,
            studentContextUsed: response.student_context_used,
          },
        ]);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Copilot could not complete your request. Please try again.";
        setError(message);
        setMessages((current) => [
          ...current,
          {
            id: createMessageId(),
            role: "assistant",
            content: message,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [accessToken, context.caseId, context.studentId, persona, sessionId],
  );

  const clearConversation = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
  }, []);

  return {
    open,
    setOpen,
    input,
    setInput,
    messages,
    isLoading,
    error,
    persona,
    personaLabel,
    suggestedPrompts,
    context,
    sendQuestion,
    clearConversation,
  };
}
