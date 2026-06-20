"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { authApi } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore } from "@/stores";

const registerSchema = z
  .object({
    tenant_name: z.string().min(2, "Institute name is required"),
    tenant_slug: z
      .string()
      .min(2, "Tenant slug is required")
      .max(128)
      .regex(/^[a-z0-9-]+$/, "Use lowercase letters, numbers, and hyphens only"),
    full_name: z.string().min(1, "Full name is required"),
    email: z.string().email("Enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(8, "Confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const router = useRouter();
  const setTenantSlug = useAuthStore((state) => state.setTenantSlug);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      tenant_name: "",
      tenant_slug: "",
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await authApi.register({
        tenant_name: values.tenant_name,
        tenant_slug: values.tenant_slug,
        email: values.email,
        password: values.password,
        full_name: values.full_name,
      });
      setTenantSlug(values.tenant_slug);
      router.push(
        `/login?tenant=${encodeURIComponent(values.tenant_slug)}&email=${encodeURIComponent(values.email)}&registered=1`,
      );
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Registration failed";
      setError("root", { message });
    }
  });

  return (
    <form onSubmit={onSubmit} className="card mx-auto w-full max-w-md space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Create your institute</h1>
        <p className="mt-1 text-sm text-slate-600">
          Register a new PrepOS tenant. You will receive institute admin access. Students
          should sign in with credentials provided by their institute.
        </p>
      </div>

      <div>
        <label className="label" htmlFor="tenant_name">
          Institute name
        </label>
        <input id="tenant_name" className="input" {...register("tenant_name")} />
        {errors.tenant_name ? (
          <p className="mt-1 text-xs text-red-600">{errors.tenant_name.message}</p>
        ) : null}
      </div>

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
        <label className="label" htmlFor="full_name">
          Your full name
        </label>
        <input id="full_name" className="input" {...register("full_name")} />
        {errors.full_name ? (
          <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>
        ) : null}
      </div>

      <div>
        <label className="label" htmlFor="email">
          Email
        </label>
        <input id="email" type="email" className="input" autoComplete="email" {...register("email")} />
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
          autoComplete="new-password"
          {...register("password")}
        />
        {errors.password ? (
          <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
        ) : null}
      </div>

      <div>
        <label className="label" htmlFor="confirm_password">
          Confirm password
        </label>
        <input
          id="confirm_password"
          type="password"
          className="input"
          autoComplete="new-password"
          {...register("confirm_password")}
        />
        {errors.confirm_password ? (
          <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>
        ) : null}
      </div>

      {errors.root ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{errors.root.message}</p>
      ) : null}

      <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create institute account"}
      </button>

      <p className="text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-brand-700 hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
