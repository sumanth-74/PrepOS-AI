"use client";

import Link from "next/link";
import { PageHeader } from "@/components/ui/page-header";

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="card w-full max-w-md text-center">
        <PageHeader
          title="Unauthorized"
          description="You do not have permission to view this page."
        />
        <Link href="/login" className="btn-primary">
          Return to sign in
        </Link>
      </div>
    </div>
  );
}
