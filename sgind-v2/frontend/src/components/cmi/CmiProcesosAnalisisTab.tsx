"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CMIProcesosDashboardResponse } from "@/lib/types";
import { CmiProcesosCalidadSection } from "@/components/cmi/CmiProcesosCalidadSection";
import { fmtPct } from "@/components/cmi/nivelUtils";

interface CmiProcesosAnalisisTabProps {
  data: CMIProcesosDashboardResponse;
}

const PROPUESTA_STYLES = [
  { key: "plan_mejoramiento", label: "Plan de mejoramiento", bg: "#fef3c7", border: "#92400e" },
  { key: "pdi", label: "PDI 2026-2030", bg: "#dbeafe", border: "#1e40af" },
  { key: "sga", label: "SGA", bg: "#ede9fe", border: "#4c1d95" },
  { key: "retos", label: "Retos", bg: "#ecfccb", border: "#365314" },
] as const;

export function CmiProcesosAnalisisTab({ data }: CmiProcesosAnalisisTabProps) {
  const { analisis_avanzado, calidad, meta, anio, mes_nombre } = data;
  const av = analisis_avanzado ?? {};
  const propuesta = av.propuesta_accion;
  const historico = useMemo(() => av.historico_indicadores ?? [], [av.historico_indicadores]);

  const [histId, setHistId] = useState(historico[0]?.id ?? "");

  const histChart = useMemo(() => {
    const item = historico.find((h) => h.id === histId);
    return item?.puntos ?? [];
  }, [historico, histId]);

  return (
    <div className="space-y-10">
      <p className="text-sm text-slate-600">
        Análisis avanzado para {anio} · {mes_nombre}. Base: {meta.base_anio}
        {meta.base_mes ? ` (mes ${meta.base_mes})` : ""}.
      </p>

      {propuesta && (
        <section>
          <h3 className="mb-4 text-lg font-semibold text-slate-800">Propuesta de acción</h3>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {PROPUESTA_STYLES.map((s) => (
              <div
                key={s.key}
                className="min-h-[120px] rounded-xl border p-4"
                style={{ backgroundColor: s.bg, borderColor: s.border }}
              >
                <p className="text-xs font-bold" style={{ color: s.border }}>
                  {s.label}
                </p>
                <p className="mt-2 text-sm leading-snug text-slate-800">
                  {propuesta[s.key as keyof typeof propuesta] as string}
                </p>
              </div>
            ))}
          </div>
          {propuesta.top_criticos?.length > 0 && (
            <div className="mt-4">
              <h4 className="mb-2 text-sm font-bold text-slate-700">Top indicadores críticos</h4>
              <ul className="space-y-1 text-sm text-slate-700">
                {propuesta.top_criticos.map((t) => (
                  <li key={t.indicador}>
                    <strong>{t.indicador}</strong> ({t.proceso}) — {fmtPct(t.cumplimiento)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {av.insights && (
        <section className="grid gap-4 lg:grid-cols-2">
          <InsightCard icon="🏆" title="Mayor mejora" text={av.insights.mejora_proceso} />
          <InsightCard icon="⚡" title="Mayor riesgo" text={av.insights.riesgo_proceso} />
        </section>
      )}

      {av.narrativa_proceso && (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="mb-2 text-sm font-bold text-slate-800">{av.narrativa_proceso.titulo}</h3>
          <div
            className="prose prose-sm max-w-none text-slate-700"
            dangerouslySetInnerHTML={{ __html: av.narrativa_proceso.texto_html }}
          />
        </section>
      )}

      <section className="grid gap-6 lg:grid-cols-2">
        <VariationTable title="Procesos con mayor mejora" rows={av.variacion_procesos?.mejoraron ?? []} positive />
        <VariationTable title="Procesos en mayor riesgo" rows={av.variacion_procesos?.empeoraron ?? []} positive={false} />
      </section>

      {historico.length > 0 && (
        <section>
          <h3 className="mb-3 text-lg font-semibold text-slate-800">Histórico de indicadores</h3>
          <label className="mb-3 flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-600">Indicador</span>
            <select
              value={histId}
              onChange={(e) => setHistId(e.target.value)}
              className="max-w-xl rounded-lg border border-slate-200 px-3 py-2"
            >
              {historico.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.indicador}
                </option>
              ))}
            </select>
          </label>
          {histChart.length > 0 && (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={histChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="periodo" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 120]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="cumplimiento" stroke="#1A3A5C" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </section>
      )}

      <CmiProcesosCalidadSection calidad={calidad} />
    </div>
  );
}

function InsightCard({ icon, title, text }: { icon: string; title: string; text: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-2xl">{icon}</p>
      <p className="mt-2 font-bold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-600">{text}</p>
    </div>
  );
}

function VariationTable({
  title,
  rows,
  positive,
}: {
  title: string;
  rows: Array<{ name: string; change: number }>;
  positive: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h4 className="mb-4 text-sm font-bold text-slate-800">{title}</h4>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">Sin datos comparativos.</p>
      ) : (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-500">
              <th className="py-2 text-left">Proceso</th>
              <th className="py-2 text-right">Variación</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name} className="border-t border-slate-100">
                <td className="py-2 text-slate-800">{r.name}</td>
                <td
                  className={`py-2 text-right font-bold ${positive ? "text-emerald-700" : "text-red-700"}`}
                >
                  {r.change > 0 ? "+" : ""}
                  {r.change.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
