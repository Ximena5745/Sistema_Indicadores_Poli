const ICONS: Record<string, string> = {
  rocket: "🚀",
  chart: "📈",
  medal: "🏅",
  bulb: "💡",
  leaf: "🌱",
  graduation: "🎓",
};

export interface StrategyCardData {
  linea: string;
  icon: string;
  color: string;
  count: number;
  cumplimiento: number;
  unit_label: string;
  historico: { anio: number; cumplimiento: number }[];
  n_indicadores?: number;
  n_proyectos?: number;
  n_retos?: number;
}

function formatPct(value: number | null | undefined, digits = 1): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "—";
  }
  return value.toFixed(digits);
}

function Sparkline({ data, color }: { data: StrategyCardData["historico"]; color: string }) {
  const valid = data.filter((d) => typeof d.cumplimiento === "number" && Number.isFinite(d.cumplimiento));
  if (!valid.length) {
    return <div className="h-10" />;
  }
  const width = 100;
  const height = 35;
  const pad = 4;
  const values = valid.map((d) => d.cumplimiento);
  const minV = Math.min(...values) * 0.9;
  const maxV = Math.max(...values) * 1.1 || minV + 20;
  const range = maxV - minV || 1;
  const yRange = height - 2 * pad;
  const points = values.map((v, i) => {
    const x = valid.length === 1 ? width / 2 : (i / (valid.length - 1)) * width;
    const y = pad + yRange - ((v - minV) / range) * yRange;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const path = `M${points.join(" L")}`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="mx-auto block overflow-hidden">
      <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="#ddd" strokeWidth="1" strokeDasharray="3" />
      <path d={path} fill="none" stroke={color} strokeWidth="2" />
      {points.map((p, i) => {
        const [cx, cy] = p.split(",");
        return <circle key={i} cx={cx} cy={cy} r="3" fill={color} />;
      })}
      <title>{valid.map((d) => `${d.anio}:${formatPct(d.cumplimiento, 0)}%`).join(" - ")}</title>
    </svg>
  );
}

interface StrategyCardProps {
  card: StrategyCardData;
}

export function StrategyCard({ card }: StrategyCardProps) {
  const hasDesglose =
    card.n_indicadores !== undefined &&
    card.n_proyectos !== undefined &&
    card.n_retos !== undefined;

  return (
    <div
      className="overflow-hidden rounded-xl border-l-4 bg-white p-3 shadow-sm"
      style={{ borderLeftColor: card.color, background: `linear-gradient(140deg,#fff,${card.color}1E)` }}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-2xl">{ICONS[card.icon] ?? "📊"}</span>
        <div className="text-right">
          <div className="text-xl font-bold" style={{ color: card.color }}>
            {formatPct(card.cumplimiento)}%
          </div>
          {hasDesglose ? (
            <div className="mt-1 space-y-0.5 text-[11px] leading-snug text-slate-600">
              <div>
                <span className="font-semibold text-slate-700">{card.n_indicadores}</span> indicadores
              </div>
              <div>
                <span className="font-semibold text-slate-700">{card.n_proyectos}</span> proyectos
              </div>
              <div>
                <span className="font-semibold text-slate-700">{card.n_retos}</span> retos
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500">
              {card.count} {card.unit_label}
            </div>
          )}
        </div>
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-700">{card.linea}</div>
      <div className="mt-2 h-10 overflow-hidden">
        <Sparkline data={card.historico} color={card.color} />
      </div>
    </div>
  );
}

export function StrategyCardGrid({ cards }: { cards: StrategyCardData[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      {cards.map((card) => (
        <StrategyCard key={card.linea} card={card} />
      ))}
    </div>
  );
}
