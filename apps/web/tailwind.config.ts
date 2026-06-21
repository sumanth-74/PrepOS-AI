import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        growth: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
        accent: {
          DEFAULT: "#10b981",
          light: "#34d399",
          dark: "#059669",
        },
        surface: {
          DEFAULT: "hsl(var(--surface) / <alpha-value>)",
          raised: "hsl(var(--surface-raised) / <alpha-value>)",
          overlay: "hsl(var(--surface-overlay) / <alpha-value>)",
        },
        border: {
          DEFAULT: "hsl(var(--border) / <alpha-value>)",
          subtle: "hsl(var(--border-subtle) / <alpha-value>)",
        },
        foreground: {
          DEFAULT: "hsl(var(--foreground) / <alpha-value>)",
          muted: "hsl(var(--foreground-muted) / <alpha-value>)",
          subtle: "hsl(var(--foreground-subtle) / <alpha-value>)",
        },
        brand: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      fontSize: {
        display: ["3rem", { lineHeight: "1.1", letterSpacing: "-0.03em", fontWeight: "700" }],
        "display-sm": ["2.25rem", { lineHeight: "1.15", letterSpacing: "-0.025em", fontWeight: "700" }],
        heading: ["1.5rem", { lineHeight: "1.25", letterSpacing: "-0.02em", fontWeight: "600" }],
        "heading-sm": ["1.125rem", { lineHeight: "1.35", letterSpacing: "-0.015em", fontWeight: "600" }],
        body: ["0.9375rem", { lineHeight: "1.6", fontWeight: "400" }],
        caption: ["0.75rem", { lineHeight: "1.5", letterSpacing: "0.02em", fontWeight: "500" }],
        metric: ["2rem", { lineHeight: "1", letterSpacing: "-0.03em", fontWeight: "700" }],
        "metric-sm": ["1.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" }],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        soft: "0 1px 2px 0 rgb(0 0 0 / 0.04), 0 1px 3px 0 rgb(0 0 0 / 0.06)",
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 4px 12px -2px rgb(0 0 0 / 0.08)",
        elevated:
          "0 4px 6px -1px rgb(0 0 0 / 0.08), 0 12px 24px -4px rgb(0 0 0 / 0.12)",
        glow: "0 0 0 1px rgb(34 197 94 / 0.15), 0 8px 32px -8px rgb(34 197 94 / 0.35)",
        "glow-lg": "0 0 0 1px rgb(34 197 94 / 0.2), 0 16px 48px -12px rgb(34 197 94 / 0.4)",
      },
      backgroundImage: {
        "gradient-growth": "linear-gradient(135deg, #16a34a 0%, #22c55e 50%, #4ade80 100%)",
        "gradient-growth-subtle":
          "linear-gradient(135deg, rgb(240 253 244) 0%, rgb(220 252 231) 100%)",
        "gradient-hero":
          "linear-gradient(135deg, hsl(var(--hero-from)) 0%, hsl(var(--hero-to)) 100%)",
        "gradient-mesh":
          "radial-gradient(at 40% 20%, rgb(34 197 94 / 0.12) 0px, transparent 50%), radial-gradient(at 80% 0%, rgb(16 185 129 / 0.08) 0px, transparent 50%), radial-gradient(at 0% 50%, rgb(74 222 128 / 0.06) 0px, transparent 50%)",
      },
      animation: {
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
        shimmer: "shimmer 1.8s ease-in-out infinite",
        "fade-up": "fade-up 0.5s ease-out forwards",
        "scale-in": "scale-in 0.35s ease-out forwards",
      },
      keyframes: {
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      transitionTimingFunction: {
        premium: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
