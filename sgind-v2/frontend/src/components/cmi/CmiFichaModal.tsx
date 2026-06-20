"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CMIFichaIndicador } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";

interface CmiFichaModalProps {
  ficha: CMIFichaIndicador | null;
  loading?: boolean;
  onClose: () => void;
}

export function CmiFichaModal({ ficha, loading, onClose }: CmiFichaModalProps) {
  if (!ficha && !loading) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <h3 className="text-lg font-bold text-poli-navy">Ficha del indicador</h3>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-800">
            ✕
          </button>
        </div>

        {loading ? (
          <p className="p-6 text-sm text-slate-500">Cargando ficha...</p>
        ) : ficha ? (
          <div className="space-y-5 p-6">
            <div>
              <p className="text-xs text-slate-500">Código {ficha.Id}</p>
              <h4 className="text-xl font-bold text-slate-900">{ficha.Indicador}</h4>
              {ficha.Linea && (
                <span
                  className="mt-2 inline-block rounded-full px-3 py-1 text-xs font-bold"
                  style={{
                    color: ficha.linea_color ?? "#1A3A5C",
                    backgroundColor: `${ficha.linea_color ?? "#1A3A5C"}22`,
                    border: `1px solid ${ficha.linea_color ?? "#1A3A5C"}`,
                  }}
                >
                  {ficha.Linea}
                </span>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Meta" value={fmtMeta(ficha as Record<string, unknown>)} />
              <Stat label="Ejecución" value={fmtEjecucion(ficha as Record<string, unknown>)} />
              <Stat label="Cumplimiento" value={fmtPct(ficha.cumplimiento_pct as number | undefined)} />
            </div>

            <div>
              <NivelBadge nivel={ficha["Nivel de cumplimiento"] as string | undefined} />
            </div>

            {typeof ficha.Descripcion === "string" && ficha.Descripcion && (
              <div>
                <p className="text-xs font-semibold text-slate-500">Descripción</p>
                <p className="text-sm text-slate-700">{ficha.Descripcion}</p>
              </div>
            )}

            {ficha.historico && ficha.historico.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-700">Histórico Meta / Ejecución / %</p>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={ficha.historico}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="periodo" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="pct" tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Line yAxisId="pct" type="monotone" dataKey="cumplimiento" stroke="#1A3A5C" name="%" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-bold text-slate-900">{value}</p>
    </div>
  );
}
