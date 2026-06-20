"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { ErrorState } from "@/components/ui/error-state";
import { captureException } from "@/lib/observability/sentry";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class AppErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    captureException(error, { componentStack: info.componentStack });
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-[50vh] items-center justify-center p-6">
          <div className="w-full max-w-lg">
            <ErrorState
              error={this.state.error}
              title={this.props.fallbackTitle ?? "Something went wrong"}
              onRetry={() => this.setState({ error: null })}
            />
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
