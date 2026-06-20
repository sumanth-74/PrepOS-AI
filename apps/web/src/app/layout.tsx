import type { Metadata } from "next";
import { AppErrorBoundary } from "@/components/error-boundary";
import { ToastProvider } from "@/components/ui/toast-provider";
import { CopilotRoot } from "@/features/copilot/copilot-root";
import { AuthProvider } from "@/providers/auth-provider";
import { QueryProvider } from "@/providers/query-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrepOS",
  description: "AI-powered exam preparation platform",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AuthProvider>
            <AppErrorBoundary>
              {children}
              <ToastProvider />
              <CopilotRoot />
            </AppErrorBoundary>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
