import { ActivityForms } from "@/components/student/activity-forms";
import { PageHeader } from "@/components/ui/page-header";

export default function StudentActivitiesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Log activity"
        description="Record study sessions, revisions, assessments, and PYQ updates. Your dashboard and twin refresh automatically after each submission."
      />
      <ActivityForms />
    </div>
  );
}
