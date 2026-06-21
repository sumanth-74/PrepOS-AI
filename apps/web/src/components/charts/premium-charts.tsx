"use client";

import {
  Area,
  AreaChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { cn } from "@/lib/utils/cn";

interface TrendPoint {
  label: string;
  value: number;
}

interface ReadinessSparklineProps {
  data: TrendPoint[];
  className?: string;
  height?: number;
}

export function ReadinessSparkline({ data, className, height = 120 }: ReadinessSparklineProps) {
  if (data.length === 0) return null;

  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="readinessFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" hide />
          <YAxis hide domain={["dataMin - 5", "dataMax + 5"]} />
          <Tooltip
            contentStyle={{
              borderRadius: "12px",
              border: "1px solid hsl(var(--border))",
              background: "hsl(var(--surface))",
              fontSize: "12px",
            }}
            formatter={(value) => [`${Number(value ?? 0).toFixed(1)}`, "Readiness"]}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#16a34a"
            strokeWidth={2}
            fill="url(#readinessFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

interface MiniBarChartProps {
  data: { name: string; value: number }[];
  className?: string;
  height?: number;
}

export function MiniBarChart({ data, className, height = 160 }: MiniBarChartProps) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className={cn("space-y-2", className)}>
      {data.map((item) => (
        <div key={item.name}>
          <div className="mb-1 flex justify-between text-xs">
            <span className="text-foreground-muted">{item.name}</span>
            <span className="font-medium text-foreground">{item.value}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-surface-raised">
            <div
              className="h-full rounded-full bg-gradient-growth transition-all duration-700"
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
      <div style={{ height: height - data.length * 36 }} />
    </div>
  );
}

interface HeatmapCell {
  label: string;
  value: number;
}

export function SegmentHeatmap({ cells, className }: { cells: HeatmapCell[]; className?: string }) {
  const max = Math.max(...cells.map((c) => c.value), 1);

  return (
    <div className={cn("grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4", className)}>
      {cells.map((cell) => {
        const intensity = cell.value / max;
        return (
          <div
            key={cell.label}
            className="rounded-xl border border-border p-3 transition-transform hover:scale-[1.02]"
            style={{
              background: `rgba(34, 197, 94, ${0.08 + intensity * 0.35})`,
            }}
          >
            <p className="text-xs text-foreground-muted">{cell.label}</p>
            <p className="mt-1 text-lg font-bold text-foreground">{cell.value}</p>
          </div>
        );
      })}
    </div>
  );
}

interface RadarPoint {
  dimension: string;
  value: number;
}

export function ReadinessRadar({
  data,
  className,
  height = 220,
}: {
  data: RadarPoint[];
  className?: string;
  height?: number;
}) {
  if (data.length === 0) return null;
  return (
    <div className={cn("w-full", className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 11, fill: "hsl(var(--foreground-muted))" }}
          />
          <Radar dataKey="value" stroke="#16a34a" fill="#22c55e" fillOpacity={0.35} />
          <Tooltip formatter={(v) => [`${Number(v ?? 0).toFixed(1)}`, "Score"]} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
