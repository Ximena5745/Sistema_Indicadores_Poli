"use client";

import { useAuthStore } from "@/stores/auth-store";
import { isDevLoginEnabled, useDevLogin } from "@/hooks/use-dev-login";

export function Header() {
  const { email, role, clearSession } = useAuthStore();
  const { login, loading } = useDevLogin();
  const showDevLogin = isDevLoginEnabled();

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="text-sm text-slate-500">Panel de indicadores institucionales</div>
      <div className="flex items-center gap-3">
        {email ? (
          <>
            <div className="text-right text-sm">
              <div className="font-medium text-slate-800">{email}</div>
              {role && (
                <div className="text-xs capitalize text-slate-500">Rol: {role}</div>
              )}
            </div>
            <button
              type="button"
              onClick={clearSession}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
            >
              Cerrar sesión
            </button>
          </>
        ) : (
          <>
            {showDevLogin && (
              <button
                type="button"
                onClick={() => login()}
                disabled={loading}
                className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-800 hover:bg-emerald-100 disabled:opacity-50"
              >
                {loading ? "Conectando…" : "Acceso desarrollo"}
              </button>
            )}
            {showDevLogin ? (
              <span className="text-xs text-slate-400">o</span>
            ) : null}
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/login`}
              className="rounded-md bg-poli-blue px-4 py-2 text-sm font-medium text-white hover:bg-poli-blue-dark"
            >
              Iniciar sesión (Microsoft)
            </a>
          </>
        )}
      </div>
    </header>
  );
}
