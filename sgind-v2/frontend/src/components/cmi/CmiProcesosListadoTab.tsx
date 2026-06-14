"use client";

import { useMemo, useState } from "react";
import type { Indicator } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";

interface CmiProcesosListadoTabProps {
  indicadores: Indicator[];
  summary: Record<string, number>;
  onOpenFicha?: (id: string) => void;
  onExportCsv?: () => void;
  onExportExcel?: () => void;
  exporting?: boolean;
}

const PAGE_SIZES = [25, 50, 100];

export function CmiProcesosListadoTab({
  indicadores,
  summary,
  onOpenFicha,
  onExportCsv,
  onExportExcel,
  exporting,
}: CmiProcesosListadoTabProps) {
  const [proceso, setProceso] = useState("Todos");
  const [estado, setEstado] = useState("Todos");
  const [busqueda, setBusqueda] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const procesos = useMemo(() => {
    const set = new Set(
      indicadores
        .map((i) => (i as Record<string, unknown>).Proceso_padre as string | undefined)
        .filter(Boolean) as string[]
    );
    return ["Todos", ...Array.from(set).sort()];
  }, [indicadores]);

  const filtered = useMemo(() => {
    return indicadores.filter((ind) => {
      const proc = (ind as Record<string, unknown>).Proceso_padre as string | undefined;
      const nivel = ind["Nivel de cumplimiento"] as string | undefined;
      if (proceso !== "Todos" && proc !== proceso) return false;
      if (estado !== "Todos" && nivel !== estado) return false;
      if (busqueda.trim() && !String(ind.Indicador ?? "").toLowerCase().includes(busqueda.trim().toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [indicadores, proceso, estado, busqueda]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageItems = filtered.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="grid flex-1 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <SummaryCard label="Total" value={summary.total ?? 0} />
        <SummaryCard label="Métricas" value={summary.metricas ?? 0} />
        <SummaryCard label="Sobrecumpl." value={summary.sobrecumplimiento ?? 0} color="text-emerald-700" />
        <SummaryCard label="Cumplimiento" value={summary.cumplimiento ?? 0} color="text-green-800" />
        <SummaryCard label="Alerta" value={summary.alerta ?? 0} color="text-amber-700" />
        <SummaryCard label="Peligro" value={summary.peligro ?? 0} color="text-red-700" />
        </div>
        <div className="flex gap-2">
          {onExportCsv && (
            <button
              type="button"
              onClick={onExportCsv}
              disabled={exporting}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Exportar CSV
            </button>
          )}
          {onExportExcel && (
            <button
              type="button"
              onClick={onExportExcel}
              disabled={exporting}
              className="rounded-lg bg-poli-navy px-3 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              Exportar Excel
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Proceso</span>
          <select
            value={proceso}
            onChange={(e) => {
              setProceso(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            {procesos.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Estado</span>
          <select
            value={estado}
            onChange={(e) => {
              setEstado(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            {["Todos", "Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro", "Pendiente de reporte"].map(
              (e) => (
                <option key={e} value={e}>
                  {e}
                </option>
              )
            )}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm sm:col-span-1">
          <span className="font-medium text-slate-600">Buscar</span>
          <input
            type="search"
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPage(0);
            }}
            placeholder="Nombre del indicador..."
            className="rounded-lg border border-slate-200 px-3 py-2"
          />
        </label>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Indicador</th>
              <th className="px-4 py-3">Proceso</th>
              <th className="px-4 py-3">Subproceso</th>
              <th className="px-4 py-3 text-right">Meta</th>
              <th className="px-4 py-3 text-right">Ejecución</th>
              <th className="px-4 py-3 text-right">Cumpl.</th>
              <th className="px-4 py-3">Nivel</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {pageItems.map((ind) => {
              const rec = ind as Record<string, unknown>;
              const id = String(ind.Id ?? "");
              return (
                <tr key={id || String(ind.Indicador)} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    {onOpenFicha && id ? (
                      <button
                        type="button"
                        onClick={() => onOpenFicha(id)}
                        className="text-left font-medium text-poli-blue hover:underline"
                      >
                        {ind.Indicador}
                      </button>
                    ) : (
                      <span className="font-medium text-slate-800">{ind.Indicador}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{String(rec.Proceso_padre ?? ind.Proceso ?? "—")}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {String(rec.Subproceso_final ?? ind.Subproceso ?? "—")}
                  </td>
                  <td className="px-4 py-3 text-right">{ind.Meta ?? "—"}</td>
                  <td className="px-4 py-3 text-right">{ind.Ejecucion ?? "—"}</td>
                  <td className="px-4 py-3 text-right">{fmtPct(ind.cumplimiento_pct as number)}</td>
                  <td className="px-4 py-3">
                    <NivelBadge nivel={ind["Nivel de cumplimiento"] as string} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <span className="text-slate-600">
          {filtered.length} indicadores · página {page + 1} de {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(0);
            }}
            className="rounded border border-slate-200 px-2 py-1"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s}/pág
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
          >
            Anterior
          </button>
          <button
            type="button"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color = "text-slate-900",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 text-center shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
