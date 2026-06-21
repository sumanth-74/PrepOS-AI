"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useSpring, useTransform } from "framer-motion";

import { cn } from "@/lib/utils/cn";

interface AnimatedCounterProps {
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  className?: string;
  duration?: number;
}

export function AnimatedCounter({
  value,
  decimals = 0,
  suffix = "",
  prefix = "",
  className,
  duration = 1.2,
}: AnimatedCounterProps) {
  const spring = useSpring(0, { stiffness: 75, damping: 18, duration: duration * 1000 });
  const display = useTransform(spring, (v) => `${prefix}${v.toFixed(decimals)}${suffix}`);
  const [text, setText] = useState(`${prefix}${(0).toFixed(decimals)}${suffix}`);

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  useEffect(() => {
    return display.on("change", (v) => setText(v));
  }, [display]);

  return (
    <motion.span className={className} aria-live="polite">
      {text}
    </motion.span>
  );
}

interface ProgressRingProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  className?: string;
  celebrate?: boolean;
}

export function ProgressRing({
  value,
  max = 100,
  size = 120,
  strokeWidth = 8,
  label,
  sublabel,
  className,
  celebrate = false,
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(value / max, 0), 1);
  const offset = circumference * (1 - pct);
  const prevPct = useRef(pct);

  useEffect(() => {
    if (celebrate && pct > prevPct.current) {
      prevPct.current = pct;
    }
  }, [celebrate, pct]);

  return (
    <div className={cn("relative inline-flex", className)} style={{ width: size, height: size }} role="img" aria-label={label}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-border"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#growthGradient)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
        <defs>
          <linearGradient id="growthGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#16a34a" />
            <stop offset="100%" stopColor="#4ade80" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-metric-sm font-bold text-foreground">{Math.round(pct * max)}</span>
        {label ? <span className="text-caption text-foreground-muted">{label}</span> : null}
        {sublabel ? <span className="text-[10px] text-foreground-subtle">{sublabel}</span> : null}
      </div>
    </div>
  );
}

interface CelebrationBurstProps {
  active: boolean;
  onComplete?: () => void;
}

export function CelebrationBurst({ active, onComplete }: CelebrationBurstProps) {
  if (!active) return null;

  const particles = Array.from({ length: 12 }, (_, i) => i);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {particles.map((i) => (
        <motion.span
          key={i}
          className="absolute left-1/2 top-1/2 h-1.5 w-1.5 rounded-full bg-growth-400"
          initial={{ opacity: 1, x: 0, y: 0, scale: 1 }}
          animate={{
            opacity: 0,
            x: Math.cos((i / 12) * Math.PI * 2) * 80,
            y: Math.sin((i / 12) * Math.PI * 2) * 80,
            scale: 0,
          }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          onAnimationComplete={i === 0 ? onComplete : undefined}
        />
      ))}
    </div>
  );
}
