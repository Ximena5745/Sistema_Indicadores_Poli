const ICONS: Record<string, string> = {
  success: "✅",
  chart: "📊",
  warning: "⚠️",
  alert: "🚨",
  info: "ℹ️",
};

export interface ExecutiveNarrativeData {
  texto: string;
  estado_color: string;
  estado_icon: string;
  health_rate?: number;
}

export function ExecutiveNarrative({ data }: { data: ExecutiveNarrativeData }) {
  const texto = data?.texto ?? "";
  const estadoColor = data?.estado_color ?? "#0B5FFF";
  const estadoIcon = data?.estado_icon ?? "info";

  return (
    <div
      className="rounded-xl border bg-gradient-to-br from-white to-blue-50 p-5 shadow-sm"
      style={{ borderLeftWidth: 6, borderLeftColor: estadoColor }}
    >
      <div className="mb-2 flex items-center gap-2">
        <span className="text-xl">{ICONS[estadoIcon] ?? "📢"}</span>
        <h3 className="text-base font-extrabold text-slate-800">Narrativa Ejecutiva</h3>
      </div>
      <p
        className="text-sm leading-relaxed text-slate-700"
        dangerouslySetInnerHTML={{ __html: texto }}
      />
    </div>
  );
}
