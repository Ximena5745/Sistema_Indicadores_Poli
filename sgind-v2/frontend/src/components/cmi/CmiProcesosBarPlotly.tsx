"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";
import type { CMIProcesoBar } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosBarPlotlyProps {
  data: CMIProcesoBar[];
  baseAnio?: number;
  maxHeight?: number;
  compact?: boolean;
  limit?: number;
}

export function CmiProcesosBarPlotly({
  data,
  baseAnio,
  maxHeight = 480,
  compact = false,
  limit,
}: CmiProcesosBarPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-slate-500">
        Sin datos por proceso
      </div>
    );
  }

  const sorted = [...data]
    .sort((a, b) => (a.cumplimiento ?? 0) - (b.cumplimiento ?? 0))
    .slice(limit ? -limit : undefined);

  const labels = sorted.map((d) => {
    const maxLen = compact ? 24 : 32;
    return d.proceso.length > maxLen ? `${d.proceso.slice(0, maxLen - 2)}…` : d.proceso;
  });

  const traces = [
    {
      type: "bar" as const,
      orientation: "h" as const,
      name: "Actual",
      y: labels,
      x: sorted.map((d) => d.cumplimiento ?? 0),
      marker: { color: sorted.map((d) => d.color ?? "#1A3A5C") },
      text: sorted.map((d) => (d.cumplimiento != null ? `${Number(d.cumplimiento).toFixed(1)}%` : "—")),
      textposition: "outside" as const,
      hovertemplate: "<b>%{y}</b><br>Actual: %{x:.1f}%<extra></extra>",
    },
  ];

  if (baseAnio && sorted.some((d) => d.cumplimiento_anterior != null)) {
    traces.push({
      type: "bar" as const,
      orientation: "h" as const,
      name: String(baseAnio),
      y: labels,
      x: sorted.map((d) => d.cumplimiento_anterior ?? 0),
      marker: { color: sorted.map(() => "#94A3B8") },
      text: sorted.map((d) =>
        d.cumplimiento_anterior != null ? `${Number(d.cumplimiento_anterior).toFixed(1)}%` : "—"
      ),
      textposition: "outside" as const,
      hovertemplate: `<b>%{y}</b><br>${baseAnio}: %{x:.1f}%<extra></extra>`,
    });
  }

  const rowH = compact ? 28 : 34;
  const computedH = Math.max(compact ? 200 : 280, sorted.length * rowH);
  const height = Math.min(computedH, maxHeight);

  const layout: Partial<Layout> = {
    barmode: "group",
    margin: { l: compact ? 130 : 160, r: 44, t: compact ? 8 : 28, b: 12 },
    height,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: { range: [0, 120], ticksuffix: "%", gridcolor: "#E2E8F0", tickfont: { size: 10 } },
    yaxis: { automargin: true, tickfont: { size: compact ? 10 : 11 } },
    legend: { orientation: "h", y: 1.08, font: { size: 10 } },
    font: { family: "inherit", size: compact ? 10 : 11 },
  };

  const chart = (
    <Plot
      data={traces}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );

  if (computedH > maxHeight) {
    return <div className="max-h-[320px] overflow-y-auto pr-1">{chart}</div>;
  }
  return chart;
}
