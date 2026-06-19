"use client";

import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";
import { useUiStore } from "@/stores";

interface NavItem {
  href: string;
  label: string;
}

interface AppShellProps {
  title: string;
  navItems: NavItem[];
  children: React.ReactNode;
}

export function AppShell({ title, navItems, children }: AppShellProps) {
  const { user, logout } = useAuth();
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);

  return (
    <div className="min-h-screen lg:flex">
      <aside
        className={`border-r border-slate-200 bg-white lg:w-64 ${
          sidebarOpen ? "block" : "hidden lg:block"
        }`}
      >
        <div className="border-b border-slate-200 px-5 py-4">
          <p className="text-lg font-semibold text-brand-700">PrepOS</p>
          <p className="text-xs text-slate-500">{title}</p>
        </div>
        <nav className="space-y-1 p-3">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            className="btn-secondary lg:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            Menu
          </button>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-sm text-slate-600 sm:inline">
              {user?.full_name ?? user?.email}
            </span>
            <button type="button" className="btn-secondary" onClick={() => void logout()}>
              Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
