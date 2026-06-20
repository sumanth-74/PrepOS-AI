import type { QueryClient } from "@tanstack/react-query";

/** Invalidate all student-facing queries after profile or activity changes. */
export function invalidateStudentData(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({ queryKey: ["student", "profile"] });
  void queryClient.invalidateQueries({ queryKey: ["twin"] });
  void queryClient.invalidateQueries({ queryKey: ["learning-graph"] });
  void queryClient.invalidateQueries({ queryKey: ["study-plan"] });
  void queryClient.invalidateQueries({ queryKey: ["goals"] });
}
