import { FadeIn } from "@/components/motion/primitives";
import { cn } from "@/lib/utils/cn";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  eyebrow?: string;
  className?: string;
}

export function PageHeader({ title, description, actions, eyebrow, className }: PageHeaderProps) {
  return (
    <FadeIn className={cn("mb-8", className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          {eyebrow ? (
            <p className="text-caption font-semibold uppercase tracking-widest text-growth-600">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="text-heading text-foreground sm:text-display-sm">{title}</h1>
          {description ? (
            <p className="mt-2 max-w-2xl text-body text-foreground-muted">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
      </div>
    </FadeIn>
  );
}
