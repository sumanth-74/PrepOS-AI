import { Inter } from "next/font/google";

import type { Metadata } from "next";
import { AppErrorBoundary } from "@/components/error-boundary";
import { ToastProvider } from "@/components/ui/toast-provider";
import { CopilotRoot } from "@/features/copilot/copilot-root";
import { AuthProvider } from "@/providers/auth-provider";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PrepOS — AI-Powered UPSC Learning Companion",
  description: "Every day you are getting closer to success.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              <AppErrorBoundary>
                {children}
                <ToastProvider />
                <CopilotRoot />
              </AppErrorBoundary>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
