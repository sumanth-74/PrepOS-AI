"use client";

import { create } from "zustand";

export interface ToastItem {
  id: string;
  message: string;
  tone: "success" | "error" | "info";
}

interface ToastState {
  items: ToastItem[];
  push: (item: Omit<ToastItem, "id">) => void;
  dismiss: (id: string) => void;
}

let toastCounter = 0;

export const useToastStore = create<ToastState>((set) => ({
  items: [],
  push: (item) => {
    const id = `toast-${++toastCounter}`;
    set((state) => ({ items: [...state.items, { ...item, id }] }));
    setTimeout(() => {
      set((state) => ({ items: state.items.filter((t) => t.id !== id) }));
    }, 5_000);
  },
  dismiss: (id) =>
    set((state) => ({ items: state.items.filter((t) => t.id !== id) })),
}));
