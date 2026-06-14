"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface CmiDonutNivelItem {
  nivel: string;
  cantidad: number;
  porcentaje: number;
  color: string;
}

interface CmiDonutNivelPlotlyProps {
  data: CmiDonutNivelItem[];
  total: number;
}

export function CmiDonutNivelPlotly({ data, total }: CmiDonutNivelPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        Sin distribución por nivel
      </div>
    );
  }

  const trace = {
    type: "pie" as const,
    labels: data.map((d) => d.nivel),
    values: data.map((d) => d.cantidad),
    hole: 0.5,
    textinfo: "label+percent" as const,
    textposition: "inside" as const,
    textfont: { size: 11, color: "#FFFFFF" },
    marker: {
      colors: data.map((d) => d.color),
      line: { color: "#FFFFFF", width: 2 },
    },
    hovertemplate: "<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>",
  };

  const layout: Partial<Layout> = {
    margin: { l: 10, r: 10, t: 30, b: 10 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: true,
    legend: {
      orientation: "h" as const,
      yanchor: "bottom",
      y: -0.12,
      xanchor: "center",
      x: 0.5,
      font: { size: 10 },
    },
    annotations: [
      {
        text: `<b>${total}</b><br><span style='font-size:12px'>indicadores</span>`,
        showarrow: false,
        font: { size: 22, color: "#1A3A5C" },
        align: "center" as const,
      },
    ],
  };

  return (
    <Plot
      data={[trace]}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: 320 }}
      useResizeHandler
    />
  );
}
