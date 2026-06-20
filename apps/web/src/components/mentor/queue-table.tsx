"use client";

import Link from "next/link";
import { useMemo } from "react";
import { PriorityBadge } from "@/components/mentor/priority-badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { useExamCatalog } from "@/hooks/use-exam-lookup";
import { buildStudentDisplayName, useStudentProfiles } from "@/hooks/use-student-lookup";
import type { MentorQueueItem } from "@/lib/types/api";
import { formatLabel } from "@/lib/utils/format";

function escalationTone(level: string): "neutral" | "warning" | "danger" {
  const normalized = level.toUpperCase();
  if (normalized.includes("CRITICAL") || normalized.includes("HIGH")) return "danger";
  if (normalized.includes("MEDIUM") || normalized.includes("ELEVATED")) return "warning";
  return "neutral";
}

export function MentorQueueTable({ items }: { items: MentorQueueItem[] }) {
  const studentIds = useMemo(
    () => [...new Set(items.map((item) => item.student_id))],
    [items],
  );
  const profileQueries = useStudentProfiles(studentIds);
  const examsQuery = useExamCatalog();

  const profileMap = useMemo(() => {
    const map = new Map<string, { target_exam: string | null }>();
    studentIds.forEach((studentId, index) => {
      const profile = profileQueries[index]?.data;
      if (profile) {
        map.set(studentId, { target_exam: profile.target_exam });
      }
    });
    return map;
  }, [profileQueries, studentIds]);

  const examNameMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const exam of examsQuery.data ?? []) {
      map.set(exam.exam_id, exam.exam_name);
    }
    return map;
  }, [examsQuery.data]);

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Student</th>
            <th className="px-4 py-3">Action</th>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Escalation</th>
            <th className="px-4 py-3">Case</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const profile = profileMap.get(item.student_id);
            const examName = profile?.target_exam
              ? examNameMap.get(profile.target_exam) ?? formatLabel(profile.target_exam)
              : null;
            const displayName = buildStudentDisplayName(
              item.student_id,
              profile?.target_exam,
              examName ?? "—",
            );

            return (
              <tr key={item.case_id} className="border-b border-slate-100">
                <td className="px-4 py-3">
                  <div>
                    <Link
                      href={`/mentor/student/${item.student_id}`}
                      className="font-medium text-brand-700 hover:underline"
                    >
                      {displayName}
                    </Link>
                    {examName ? <p className="text-xs text-slate-500">{examName}</p> : null}
                  </div>
                </td>
                <td className="px-4 py-3">{formatLabel(item.mentor_action)}</td>
                <td className="px-4 py-3">
                  <PriorityBadge priorityScore={item.priority_score} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge
                    label={formatLabel(item.escalation_level)}
                    tone={escalationTone(item.escalation_level)}
                  />
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/mentor/cases/${item.case_id}`}
                    className="text-brand-700 hover:underline"
                  >
                    {formatLabel(item.case_status)}
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
