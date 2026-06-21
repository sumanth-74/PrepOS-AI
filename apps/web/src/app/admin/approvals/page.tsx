"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApprovalsApi } from "@/lib/api";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useAuthStore } from "@/stores";

export default function AdminApprovalsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["admin", "approvals"],
    queryFn: () => adminApprovalsApi.list(token!),
    enabled: Boolean(token),
  });

  const approveMutation = useMutation({
    mutationFn: (actionId: string) => adminApprovalsApi.approve(token!, actionId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "approvals"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (actionId: string) => adminApprovalsApi.reject(token!, actionId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "approvals"] }),
  });

  return (
    <>
      <PageHeader
        title="Agent approval workflows"
        description="Review autonomous agent proposals before they affect learners."
      />
      <QueryBoundary
        query={query}
        loadingLabel="Loading pending approvals…"
        emptyTitle="No pending approvals"
        emptyDescription="Agent proposals requiring human review will appear here."
        isEmpty={(data) => data.items.length === 0}
      >
        {(data) => (
          <section className="card overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <caption className="sr-only">Pending agent approval actions</caption>
              <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <tr>
                  <th scope="col" className="px-2 py-2">
                    Action
                  </th>
                  <th scope="col" className="px-2 py-2">
                    Agent
                  </th>
                  <th scope="col" className="px-2 py-2">
                    Subject
                  </th>
                  <th scope="col" className="px-2 py-2">
                    Status
                  </th>
                  <th scope="col" className="px-2 py-2">
                    Decision
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.action_id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{item.action_type}</td>
                    <td className="px-2 py-2">{item.proposed_by_agent}</td>
                    <td className="px-2 py-2">{item.subject_key}</td>
                    <td className="px-2 py-2">{item.status}</td>
                    <td className="px-2 py-2">
                      {item.status === "pending" ? (
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="btn-primary"
                            disabled={approveMutation.isPending || rejectMutation.isPending}
                            onClick={() => approveMutation.mutate(item.action_id)}
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            className="btn-secondary"
                            disabled={approveMutation.isPending || rejectMutation.isPending}
                            onClick={() => rejectMutation.mutate(item.action_id)}
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </QueryBoundary>
    </>
  );
}
