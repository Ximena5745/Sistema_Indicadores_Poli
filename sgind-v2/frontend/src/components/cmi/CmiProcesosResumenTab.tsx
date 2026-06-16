"use client";

import type { CMIProcesosVistaGlobal } from "@/lib/types";
import { CmiCatalogChartsPlotly } from "@/components/cmi/CmiCatalogChartsPlotly";
import { CmiDonutNivelPlotly } from "@/components/cmi/CmiDonutNivelPlotly";
import { CmiMetricCard } from "@/components/cmi/CmiMetricCard";
import { CmiProcesosBarPlotly } from "@/components/cmi/CmiProcesosBarPlotly";
import { fmtNum, fmtPct } from "@/components/cmi/nivelUtils";

const RESUMEN_BAR_LIMIT = 12;

interface CmiProcesosResumenTabProps {
  vista: CMIProcesosVistaGlobal;
  baseAnio: number;
}

export function CmiProcesosResumenTab({ vista, baseAnio }: CmiProcesosResumenTabProps) {
  const { kpis, banner, distribucion_nivel, proceso_bars, catalog_charts, variacion } = vista;

  const conteo = kpis.conteo_estados ?? {};
  const nAlerta = conteo["Alerta"] ?? 0;
  const nPeligro = conteo["Peligro"] ?? 0;

  const barSlice = [...proceso_bars]
    .sort((a, b) => (b.cumplimiento ?? 0) - (a.cumplimiento ?? 0))
    .slice(0, RESUMEN_BAR_LIMIT);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-br from-[#173a63] to-[#2d5a8a] p-5 text-white shadow-lg sm:p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/60">CMI por Procesos</p>
            <h3 className="text-xl font-bold sm:text-2xl">
              {banner.anio} · {banner.mes}
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <Chip label="Subprocesos = 1" />
            <Chip label="Validado Kawak" />
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <BannerStat label="Cumplimiento global" value={fmtPct(banner.cumplimiento_global)} large />
          <BannerStat
            label={`vs ${banner.base_anio}`}
            value={
              banner.variacion_pp != null
                ? `${banner.variacion_pp > 0 ? "+" : ""}${fmtNum(banner.variacion_pp)} pp`
                : "—"
            }
          />
          <BannerStat label="Indicadores" value={String(banner.total_indicadores)} />
          <BannerStat label="En riesgo" value={String(banner.en_riesgo)} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <CmiMetricCard
          title="Cumplimiento promedio"
          value={fmtPct(kpis.promedio)}
          subtitle={`Corte ${vista.mes_nombre}`}
          icon="📈"
          color="#43A047"
        />
        <CmiMetricCard
          title="En alerta"
          value={String(nAlerta)}
          subtitle="80% – 99%"
          icon="⚠️"
          color="#FBAF17"
        />
        <CmiMetricCard
          title="En peligro"
          value={String(nPeligro)}
          subtitle="Menor a 80%"
          icon="🚨"
          color="#D32F2F"
        />
        <CmiMetricCard
          title="Procesos activos"
          value={String(kpis.n_procesos)}
          subtitle={`${kpis.n_subprocesos} subprocesos · ${kpis.n_unidades} unidades`}
          icon="🏢"
          color="#1A3A5C"
        />
      </div>

      <CmiCatalogChartsPlotly
        periodicidad={catalog_charts.periodicidad}
        tipoIndicador={catalog_charts.tipo_indicador}
      />

      <div className="grid gap-5 lg:grid-cols-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:col-span-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h4 className="text-sm font-bold text-slate-800">
              Top procesos por cumplimiento {baseAnio ? `(vs ${baseAnio})` : ""}
            </h4>
            {proceso_bars.length > RESUMEN_BAR_LIMIT && (
              <span className="text-[10px] text-slate-500">
                Mostrando {RESUMEN_BAR_LIMIT} de {proceso_bars.length} · ver todos en Procesos
              </span>
            )}
          </div>
          <CmiProcesosBarPlotly data={barSlice} baseAnio={baseAnio} maxHeight={300} compact />
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:col-span-2">
          <h4 className="mb-3 text-sm font-bold text-slate-800">Distribución por nivel</h4>
          <CmiDonutNivelPlotly data={distribucion_nivel} total={kpis.total} />
        </div>
      </div>

      {(variacion.mejoraron.length > 0 || variacion.empeoraron.length > 0) && (
        <div className="grid gap-4 lg:grid-cols-2">
          <VarTable title="Mayor mejora" rows={variacion.mejoraron} positive />
          <VarTable title="Mayor riesgo" rows={variacion.empeoraron} positive={false} />
        </div>
      )}
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-white/15 px-2.5 py-1 text-[10px] font-semibold text-white/90">
      {label}
    </span>
  );
}

function BannerStat({
  label,
  value,
  large,
}: {
  label: string;
  value: string;
  large?: boolean;
}) {
  return (
    <div className="rounded-xl bg-white/10 px-3 py-2.5">
      <p className="text-[10px] font-bold uppercase tracking-wider text-white/55">{label}</p>
      <p className={`mt-0.5 font-bold ${large ? "text-2xl" : "text-lg"}`}>{value}</p>
    </div>
  );
}

function VarTable({
  title,
  rows,
  positive,
}: {
  title: string;
  rows: Array<{ indicador: string; variacion: number }>;
  positive: boolean;
}) {
  if (!rows.length) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-600">{title}</h4>
      <ul className="space-y-1.5">
        {rows.slice(0, 5).map((r) => (
          <li key={r.indicador} className="flex items-center justify-between gap-2 text-sm">
            <span className="truncate text-slate-700">{r.indicador}</span>
            <span className={`shrink-0 font-bold ${positive ? "text-emerald-700" : "text-red-700"}`}>
              {r.variacion > 0 ? "+" : ""}
              {fmtNum(r.variacion)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
