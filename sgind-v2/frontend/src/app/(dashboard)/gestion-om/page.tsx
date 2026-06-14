"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FilterBar } from "@/components/ui/FilterBar";
import { fetchOM } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export default function GestionOMPage() {
  const token = useAuthStore((s) => s.token);
  const role = useAuthStore((s) => s.role);
  const [anio, setAnio] = useState(new Date().getFullYear());
  const [periodo, setPeriodo] = useState("");

  const params = { anio, ...(periodo ? { periodo } : {}) };

  const query = useQuery({
    queryKey: ["om", params],
    queryFn: () => fetchOM(params),
    enabled: !!token,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Gestión OM</h2>
          <p className="mt-1 text-slate-600">Oportunidades de mejora registradas</p>
        </div>
        {role === "calidad" || role === "desempeno" ? (
          <span className="rounded-md bg-green-50 px-3 py-1 text-xs text-green-700">
            Permisos de edición — Fase 5+
          </span>
        ) : null}
      </div>

      <FilterBar
        anio={anio}
        periodo={periodo}
        onAnioChange={setAnio}
        onPeriodoChange={setPeriodo}
      />

      {!token ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver registros OM.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : !query.data?.length ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
          No hay registros OM para los filtros seleccionados.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Indicador</th>
                <th className="px-4 py-3">Proceso</th>
                <th className="px-4 py-3">Periodo</th>
                <th className="px-4 py-3">Nº OM</th>
                <th className="px-4 py-3">Registrado por</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {query.data.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-800">{row.nombre_indicador}</div>
                    <div className="font-mono text-xs text-slate-400">{row.id_indicador}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{row.proceso ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {row.periodo} {row.anio}
                  </td>
                  <td className="px-4 py-3">{row.numero_om ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-500">{row.registrado_por ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
