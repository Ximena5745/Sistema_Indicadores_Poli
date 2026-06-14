"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function AuthCallbackClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      setSession(token);
      router.replace("/resumen-general");
    }
  }, [searchParams, setSession, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <p className="text-slate-600">Procesando autenticación…</p>
    </div>
  );
}
