"use client";

import type { CMIProcesosDashboardResponse } from "@/lib/types";
import { CmiDonutNivelPlotly } from "@/components/cmi/CmiDonutNivelPlotly";
import { CmiMetricCard } from "@/components/cmi/CmiMetricCard";
import { CmiProcesosBarPlotly } from "@/components/cmi/CmiProcesosBarPlotly";

const NIVEL_COLORS: Record<string, string> = {
  Sobrecumplimiento: "#6699FF",
  Cumplimiento: "#43A047",
  Alerta: "#FBAF17",
  Peligro: "#D32F2F",
  "Pendiente de reporte": "#9E9E9E",
};

interface CmiProcesosResumenTabProps {
  data: CMIProcesosDashboardResponse;
}

export function CmiProcesosResumenTab({ data }: CmiProcesosResumenTabProps) {
  const {
    kpis,
    banner,
    distribucion_nivel,
    tipo_proceso_cards,
    proceso_bars,
    catalog_charts,
    meta,
    analisis_avanzado,
    variacion,
  } = data;
  const topCount = kpis.conteo_estados[kpis.top_nivel] ?? 0;
  const nivelColor = NIVEL_COLORS[kpis.top_nivel] ?? "#1A3A5C";
  const insights = analisis_avanzado?.insights;

  return (
    <div className="space-y-8">
      <h3 className="text-xl font-bold text-slate-900">Resumen Desglosado</h3>

      <div className="rounded-2xl border border-poli-navy/20 bg-gradient-to-br from-poli-navy via-[#234a73] to-[#2d5a8a] p-6 text-white shadow-[0_8px_32px_rgba(26,58,92,0.25)]">
        <p className="text-xs font-bold uppercase tracking-wider text-white/70">{banner.titulo}</p>
        <h3 className="mt-1 text-2xl font-bold">
          {banner.anio} · {banner.mes}
        </h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-4">
          <BannerStat
            label="Cumplimiento global"
            value={banner.cumplimiento_global != null ? `${banner.cumplimiento_global}%` : "—"}
          />
          <BannerStat
            label={`vs ${banner.base_anio}`}
            value={
              banner.variacion_pp != null
                ? `${banner.variacion_pp > 0 ? "+" : ""}${banner.variacion_pp} pp`
                : "—"
            }
          />
          <BannerStat label="Indicadores" value={String(banner.total_indicadores)} />
          <BannerStat label="En riesgo" value={String(banner.en_riesgo)} />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CmiMetricCard
          title="Indicadores CMI Procesos"
          value={String(kpis.total)}
          subtitle={`Con dato: ${kpis.con_dato}`}
          icon="📊"
          color="#1A3A5C"
        />
        <CmiMetricCard
          title="Promedio cumplimiento"
          value={`${kpis.promedio}%`}
          subtitle={`${kpis.n_procesos} procesos · ${kpis.n_subprocesos} subprocesos`}
          icon="📈"
          color="#43A047"
        />
        <CmiMetricCard
          title="Nivel predominante"
          value={kpis.top_nivel}
          subtitle={`${topCount} de ${kpis.total}`}
          icon="🏆"
          color={nivelColor}
        />
        <CmiMetricCard
          title="En riesgo"
          value={String(kpis.en_riesgo)}
          subtitle={`${kpis.n_unidades} unidades`}
          icon="⚠️"
          color={kpis.en_riesgo > 0 ? "#D32F2F" : "#43A047"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)] lg:col-span-3">
          <h4 className="mb-4 text-sm font-bold text-slate-800">
            Cumplimiento por proceso {meta.base_anio ? `(vs ${meta.base_anio})` : ""}
          </h4>
          <CmiProcesosBarPlotly data={proceso_bars} baseAnio={meta.base_anio} />
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)] lg:col-span-2">
          <h4 className="mb-4 text-sm font-bold text-slate-800">Distribución por nivel</h4>
          <CmiDonutNivelPlotly data={distribucion_nivel} total={kpis.total} />
        </div>
      </div>

      {insights && (insights.mejora_proceso || insights.riesgo_proceso) && (
        <div>
          <h4 className="mb-4 text-sm font-bold text-slate-800">Insights automáticos</h4>
          <div className="grid gap-3 lg:grid-cols-2">
            {insights.mejora_proceso && (
              <InsightCard
                emoji="🏆"
                title="Mayor mejora"
                text={insights.mejora_proceso}
                gradient="from-emerald-50 to-blue-50"
                borderColor="#43A047"
              />
            )}
            {insights.riesgo_proceso && (
              <InsightCard
                emoji="⚡"
                title="Mayor riesgo"
                text={insights.riesgo_proceso}
                gradient="from-red-50 to-amber-50"
                borderColor="#D32F2F"
              />
            )}
          </div>
        </div>
      )}

      {variacion.top_riesgo_procesos.length > 0 && (
        <div>
          <h4 className="mb-4 text-sm font-bold text-slate-800">Procesos con más indicadores en riesgo</h4>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {variacion.top_riesgo_procesos.slice(0, 6).map((p) => (
              <div
                key={p.proceso}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-[0_2px_8px_rgba(26,58,92,0.05)]"
              >
                <p className="text-sm font-bold text-slate-800">{p.proceso}</p>
                <p className="mt-2 text-2xl font-extrabold text-red-600">{p.n_riesgo}</p>
                <p className="text-xs text-slate-500">
                  en riesgo · cumpl. {p.cumplimiento != null ? `${p.cumplimiento}%` : "—"}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {tipo_proceso_cards.length > 0 && (
        <div>
          <h4 className="mb-4 text-sm font-bold text-slate-800">Por tipo de proceso</h4>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {tipo_proceso_cards.map((card) => (
              <div
                key={card.tipo}
                className="rounded-2xl border border-slate-200 p-4 shadow-[0_2px_12px_rgba(26,58,92,0.06)] transition hover:shadow-[0_6px_20px_rgba(26,58,92,0.1)]"
                style={{ backgroundColor: card.color_light }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{card.icon}</span>
                  <span className="text-sm font-bold" style={{ color: card.color }}>
                    {card.tipo}
                  </span>
                </div>
                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {card.cumplimiento != null ? `${card.cumplimiento}%` : "—"}
                </p>
                <p className="text-xs text-slate-600">
                  {card.n_indicadores} indicadores · {card.n_riesgo} en riesgo
                  {card.variacion_pp != null && (
                    <span className={card.variacion_pp >= 0 ? " text-emerald-700" : " text-red-700"}>
                      {" "}
                      · {card.variacion_pp > 0 ? "+" : ""}
                      {card.variacion_pp} pp
                    </span>
                  )}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {(catalog_charts.periodicidad.length > 0 || catalog_charts.tipo_indicador.length > 0) && (
        <div className="grid gap-6 lg:grid-cols-2">
          <CatalogList title="Periodicidad" items={catalog_charts.periodicidad} />
          <CatalogList title="Tipo de indicador" items={catalog_charts.tipo_indicador} />
        </div>
      )}
    </div>
  );
}

function InsightCard({
  emoji,
  title,
  text,
  gradient,
  borderColor,
}: {
  emoji: string;
  title: string;
  text: string;
  gradient: string;
  borderColor: string;
}) {
  return (
    <div
      className={`rounded-xl border-l-[5px] bg-gradient-to-r p-4 shadow-[0_2px_6px_rgba(0,0,0,0.06)] ${gradient}`}
      style={{ borderLeftColor: borderColor }}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">{emoji}</span>
        <div>
          <p className="text-sm font-bold text-slate-800">{title}</p>
          <p className="mt-1 text-sm text-slate-700">{text}</p>
        </div>
      </div>
    </div>
  );
}

function BannerStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-bold uppercase tracking-wider text-white/60">{label}</p>
      <p className="mt-1 text-xl font-bold">{value}</p>
    </div>
  );
}

function CatalogList({
  title,
  items,
}: {
  title: string;
  items: Array<{ label: string; count: number }>;
}) {
  const total = items.reduce((a, i) => a + i.count, 0) || 1;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)]">
      <h4 className="mb-3 text-sm font-bold text-slate-800">{title}</h4>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.label} className="flex items-center justify-between text-sm">
            <span className="text-slate-700">{item.label}</span>
            <span className="font-semibold text-poli-navy">
              {item.count} ({Math.round((item.count / total) * 100)}%)
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
