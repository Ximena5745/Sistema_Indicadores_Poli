"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";
import type { CMIProcesoBar } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosBarPlotlyProps {
  data: CMIProcesoBar[];
  baseAnio?: number;
}

export function CmiProcesosBarPlotly({ data, baseAnio }: CmiProcesosBarPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        Sin datos por proceso
      </div>
    );
  }

  const sorted = [...data].sort((a, b) => (a.cumplimiento ?? 0) - (b.cumplimiento ?? 0));
  const labels = sorted.map((d) =>
    d.proceso.length > 32 ? `${d.proceso.slice(0, 30)}…` : d.proceso
  );

  const traces = [
    {
      type: "bar" as const,
      orientation: "h" as const,
      name: "Actual",
      y: labels,
      x: sorted.map((d) => d.cumplimiento ?? 0),
      marker: { color: "#1A3A5C" },
      text: sorted.map((d) => (d.cumplimiento != null ? `${d.cumplimiento.toFixed(1)}%` : "—")),
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
      marker: { color: "#94A3B8" },
      text: sorted.map((d) =>
        d.cumplimiento_anterior != null ? `${d.cumplimiento_anterior.toFixed(1)}%` : "—"
      ),
      textposition: "outside" as const,
      hovertemplate: `<b>%{y}</b><br>${baseAnio}: %{x:.1f}%<extra></extra>`,
    });
  }

  const layout: Partial<Layout> = {
    barmode: "group",
    margin: { l: 160, r: 48, t: 32, b: 20 },
    height: Math.max(280, sorted.length * 36),
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: { range: [0, 120], ticksuffix: "%", gridcolor: "#E2E8F0" },
    yaxis: { automargin: true },
    legend: { orientation: "h", y: 1.12 },
    font: { family: "inherit", size: 11 },
  };

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
