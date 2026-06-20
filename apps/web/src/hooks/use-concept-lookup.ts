"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { catalogApi } from "@/lib/api";
import type { ConceptDisplayInfo, ExamTreeResponse } from "@/lib/types/api";
import { useAuthToken } from "@/providers/auth-provider";

function buildConceptCatalog(tree: ExamTreeResponse): Map<string, ConceptDisplayInfo> {
  const map = new Map<string, ConceptDisplayInfo>();

  for (const subjectEntry of tree.subjects) {
    for (const topicEntry of subjectEntry.topics) {
      for (const concept of topicEntry.concepts) {
        map.set(concept.concept_id, {
          conceptId: concept.concept_id,
          name: concept.concept_name,
          path: `${subjectEntry.subject.subject_name} › ${topicEntry.topic.topic_name}`,
          subjectName: subjectEntry.subject.subject_name,
          topicName: topicEntry.topic.topic_name,
        });
      }
    }
  }

  return map;
}

export function useConceptCatalog(examId: string | null | undefined) {
  const token = useAuthToken();

  return useQuery({
    queryKey: ["concept-catalog", examId],
    queryFn: () => catalogApi.getExamTree(examId!, token),
    enabled: Boolean(token && examId),
    staleTime: 60 * 60 * 1000,
  });
}

export function useConceptLookup(examId: string | null | undefined) {
  const catalogQuery = useConceptCatalog(examId);

  const catalog = useMemo(
    () => (catalogQuery.data ? buildConceptCatalog(catalogQuery.data) : new Map()),
    [catalogQuery.data],
  );

  const getConceptInfo = (conceptId: string): ConceptDisplayInfo | null =>
    catalog.get(conceptId) ?? null;

  return {
    catalogQuery,
    catalog,
    getConceptInfo,
    isLoading: catalogQuery.isLoading,
  };
}

export function useConceptInfo(examId: string | null | undefined, conceptId: string) {
  const token = useAuthToken();
  const { getConceptInfo, catalogQuery } = useConceptLookup(examId);
  const cached = getConceptInfo(conceptId);

  const fallbackQuery = useQuery({
    queryKey: ["concept", conceptId, "ancestors"],
    queryFn: async () => {
      const response = await catalogApi.getConceptAncestors(conceptId, token);
      return {
        conceptId: response.concept.concept_id,
        name: response.concept.concept_name,
        path: `${response.subject.subject_name} › ${response.topic.topic_name}`,
        subjectName: response.subject.subject_name,
        topicName: response.topic.topic_name,
      } satisfies ConceptDisplayInfo;
    },
    enabled: Boolean(token && conceptId && catalogQuery.isSuccess && !cached),
    staleTime: 60 * 60 * 1000,
  });

  return cached ?? fallbackQuery.data ?? null;
}
