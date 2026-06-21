"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useAuth } from "@/providers/auth-provider";
import { useAuthStore } from "@/stores";

const loginSchema = z.object({
  tenant_slug: z.string().min(1, "Tenant is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const tenantSlug = useAuthStore((state) => state.tenantSlug);
  const registered = searchParams.get("registered") === "1";
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      tenant_slug: tenantSlug ?? "",
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    const tenant = searchParams.get("tenant");
    const email = searchParams.get("email");
    if (tenant) {
      setValue("tenant_slug", tenant);
    }
    if (email) {
      setValue("email", email);
    }
  }, [searchParams, setValue]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await login(values);
    } catch (error) {
      setError("root", {
        message: error instanceof Error ? error.message : "Login failed",
      });
    }
  });

  return (
    <form onSubmit={onSubmit} className="card-elevated relative mx-auto w-full max-w-md space-y-5 backdrop-blur-xl">
      <div>
        <h2 className="text-heading-sm text-foreground">Welcome back</h2>
        <p className="mt-1 text-sm text-foreground-muted">
          Sign in to continue your preparation journey.
        </p>
      </div>

      {registered ? (
        <p className="rounded-xl bg-growth-50 px-3 py-2 text-sm text-growth-800 dark:bg-growth-950/40 dark:text-growth-300" role="status">
          Institute account created. Sign in with your new credentials.
        </p>
      ) : null}

      <div>
        <label className="label" htmlFor="tenant_slug">
          Tenant slug
        </label>
        <input id="tenant_slug" className="input" {...register("tenant_slug")} />
        {errors.tenant_slug ? (
          <p className="mt-1 text-xs text-red-600">{errors.tenant_slug.message}</p>
        ) : null}
      </div>

      <div>
        <label className="label" htmlFor="email">
          Email
        </label>
        <input id="email" type="email" className="input" {...register("email")} />
        {errors.email ? (
          <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
        ) : null}
      </div>

      <div>
        <label className="label" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          className="input"
          {...register("password")}
        />
        {errors.password ? (
          <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
        ) : null}
      </div>

      {errors.root ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {errors.root.message}
        </p>
      ) : null}

      <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>

      <p className="text-center text-sm text-slate-600">
        Need a new institute?{" "}
        <Link href="/register" className="font-semibold text-growth-600 hover:underline">
          Register
        </Link>
      </p>
    </form>
  );
}
