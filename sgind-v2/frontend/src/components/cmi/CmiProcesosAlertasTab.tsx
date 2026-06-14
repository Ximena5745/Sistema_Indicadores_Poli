"use client";

import { useMemo, useState } from "react";
import type { Indicator } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";

interface CmiProcesosAlertasTabProps {
  peligro: number;
  alerta: number;
  items: Indicator[];
  onOpenFicha?: (id: string) => void;
}

export function CmiProcesosAlertasTab({ peligro, alerta, items, onOpenFicha }: CmiProcesosAlertasTabProps) {
  const [severidad, setSeveridad] = useState("Todos");
  const [proceso, setProceso] = useState("Todos");

  const procesos = useMemo(() => {
    const set = new Set(
      items
        .map((i) => (i as Record<string, unknown>).Proceso_padre as string | undefined)
        .filter(Boolean) as string[]
    );
    return ["Todos", ...Array.from(set).sort()];
  }, [items]);

  const filtered = useMemo(() => {
    return items.filter((ind) => {
      const nivel = ind["Nivel de cumplimiento"] as string | undefined;
      const proc = (ind as Record<string, unknown>).Proceso_padre as string | undefined;
      if (severidad !== "Todos" && nivel !== severidad) return false;
      if (proceso !== "Todos" && proc !== proceso) return false;
      return true;
    });
  }, [items, severidad, proceso]);

  if (!items.length) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center">
        <p className="text-lg font-semibold text-emerald-800">¡Excelente!</p>
        <p className="mt-1 text-sm text-emerald-700">No hay alertas activas en este corte.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-slate-800">Alertas críticas por proceso</h3>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg bg-red-100 p-5 text-center">
          <p className="text-3xl font-bold text-red-800">{peligro}</p>
          <p className="text-sm font-bold text-red-700">Peligro (&lt; 80%)</p>
        </div>
        <div className="rounded-lg bg-amber-100 p-5 text-center">
          <p className="text-3xl font-bold text-amber-800">{alerta}</p>
          <p className="text-sm font-bold text-amber-700">Alerta (80% – 99%)</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Severidad</span>
          <select
            value={severidad}
            onChange={(e) => setSeveridad(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            {["Todos", "Peligro", "Alerta"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Proceso</span>
          <select
            value={proceso}
            onChange={(e) => setProceso(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            {procesos.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="space-y-2">
        {filtered.map((ind) => {
          const id = String(ind.Id ?? "");
          const proc = (ind as Record<string, unknown>).Proceso_padre as string | undefined;
          return (
            <div
              key={id || String(ind.Indicador)}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3"
            >
              <div>
                {onOpenFicha && id ? (
                  <button
                    type="button"
                    onClick={() => onOpenFicha(id)}
                    className="font-semibold text-poli-blue hover:underline"
                  >
                    {ind.Indicador}
                  </button>
                ) : (
                  <p className="font-semibold text-slate-900">{ind.Indicador}</p>
                )}
                <p className="text-xs text-slate-500">{proc ?? ind.Proceso ?? "—"}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-slate-800">{fmtPct(ind.cumplimiento_pct as number)}</span>
                <NivelBadge nivel={ind["Nivel de cumplimiento"] as string} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
