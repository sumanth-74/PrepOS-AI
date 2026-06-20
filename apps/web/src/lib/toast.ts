import { useToastStore } from "@/stores/toast-store";

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
