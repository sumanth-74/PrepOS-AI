"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { adminApprovalsApi } from "@/lib/api";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthStore } from "@/stores";

export default function AdminApprovalsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "approvals"],
    queryFn: () => adminApprovalsApi.list(token!),
    enabled: Boolean(token),
  });

  return (
    <RoleGuard allowed={["institute_admin", "super_admin", "faculty"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Agent approval workflows"
          description="Review autonomous agent proposals before they affect learners."
        />
        <section className="card overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-2 py-2">Action</th>
                <th className="px-2 py-2">Agent</th>
                <th className="px-2 py-2">Subject</th>
                <th className="px-2 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {(query.data?.items ?? []).map((item) => (
                <tr key={item.action_id} className="border-b border-slate-100">
                  <td className="px-2 py-2">{item.action_type}</td>
                  <td className="px-2 py-2">{item.proposed_by_agent}</td>
                  <td className="px-2 py-2">{item.subject_key}</td>
                  <td className="px-2 py-2">{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <Link href="/admin/agents" className="btn-secondary inline-block">
          Back to agent dashboard
        </Link>
      </div>
    </RoleGuard>
  );
}
