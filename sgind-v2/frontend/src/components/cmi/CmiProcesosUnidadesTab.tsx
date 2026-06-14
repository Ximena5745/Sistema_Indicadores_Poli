"use client";

import { useState } from "react";
import type { CMIProcesoDetalle, CMIUnidadDetalle } from "@/lib/types";
import { fmtPct } from "@/components/cmi/nivelUtils";

interface CmiProcesosUnidadesTabProps {
  procesos: CMIProcesoDetalle[];
  unidades: CMIUnidadDetalle[];
}

export function CmiProcesosUnidadesTab({ procesos, unidades }: CmiProcesosUnidadesTabProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-8">
      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-800">Unidades organizacionales</h3>
        {unidades.length === 0 ? (
          <p className="text-sm text-slate-500">No hay unidades para el corte seleccionado.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Unidad</th>
                  <th className="px-4 py-3 text-right">Procesos</th>
                  <th className="px-4 py-3 text-right">Indicadores</th>
                  <th className="px-4 py-3 text-right">Cumpl. prom.</th>
                  <th className="px-4 py-3 text-right">En riesgo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {unidades.map((u) => (
                  <tr key={u.unidad} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-800">{u.unidad}</td>
                    <td className="px-4 py-3 text-right">{u.n_procesos}</td>
                    <td className="px-4 py-3 text-right">{u.n_indicadores}</td>
                    <td className="px-4 py-3 text-right">{fmtPct(u.cumplimiento_promedio)}</td>
                    <td className="px-4 py-3 text-right text-amber-700">{u.en_riesgo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-800">Procesos y subprocesos</h3>
        {procesos.length === 0 ? (
          <p className="text-sm text-slate-500">No hay procesos para el corte seleccionado.</p>
        ) : (
          <div className="space-y-3">
            {procesos.map((p) => (
              <div key={p.proceso} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                <button
                  type="button"
                  onClick={() => setExpanded(expanded === p.proceso ? null : p.proceso)}
                  className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-slate-50"
                >
                  <div>
                    <p className="font-semibold text-slate-900">{p.proceso}</p>
                    <p className="text-xs text-slate-500">
                      {p.unidad || "Sin unidad"} · {p.tipo_proceso || "Sin tipo"} · {p.total_indicadores}{" "}
                      indicadores
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-poli-navy">{fmtPct(p.cumplimiento_promedio)}</p>
                    <p className="text-xs text-amber-700">{p.en_riesgo} en riesgo</p>
                  </div>
                </button>
                {expanded === p.proceso && p.subprocesos.length > 0 && (
                  <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-3">
                    <table className="min-w-full text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500">
                        <tr>
                          <th className="py-2 pr-4">Subproceso</th>
                          <th className="py-2 pr-4 text-right">Indicadores</th>
                          <th className="py-2 pr-4 text-right">Cumpl.</th>
                          <th className="py-2 text-right">Riesgo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {p.subprocesos.map((s) => (
                          <tr key={s.subproceso}>
                            <td className="py-2 pr-4 text-slate-800">{s.subproceso}</td>
                            <td className="py-2 pr-4 text-right">{s.n_indicadores}</td>
                            <td className="py-2 pr-4 text-right">{fmtPct(s.cumplimiento)}</td>
                            <td className="py-2 text-right text-amber-700">{s.en_riesgo}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
