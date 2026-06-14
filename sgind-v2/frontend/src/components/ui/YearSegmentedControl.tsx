interface YearSegmentedControlProps {
  years: number[];
  anio: number;
  onChange: (anio: number) => void;
}

export function YearSegmentedControl({ years, anio, onChange }: YearSegmentedControlProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {years.map((y) => (
        <button
          key={y}
          type="button"
          onClick={() => onChange(y)}
          className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
            anio === y
              ? "bg-poli-navy text-white shadow-sm"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          {y}
        </button>
      ))}
    </div>
  );
}
