"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KPICard } from "@/components/ui/KPICard";
import { createOM, fetchOMMatriz } from "@/lib/api";
import { useAuthReady, useAuthStore } from "@/stores/auth-store";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const TIPOS_ACCION = ["OM Kawak", "Reto Plan Anual", "Proyecto Institucional", "Otro"];

export default function GestionOMPage() {
  const { isAuthenticated } = useAuthReady();
  const role = useAuthStore((s) => s.role);
  const canEdit = role === "calidad" || role === "desempeno";
  const queryClient = useQueryClient();

  const [anio, setAnio] = useState(2025);
  const [mes, setMes] = useState("Diciembre");
  const [proceso, setProceso] = useState("Todos");
  const [subproceso, setSubproceso] = useState("Todos");
  const [mostrarAlerta, setMostrarAlerta] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tipoAccion, setTipoAccion] = useState("OM Kawak");
  const [numeroOm, setNumeroOm] = useState("");

  const query = useQuery({
    queryKey: ["om-matriz", anio, mes, proceso, subproceso, mostrarAlerta],
    queryFn: () =>
      fetchOMMatriz({
        anio,
        mes,
        ...(proceso !== "Todos" ? { proceso } : {}),
        ...(subproceso !== "Todos" ? { subproceso } : {}),
        mostrar_alerta: mostrarAlerta,
      }),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (query.data?.filtros) {
      const defAnio = Number(query.data.filtros.anio_default) || 2025;
      if (!Number.isNaN(defAnio)) setAnio(defAnio);
      setMes(query.data.filtros.mes_default ?? "Diciembre");
    }
  }, [query.data?.filtros]);

  const createMutation = useMutation({
    mutationFn: createOM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["om-matriz"] });
      setFormOpen(false);
      setNumeroOm("");
    },
  });

  const data = query.data;
  const selectedRow = data?.filas.find((f) => f.id === selectedId);

  const handleSubmit = () => {
    if (!selectedRow) return;
    createMutation.mutate({
      id_indicador: selectedRow.id,
      nombre_indicador: selectedRow.indicador,
      proceso: selectedRow.proceso,
      periodo: mes,
      anio,
      tiene_om: 1,
      tipo_accion: tipoAccion,
      numero_om: numeroOm || undefined,
      comentario: numeroOm || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Gestión OM</h2>
        <p className="mt-1 text-slate-600">
          Indicadores en Peligro/Alerta con registro de oportunidades de mejora. Fuente: Consolidado Histórico.
        </p>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver la matriz OM.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : data?.error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{data.error}</div>
      ) : (
        <>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="mb-1 text-xs text-slate-500">Año</p>
                <div className="flex flex-wrap gap-1">
                  {(data?.filtros.anios ?? ["2025"]).map((y) => (
                    <button
                      key={y}
                      type="button"
                      onClick={() => setAnio(Number(y))}
                      className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
                        String(anio) === String(y) ? "bg-poli-navy text-white" : "bg-slate-100"
                      }`}
                    >
                      {y}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs text-slate-500">Mes</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={mes}
                  onChange={(e) => setMes(e.target.value)}
                >
                  {MESES.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <p className="mb-1 text-xs text-slate-500">Proceso</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={proceso}
                  onChange={(e) => setProceso(e.target.value)}
                >
                  <option value="Todos">Todos</option>
                  {(data?.filtros.procesos ?? []).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <p className="mb-1 text-xs text-slate-500">Subproceso</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={subproceso}
                  onChange={(e) => setSubproceso(e.target.value)}
                >
                  <option value="Todos">Todos</option>
                  {(data?.filtros.subprocesos ?? []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <label className="mt-3 flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={mostrarAlerta}
                onChange={(e) => setMostrarAlerta(e.target.checked)}
              />
              Mostrar también indicadores en Alerta
            </label>
          </div>

          <h3 className="text-lg font-semibold text-slate-800">
            📊 Indicadores en Riesgo — {mes} {anio}
          </h3>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard label="🔴 Peligro" value={data?.kpis.peligro ?? 0} />
            <KPICard label="🟡 Alerta" value={data?.kpis.alerta ?? 0} />
            <KPICard label="📋 Con OM" value={`${data?.kpis.con_om ?? 0} / ${data?.kpis.total ?? 0}`} />
            <KPICard
              label="📊 Avance OM"
              value={
                data?.kpis.avance_om_promedio != null ? `${data.kpis.avance_om_promedio}%` : "—"
              }
            />
          </div>

          {canEdit && (
            <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="min-w-[200px] flex-1">
                <p className="mb-1 text-xs text-slate-500">Indicador</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={selectedId ?? ""}
                  onChange={(e) => {
                    setSelectedId(e.target.value || null);
                    setFormOpen(!!e.target.value);
                  }}
                >
                  <option value="">Seleccionar indicador…</option>
                  {(data?.filas ?? []).map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.id} — {f.indicador.slice(0, 60)}
                    </option>
                  ))}
                </select>
              </div>
              {formOpen && selectedRow ? (
                <>
                  <div>
                    <p className="mb-1 text-xs text-slate-500">Tipo de acción</p>
                    <select
                      className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={tipoAccion}
                      onChange={(e) => setTipoAccion(e.target.value)}
                    >
                      {TIPOS_ACCION.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <p className="mb-1 text-xs text-slate-500">Nº OM / Identificador</p>
                    <input
                      className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={numeroOm}
                      onChange={(e) => setNumeroOm(e.target.value)}
                      placeholder="Identificador OM"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={createMutation.isPending}
                    className="rounded-lg bg-poli-navy px-4 py-2 text-sm font-semibold text-white hover:bg-poli-navy/90 disabled:opacity-50"
                  >
                    {createMutation.isPending ? "Guardando…" : "Asociar nueva OM"}
                  </button>
                </>
              ) : null}
            </div>
          )}

          {!data?.filas.length ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
              No hay indicadores en Peligro con los filtros seleccionados.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-800 text-xs uppercase text-white">
                  <tr>
                    {[
                      "Id",
                      "Indicador",
                      "Subproceso",
                      "Periodicidad",
                      "Meta",
                      "Ejecución",
                      "Cumplimiento",
                      "Categoría",
                      "Tipo de Acción",
                      "OM",
                      "Avance OM",
                    ].map((h) => (
                      <th key={h} className="whitespace-nowrap px-3 py-2">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.filas.map((row) => (
                    <tr key={row.id} style={{ backgroundColor: row.row_bg }}>
                      <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                      <td className="max-w-[200px] truncate px-3 py-2" title={row.indicador}>
                        {row.indicador}
                      </td>
                      <td className="px-3 py-2">{row.subproceso}</td>
                      <td className="px-3 py-2">{row.periodicidad}</td>
                      <td className="px-3 py-2 text-right">{row.meta != null ? String(row.meta) : "—"}</td>
                      <td className="px-3 py-2 text-right">{row.ejecucion != null ? String(row.ejecucion) : "—"}</td>
                      <td className="px-3 py-2 text-right">
                        {row.cumplimiento_pct != null ? `${row.cumplimiento_pct}%` : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className="rounded px-1.5 py-0.5 text-xs font-medium text-white"
                          style={{ backgroundColor: row.categoria_color }}
                        >
                          {row.categoria}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
                          style={{ backgroundColor: row.tipo_accion_color }}
                        >
                          {row.tipo_accion}
                        </span>
                      </td>
                      <td className="px-3 py-2">{row.numero_om || "—"}</td>
                      <td className="px-3 py-2">
                        {row.avance_om != null ? (
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-16 overflow-hidden rounded-full bg-slate-200">
                              <div
                                className="h-full rounded-full bg-emerald-500"
                                style={{ width: `${Math.min(100, row.avance_om)}%` }}
                              />
                            </div>
                            <span className="text-xs">{row.avance_om}%</span>
                          </div>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
