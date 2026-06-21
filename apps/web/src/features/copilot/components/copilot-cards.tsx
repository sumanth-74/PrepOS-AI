"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Calendar,
  FileText,
  Lightbulb,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";

import { cn } from "@/lib/utils/cn";

export interface CopilotCardData {
  card_type: string;
  title: string;
  summary: string;
  explanation?: string | null;
  data?: Record<string, unknown>;
  expanded?: boolean;
}

const CARD_CONFIG: Record<
  string,
  { icon: React.ReactNode; gradient: string; label: string }
> = {
  recommendation: {
    icon: <Lightbulb className="h-4 w-4" />,
    gradient: "from-growth-500/10 to-emerald-500/5",
    label: "Recommendation",
  },
  forecast: {
    icon: <TrendingUp className="h-4 w-4" />,
    gradient: "from-blue-500/10 to-cyan-500/5",
    label: "Forecast",
  },
  plan: {
    icon: <Calendar className="h-4 w-4" />,
    gradient: "from-violet-500/10 to-purple-500/5",
    label: "Study Plan",
  },
  intervention: {
    icon: <Zap className="h-4 w-4" />,
    gradient: "from-amber-500/10 to-orange-500/5",
    label: "Intervention",
  },
  pyq: {
    icon: <FileText className="h-4 w-4" />,
    gradient: "from-slate-500/10 to-slate-400/5",
    label: "PYQ",
  },
  current_affairs: {
    icon: <Sparkles className="h-4 w-4" />,
    gradient: "from-teal-500/10 to-green-500/5",
    label: "Current Affairs",
  },
  memory: {
    icon: <Brain className="h-4 w-4" />,
    gradient: "from-indigo-500/10 to-violet-500/5",
    label: "Memory",
  },
};

interface CopilotCardProps {
  card: CopilotCardData;
}

export function CopilotCard({ card }: CopilotCardProps) {
  const config = CARD_CONFIG[card.card_type] ?? {
    icon: <Target className="h-4 w-4" />,
    gradient: "from-growth-500/10 to-emerald-500/5",
    label: card.card_type,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-surface shadow-soft",
        "bg-gradient-to-br",
        config.gradient,
      )}
    >
      <div className="p-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-growth-100 text-growth-700 dark:bg-growth-900/50 dark:text-growth-300">
            {config.icon}
          </span>
          <span className="text-[10px] font-bold uppercase tracking-widest text-growth-700 dark:text-growth-400">
            {config.label}
          </span>
        </div>
        <p className="mt-3 text-sm font-semibold text-foreground">{card.title}</p>
        <p className="mt-1 text-xs leading-relaxed text-foreground-muted">{card.summary}</p>
        {card.explanation ? (
          <details className="mt-3 rounded-lg bg-surface/80 p-2.5 text-xs text-foreground-muted">
            <summary className="cursor-pointer font-medium text-foreground">Why this matters</summary>
            <p className="mt-2 leading-relaxed">{card.explanation}</p>
          </details>
        ) : null}
      </div>
    </motion.div>
  );
}

interface CopilotCardListProps {
  cards: CopilotCardData[];
}

export function CopilotCardList({ cards }: CopilotCardListProps) {
  if (cards.length === 0) return null;
  return (
    <div className="mt-3 space-y-2">
      {cards.map((card) => (
        <CopilotCard key={`${card.card_type}-${card.title}`} card={card} />
      ))}
    </div>
  );
}
