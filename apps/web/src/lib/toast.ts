import { useToastStore } from "@/stores/toast-store";
import { ApiError } from "@/lib/api/errors";

export type ToastTone = "success" | "error" | "info";

export function toast(message: string, tone: ToastTone = "info"): void {
  useToastStore.getState().push({ message, tone });
}

export function toastSuccess(message: string): void {
  toast(message, "success");
}

export function toastError(message: string): void {
  toast(message, "error");
}

export function toastMutationError(error: unknown, fallback = "Request failed."): void {
  if (error instanceof ApiError) {
    toastError(error.message);
    return;
  }
  if (error instanceof Error && error.message) {
    toastError(error.message);
    return;
  }
  toastError(fallback);
}
