"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import {
  ChevronRight,
  Menu,
  Moon,
  Search,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { PageTransition } from "@/components/motion/primitives";
import { Button } from "@/components/design-system/button";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/providers/auth-provider";
import { useUiStore } from "@/stores";

export interface NavItem {
  href: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string;
}

export interface NavSection {
  title?: string;
  items: NavItem[];
}

interface PremiumShellProps {
  title: string;
  subtitle?: string;
  navSections: NavSection[];
  flatNav?: NavItem[];
  children: React.ReactNode;
  showCopilotHint?: boolean;
}

function isActiveNav(pathname: string, href: string): boolean {
  if (href.endsWith("/dashboard") || href === "/admin") {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function PremiumShell({
  title,
  subtitle,
  navSections,
  flatNav,
  children,
  showCopilotHint = true,
}: PremiumShellProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);
  const [searchQuery, setSearchQuery] = useState("");

  const allNav = flatNav ?? navSections.flatMap((s) => s.items);
  const filteredNav =
    searchQuery.trim().length > 0
      ? allNav.filter((item) =>
          item.label.toLowerCase().includes(searchQuery.toLowerCase()),
        )
      : allNav;

  return (
    <div className="min-h-screen bg-surface bg-gradient-mesh lg:flex">
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen ? (
          <motion.div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
          />
        ) : null}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-surface/95 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <Link href={allNav[0]?.href ?? "/"} className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-growth shadow-glow">
                <Sparkles className="h-4 w-4 text-white" aria-hidden />
              </div>
              <div>
                <p className="text-sm font-bold text-foreground">PrepOS</p>
                <p className="text-[11px] text-foreground-muted">{title}</p>
              </div>
            </Link>
            {subtitle ? (
              <p className="mt-1 text-[11px] text-foreground-subtle">{subtitle}</p>
            ) : null}
          </div>
          <button
            type="button"
            className="btn-ghost lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="border-b border-border p-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-subtle" />
            <input
              type="search"
              className="input pl-9 text-sm"
              placeholder="Search navigation…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search navigation"
            />
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3" aria-label="Main navigation">
          {searchQuery.trim() ? (
            <ul className="space-y-1">
              {filteredNav.map((item) => (
                <NavLink
                  key={item.href}
                  item={item}
                  active={isActiveNav(pathname, item.href)}
                  onNavigate={() => setSidebarOpen(false)}
                />
              ))}
            </ul>
          ) : (
            navSections.map((section) => (
              <div key={section.title ?? "default"} className="mb-4">
                {section.title ? (
                  <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-foreground-subtle">
                    {section.title}
                  </p>
                ) : null}
                <ul className="space-y-0.5">
                  {section.items.map((item) => (
                    <NavLink
                      key={item.href}
                      item={item}
                      active={isActiveNav(pathname, item.href)}
                      onNavigate={() => setSidebarOpen(false)}
                    />
                  ))}
                </ul>
              </div>
            ))
          )}
        </nav>

        {showCopilotHint ? (
          <div className="border-t border-border p-4">
            <div className="rounded-xl border border-growth-200/60 bg-growth-50/50 p-3 dark:border-growth-800/40 dark:bg-growth-950/30">
              <p className="text-xs font-semibold text-growth-800 dark:text-growth-300">
                AI Copilot
              </p>
              <p className="mt-1 text-[11px] text-foreground-muted">
                Press the sparkle button anytime for intelligent guidance.
              </p>
            </div>
          </div>
        ) : null}
      </aside>

      {/* Main content */}
      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-border bg-surface/80 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-3 px-4 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                className="btn-ghost lg:hidden"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open navigation"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="hidden min-w-0 sm:block">
                <Breadcrumbs />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="btn-ghost"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                aria-label="Toggle theme"
              >
                {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
              <span className="hidden max-w-[140px] truncate text-sm text-foreground-muted md:inline">
                {user?.full_name ?? user?.email}
              </span>
              <Button variant="secondary" size="sm" onClick={() => void logout()}>
                Sign out
              </Button>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </div>
  );
}

function NavLink({
  item,
  active,
  onNavigate,
}: {
  item: NavItem;
  active: boolean;
  onNavigate: () => void;
}) {
  return (
    <li>
      <Link
        href={item.href}
        onClick={onNavigate}
        aria-current={active ? "page" : undefined}
        className={cn(
          "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
          active
            ? "nav-active"
            : "text-foreground-muted hover:bg-surface-raised hover:text-foreground",
        )}
      >
        {item.icon ? (
          <span className={cn("shrink-0", active ? "text-growth-600" : "text-foreground-subtle")}>
            {item.icon}
          </span>
        ) : null}
        <span className="truncate">{item.label}</span>
        {item.badge ? (
          <span className="ml-auto rounded-full bg-growth-100 px-2 py-0.5 text-[10px] font-semibold text-growth-700">
            {item.badge}
          </span>
        ) : active ? (
          <ChevronRight className="ml-auto h-4 w-4 opacity-60" aria-hidden />
        ) : null}
      </Link>
    </li>
  );
}
