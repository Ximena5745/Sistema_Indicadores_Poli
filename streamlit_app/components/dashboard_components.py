"""
streamlit_app/components/dashboard_components.py
CMI por Procesos — Componentes reutilizables para el dashboard ejecutivo.

Provee funciones de renderizado para:
- KPIs ejecutivos (resumen rápido de cumplimiento)
- Alertas y hallazgos de indicadores críticos
- Tabla analítica filtrable con semaforización
- Fichas detalladas con tendencias (↑ ↓ →)
- Análisis por unidad organizacional
- Análisis histórico por indicador

REGLAS (PROJECT_RULES.md):
- Semaforización SOLO desde NIVELES_COLORS centralizado (§3.3)
- NO duplicar lógica existente en resumen_por_proceso.py (§2.1)
- Funciones reutilizables, sin hardcodes de negocio (§2.3)
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import hashlib
import unicodedata
from streamlit_app.utils.formatting import formatear_meta_ejecucion_df
from streamlit_app.components.cmi_tabs.modal_ficha import render_modal_ficha

# Contador por módulo para generar claves únicas por llamada durante un rerun
_PLOT_KEY_COUNTER = 0

# ── Semaforización centralizada (PROJECT_RULES §3.3) ─────────────────────────
# Única fuente: mismos valores que NIVELES_COLORS en resumen_por_proceso.py
NIVELES_COLORS = {
    "sobrecumplimiento": "#6699FF",
    "cumplimiento": "#2E7D32",
    "alerta": "#F9A825",
    "peligro": "#C62828",
    "sin dato": "#6E7781",
}

NIVEL_BG = {
    "sobrecumplimiento": "#EEF2FF",
    "cumplimiento": "#E8F5E9",
    "alerta": "#FFFDE7",
    "peligro": "#FFEBEE",
    "sin dato": "#F5F5F5",
}

MESES_OPCIONES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


# ── Helpers internos ──────────────────────────────────────────────────────────

def _resolve_pct_col(df: pd.DataFrame) -> str | None:
    """Resuelve el nombre de la columna de cumplimiento disponible en el DataFrame."""
    for col in ("cumplimiento_pct", "Cumplimiento_pct", "Cumplimiento_norm"):
        if col in df.columns:
            return col
    return None


def _norm_text(value: str) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_norm = {_norm_text(c): c for c in df.columns}
    for cand in candidates:
        key = _norm_text(cand)
        if key in cols_norm:
            return cols_norm[key]
    for cand in candidates:
        key = _norm_text(cand)
        for norm_col, real_col in cols_norm.items():
            if key in norm_col:
                return real_col
    return None


def _nivel_from_pct(val: float | None) -> str:
    """Clasifica nivel de cumplimiento. Fuente única (PROJECT_RULES §3.3)."""
    try:
        v = float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "sin dato"
    if v >= 105:
        return "sobrecumplimiento"
    if v >= 100:
        return "cumplimiento"
    if v >= 80:
        return "alerta"
    return "peligro"


def _detect_trend(values: list) -> str:
    """Detecta tendencia de los últimos 3+ valores. Retorna: ↑ ↓ →"""
    vals = [v for v in values if v is not None and pd.notna(v)]
    if len(vals) < 2:
        return "→"
    last3 = vals[-3:]
    diff = float(last3[-1]) - float(last3[0])
    if diff > 2:
        return "↑"
    if diff < -2:
        return "↓"
    return "→"


def _normalize_pct(series: pd.Series, pct_col: str) -> pd.Series:
    """Normaliza a porcentaje (multiplica por 100 si es Cumplimiento_norm decimal)."""
    vals = pd.to_numeric(series, errors="coerce")
    if pct_col == "Cumplimiento_norm":
        vals = vals * 100
    return vals


def _is_cmi_procesos(df: pd.DataFrame) -> bool:
    """Detecta si el DataFrame corresponde a CMI por Procesos según columnas de subproceso.

    Esta detección se basa en la presencia de subprocesos; no debe depender del
    campo `Ind act`, que está deprecado para la vista de CMI por Procesos.
    """
    for col in ("Subproceso", "Subproceso_final", "Subprocesos", "Subproceso_norm"):
        if col in df.columns:
            return True
    return False


def _build_sort_key(df: pd.DataFrame) -> pd.Series:
    """Construye una llave numérica para ordenar registros por fecha/periodo.

    Prioriza columnas: 'Anio'/'Año' + 'Mes_num' o 'Mes' (convertido), o 'Fecha'.
    Retorna una Serie de enteros que representa año*100 + mes, o incremento si no hay fecha.
    """
    # Año
    year_col = None
    for c in ("Anio", "Año", "Anio_num", "Year"):
        if c in df.columns:
            year_col = c
            break
    # Mes num
    mes_col = None
    for c in ("Mes_num", "Mes", "Periodo"):
        if c in df.columns:
            mes_col = c
            break
    # Fecha
    fecha_col = "Fecha" if "Fecha" in df.columns else None

    if fecha_col:
        try:
            fecha = pd.to_datetime(df[fecha_col], errors="coerce")
            key = fecha.dt.year.fillna(0).astype(int) * 100 + fecha.dt.month.fillna(0).astype(int)
            return key.fillna(0).astype(int)
        except Exception:
            pass

    if year_col:
        years = pd.to_numeric(df[year_col], errors="coerce").fillna(0).astype(int)
        if mes_col:
            # intentar convertir Mes a número si es texto
            mes_vals = df[mes_col]
            mes_num = pd.to_numeric(mes_vals, errors="coerce")
            if mes_num.isna().all():
                # mapear nombres de meses
                mes_map = {m.upper(): i + 1 for i, m in enumerate(MESES_OPCIONES)}
                mes_num = mes_vals.astype(str).str.strip().str.upper().map(mes_map).fillna(0).astype(int)
            else:
                mes_num = mes_num.fillna(0).astype(int)
            key = years * 100 + mes_num
            return key.fillna(0).astype(int)
        else:
            return years * 100

    # fallback: usar índice para orden estable
    return pd.Series(range(len(df)), index=df.index)


# ── Componentes públicos ───────────────────────────────────────────────────────

def render_executive_kpis(df: pd.DataFrame, pct_col: str | None = None) -> None:
    """Fila de 4 KPIs ejecutivos: en meta, en alerta, críticos, cumplimiento global."""
    if df.empty:
        return
    pct_col = pct_col or _resolve_pct_col(df)
    if pct_col is None or pct_col not in df.columns:
        return

    vals = _normalize_pct(df[pct_col], pct_col)

    # Si existe columna Id, contar indicadores únicos: tomar el último valor válido
    # por Id y calcular métricas sobre esa serie para evitar duplicados por periodos.
    if "Id" in df.columns:
        df_ids = df[["Id", pct_col]].copy()
        df_ids["Id_norm"] = df_ids["Id"].astype(str).str.strip()
        df_ids[pct_col] = _normalize_pct(df_ids[pct_col], pct_col)
        # ordenar por fecha/periodo antes de tomar el último registro por Id
        sort_key = _build_sort_key(df)
        # alinear índice
        df_ids = df_ids.reindex(sort_key.index)
        df_ids["_sort_key"] = sort_key
        df_ids = df_ids.sort_values("_sort_key")
        per_id = df_ids.groupby("Id_norm", dropna=False)[pct_col].agg(
            lambda x: x.dropna().iloc[-1] if x.dropna().any() else pd.NA
        )
        vals = per_id
    else:
        vals = vals

    total = max(len(vals.dropna()), 1)
    en_meta = int((vals >= 100).sum())
    en_alerta = int(((vals >= 80) & (vals < 100)).sum())
    en_peligro = int((vals < 80).sum())
    prom = float(vals.mean()) if not vals.dropna().empty else 0.0

    pct_meta = round(en_meta / total * 100, 1)
    pct_alerta = round(en_alerta / total * 100, 1)
    pct_peligro = round(en_peligro / total * 100, 1)
    color_global = "#2E7D32" if prom >= 100 else ("#F9A825" if prom >= 80 else "#C62828")

    st.markdown(
        f"""
        <div class="cmi-kpi-bar">
            <div class="cmi-kpi-card cmi-kpi-success">
                <div class="cmi-kpi-label">✅ En meta</div>
                <div class="cmi-kpi-value">{en_meta}</div>
                <div class="cmi-kpi-sub">{pct_meta}% del total</div>
            </div>
            <div class="cmi-kpi-card cmi-kpi-warning">
                <div class="cmi-kpi-label">⚠️ En alerta</div>
                <div class="cmi-kpi-value">{en_alerta}</div>
                <div class="cmi-kpi-sub">{pct_alerta}% del total</div>
            </div>
            <div class="cmi-kpi-card cmi-kpi-danger">
                <div class="cmi-kpi-label">🔴 Críticos</div>
                <div class="cmi-kpi-value">{en_peligro}</div>
                <div class="cmi-kpi-sub">{pct_peligro}% del total</div>
            </div>
            <div class="cmi-kpi-card" style="border-top:4px solid {color_global};">
                <div class="cmi-kpi-label">📊 Cumplimiento Global</div>
                <div class="cmi-kpi-value" style="color:{color_global};">{prom:.1f}%</div>
                <div class="cmi-kpi-sub">{total} indicadores activos</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alertas_criticas(
    df: pd.DataFrame,
    pct_col: str | None = None,
    max_alerts: int = 6,
) -> None:
    """Tarjetas de alerta para indicadores en estado Peligro (cumplimiento < 80%)."""
    if df.empty:
        return
    pct_col = pct_col or _resolve_pct_col(df)
    if pct_col is None or pct_col not in df.columns:
        st.info("No hay columna de cumplimiento disponible para calcular alertas.")
        return

    vals = _normalize_pct(df[pct_col], pct_col)
    df_work = df.copy()
    df_work["_pct_num"] = vals
    criticos = df_work[df_work["_pct_num"] < 80].copy()

    if criticos.empty:
        st.success("🎉 No hay indicadores en estado crítico para este corte.")
        return

    if "Id" in criticos.columns:
        criticos["Id_norm"] = criticos["Id"].astype(str).str.strip()
        sort_key = _build_sort_key(criticos)
        criticos = criticos.reindex(sort_key.index)
        criticos["_sort_key"] = sort_key
        criticos = (
            criticos.sort_values("_sort_key")
            .drop_duplicates(subset=["Id_norm"], keep="last")
            .sort_values("_pct_num", ascending=True)
        )
    else:
        criticos = criticos.sort_values("_pct_num", ascending=True)
    total_criticos = len(criticos)

    st.markdown(
        f"""<div class="cmi-alert-header">
            🚨 <strong>{total_criticos} indicador(es) en estado crítico</strong>
            — cumplimiento &lt; 80%
        </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, (_, row) in enumerate(criticos.head(max_alerts).iterrows()):
        nombre = str(row.get("Indicador", "Sin nombre"))
        proceso = str(
            row.get("Proceso", row.get("Proceso_padre", row.get("Subproceso_final", "—")))
        )
        tipo = str(row.get("Tipo de proceso", "—"))
        pct_val = float(row["_pct_num"]) if pd.notna(row["_pct_num"]) else 0.0
        desviacion = round(100 - pct_val, 1)

        if pct_val < 50:
            analisis = "Desempeño crítico. Requiere intervención inmediata."
        elif pct_val < 70:
            analisis = "Desempeño bajo. Revisar causas y activar plan de mejora."
        else:
            analisis = "Indicador en zona de alerta. Monitorear para evitar deterioro."

        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="cmi-alert-card">
                    <div class="cmi-alert-title">{nombre}</div>
                    <div class="cmi-alert-meta">📁 {proceso} &nbsp;·&nbsp; {tipo}</div>
                    <div class="cmi-alert-pct">
                        <span class="cmi-badge-danger">{pct_val:.1f}%</span>
                        <span class="cmi-alert-gap">Brecha: -{desviacion:.1f} pp</span>
                    </div>
                    <div class="cmi-alert-analysis">{analisis}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if total_criticos > max_alerts:
        st.caption(
            f"Mostrando {max_alerts} de {total_criticos} críticos. "
            "Usa la Tabla Analítica para ver todos."
        )


def render_tabla_analitica(df: pd.DataFrame, pct_col: str | None = None) -> None:
    """Tabla analítica filtrable con columna de Estado y exportación CSV."""
    if df.empty:
        st.info("No hay datos disponibles para la tabla.")
        return

    pct_col = pct_col or _resolve_pct_col(df)

    # ── Filtros dinámicos ─────────────────────────────────────────────────────
    filtro_defs: dict[str, str] = {}
    if "Tipo de proceso" in df.columns:
        filtro_defs["Tipo de proceso"] = "Tipo de proceso"
    proc_col = next((c for c in ("Proceso", "Proceso_padre") if c in df.columns), None)
    if proc_col:
        filtro_defs["Proceso"] = proc_col
    filtered = df.copy()
    if filtro_defs:
        fcols = st.columns(min(len(filtro_defs), 3))
        for idx, (label, col_actual) in enumerate(filtro_defs.items()):
            opts = ["Todos"] + sorted(filtered[col_actual].dropna().astype(str).unique().tolist())
            with fcols[idx % len(fcols)]:
                sel = st.selectbox(
                    f"Filtrar por {label}",
                    options=opts,
                    index=0,
                    key=f"cmi_tabla_filter_{label}",
                )
                if sel != "Todos":
                    filtered = filtered[filtered[col_actual].astype(str) == sel]

    # ── Construir tabla de visualización ─────────────────────────────────────
    col_priority = [
        ("Indicador", "Indicador"),
        ("Proceso_padre", "Proceso"),
        ("Proceso", "Proceso"),
        ("Tipo de proceso", "Tipo"),
        ("Meta", "Meta"),
        ("Ejecucion", "Ejecución"),
        ("Mes", "Mes"),
    ]
    seen_dest: set[str] = set()
    rename_map: dict[str, str] = {}
    for src, dest in col_priority:
        if src in filtered.columns and dest not in seen_dest:
            rename_map[src] = dest
            seen_dest.add(dest)

    tabla = filtered[list(rename_map.keys())].rename(columns=rename_map).copy()
    meta_col = _first_col(filtered, ["Meta", "Meta último periodo", "Meta ultimo periodo"]) or "Meta"
    ejec_col = _first_col(filtered, ["Ejecución", "Ejecucion"]) or "Ejecucion"
    sign_cols = [
        c for c in [
            "Meta_Signo",
            "Meta s",
            "MetaS",
            "Decimales_Meta",
            "Decimales",
            "DecimalesEje",
            "DecEjec",
            "Ejecucion_Signo",
            "Ejecución s",
            "Ejecucion s",
            "EjecS",
        ]
        if c in filtered.columns
    ]
    if sign_cols:
        tabla = pd.concat([tabla, filtered[sign_cols].reset_index(drop=True)], axis=1)
    tabla = formatear_meta_ejecucion_df(
        tabla,
        meta_col=meta_col,
        ejec_col=ejec_col,
    )
    cleanup_cols = [
        "Meta_Signo",
        "Meta s",
        "MetaS",
        "Decimales_Meta",
        "Decimales",
        "DecimalesEje",
        "DecEjec",
        "Ejecucion_Signo",
        "Ejecución s",
        "Ejecucion s",
        "EjecS",
    ]
    tabla = tabla.drop(columns=[c for c in cleanup_cols if c in tabla.columns])

    if pct_col and pct_col in filtered.columns:
        vals = _normalize_pct(filtered[pct_col], pct_col)
        tabla["Cumplimiento %"] = vals.round(1)
        tabla["Estado"] = vals.apply(
            lambda v: "🟢 Meta"
            if v >= 100
            else ("🟡 Alerta" if v >= 80 else ("🔴 Crítico" if pd.notna(v) else "⬜ Sin dato"))
        )

    if "Indicador" in tabla.columns:
        tabla["Ver ficha"] = "Ver ficha"

    sel_indicador, ver_button = st.columns([3, 1])
    selected = ""
    if "Indicador" in filtered.columns:
        with sel_indicador:
            selected = st.selectbox(
                "Seleccionar indicador para ver ficha",
                [""] + filtered["Indicador"].astype(str).fillna(" ").tolist(),
                key="tabla_analitica_sel_indicador",
            )
        with ver_button:
            if selected and st.button("Ver ficha", key="tabla_analitica_button"):
                row = filtered[filtered["Indicador"].astype(str) == selected].head(1)
                if not row.empty:
                    render_modal_ficha(row.iloc[0])

    st.dataframe(tabla, use_container_width=True, hide_index=True)

    csv = tabla.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name="cmi_por_procesos_analisis.csv",
        mime="text/csv",
        key="cmi_download_tabla",
    )


def render_fichas_indicadores(
    df: pd.DataFrame,
    pct_col: str | None = None,
    max_fichas: int = 20,
) -> None:
    """Fichas de indicadores por tarjeta con resumen de meta, ejecución y cumplimiento."""
    if df.empty:
        st.info("No hay indicadores para mostrar en este corte.")
        return

    pct_col = pct_col or _resolve_pct_col(df)
    df_work = df.copy()

    if pct_col and pct_col in df_work.columns:
        df_work["_pct_num"] = _normalize_pct(df_work[pct_col], pct_col)
    else:
        df_work["_pct_num"] = pd.NA

    # Para CMI por Procesos, mostrar fichas por Id único (último registro por Id)
    if _is_cmi_procesos(df_work) and "Id" in df_work.columns:
        df_work["Id_norm"] = df_work["Id"].astype(str).str.strip()
        sort_key = _build_sort_key(df_work)
        df_work = df_work.reindex(sort_key.index)
        df_work["_sort_key"] = sort_key
        agg_map = {
            "Indicador": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Proceso": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Proceso_padre": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Tipo de proceso": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Unidad": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Meta": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Ejecucion": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "_pct_num": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Frecuencia": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
            "Subproceso_final": lambda s: s.dropna().iloc[-1] if not s.dropna().empty else pd.NA,
        }
        agg_map = {col: fn for col, fn in agg_map.items() if col in df_work.columns}
        df_group = (
            df_work.sort_values("_sort_key")
            .groupby("Id_norm", dropna=False)
            .agg(agg_map)
            .reset_index()
        )
        df_iter = df_group.sort_values("_pct_num", na_position="last")
        total_count = len(df_group)
    else:
        df_iter = df_work.sort_values("_pct_num", na_position="last")
        total_count = len(df_work)

    st.markdown(
        """
        <style>
        .cmi-ficha-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        @media (max-width: 900px) {
            .cmi-ficha-grid { grid-template-columns: 1fr; }
        }
        .cmi-ficha-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(59, 130, 246, 0.18);
            border-radius: 22px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .cmi-ficha-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 22px 45px rgba(15, 23, 42, 0.14);
        }
        .cmi-ficha-card-header {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 20px 22px 14px;
            align-items: flex-start;
            background: linear-gradient(135deg, rgba(216, 180, 254, 0.22), rgba(56, 189, 248, 0.15));
        }
        .cmi-ficha-card-title {
            font-size: 1.02rem;
            font-weight: 900;
            line-height: 1.2;
            color: #0F172A;
            margin: 0 0 6px 0;
        }
        .cmi-ficha-card-id {
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
            color: #1D4ED8;
            text-transform: uppercase;
        }
        .cmi-ficha-card-subtitle {
            font-size: 0.79rem;
            line-height: 1.5;
            color: #334155;
        }
        .cmi-ficha-status {
            padding: 7px 14px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            background: rgba(14, 165, 233, 0.18);
            color: #0E7490;
            white-space: nowrap;
        }
        .cmi-ficha-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            padding: 0 22px 18px;
        }
        .cmi-ficha-stat {
            background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
            border-radius: 16px;
            border: 1px solid rgba(59, 130, 246, 0.16);
            padding: 16px 14px;
        }
        .cmi-ficha-stat-label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #64748B;
            margin-bottom: 6px;
        }
        .cmi-ficha-stat-value {
            font-size: 1.35rem;
            font-weight: 800;
            color: #102A43;
            line-height: 1.1;
        }
        .cmi-ficha-footer {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            padding: 0 20px 18px;
        }
        .cmi-ficha-footer-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
            font-size: 0.76rem;
            color: #475569;
        }
        .cmi-ficha-footer-label {
            font-weight: 700;
            color: #334155;
        }
        .cmi-ficha-footer-value {
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    card_rows: list[tuple[str, pd.Series]] = []
    shown = 0
    for _, row in df_iter.iterrows():
        if shown >= max_fichas:
            break

        nombre = str(row.get("Indicador", f"Indicador {shown + 1}"))
        row_id = str(row.get("Id_norm", row.get("Id", ""))).strip() or "—"
        pct_raw = row.get("_pct_num", None)
        pct_val_f: float | None = float(pct_raw) if pd.notna(pct_raw) else None
        nivel = _nivel_from_pct(pct_val_f)
        color = NIVELES_COLORS.get(nivel, "#9E9E9E")
        pct_label = f"{pct_val_f:.1f}%" if pct_val_f is not None else "Sin dato"
        proceso = str(row.get("Proceso", row.get("Proceso_padre", "—")))
        tipo = str(row.get("Tipo de proceso", "—"))
        unidad = str(row.get("Unidad", "—"))
        meta_val = row.get("Meta", "—")
        ejec_val = row.get("Ejecucion", "—")
        freq = str(row.get("Frecuencia", row.get("Periodicidad", "—")))
        status_text = nivel.title() if nivel != "sin dato" else "Sin dato"

        card_html = f"""
            <div class="cmi-ficha-card">
                <div class="cmi-ficha-card-header">
                    <div>
                        <div class="cmi-ficha-card-id">ID {row_id}</div>
                        <div class="cmi-ficha-card-title">{nombre}</div>
                        <div class="cmi-ficha-card-subtitle">{proceso} · {tipo} · {unidad}</div>
                    </div>
                    <div class="cmi-ficha-status">{status_text}</div>
                </div>
                <div class="cmi-ficha-stats">
                    <div class="cmi-ficha-stat">
                        <div class="cmi-ficha-stat-label">Meta</div>
                        <div class="cmi-ficha-stat-value">{meta_val}</div>
                    </div>
                    <div class="cmi-ficha-stat">
                        <div class="cmi-ficha-stat-label">Ejecución</div>
                        <div class="cmi-ficha-stat-value">{ejec_val}</div>
                    </div>
                    <div class="cmi-ficha-stat">
                        <div class="cmi-ficha-stat-label">Cumplimiento</div>
                        <div class="cmi-ficha-stat-value" style="color:{color};">{pct_label}</div>
                    </div>
                </div>
                <div class="cmi-ficha-footer">
                    <div class="cmi-ficha-footer-item">
                        <span class="cmi-ficha-footer-label">Frecuencia</span>
                        <span class="cmi-ficha-footer-value">{freq}</span>
                    </div>
                    <div class="cmi-ficha-footer-item">
                        <span class="cmi-ficha-footer-label">ID</span>
                        <span class="cmi-ficha-footer-value">{row_id}</span>
                    </div>
                </div>
            </div>
            """
        card_rows.append((card_html, row))
        shown += 1

    for i in range(0, len(card_rows), 2):
        cols = st.columns(2)
        for col, (card_html, row) in zip(cols, card_rows[i : i + 2]):
            col.markdown(card_html, unsafe_allow_html=True)
            btn_key = f"cmi_ficha_detail_{row.get('Id', '')}_{i}"
            if col.button("Ver detalle", key=btn_key, use_container_width=True):
                render_modal_ficha(row)

    if total_count > max_fichas:
        st.caption(
            f"Mostrando {max_fichas} de {total_count} indicadores. "
            "Usa los filtros de la Tabla Analítica para acotar."
        )


def render_analisis_unidad(df: pd.DataFrame, pct_col: str | None = None) -> None:
    """Ranking de unidades organizacionales por cumplimiento promedio."""
    if df.empty:
        return
    if "Unidad" not in df.columns:
        st.info("No hay datos de Unidad Organizacional disponibles en este corte.")
        return

    pct_col = pct_col or _resolve_pct_col(df)
    if pct_col is None or pct_col not in df.columns:
        st.info("No hay columna de cumplimiento disponible.")
        return

    df_work = df.copy()
    df_work["_pct_num"] = _normalize_pct(df_work[pct_col], pct_col)

    # Para CMI por Procesos, agrupar por Unidad usando conteo único de Id
    if _is_cmi_procesos(df_work) and "Id" in df_work.columns:
        df_work["Id_norm"] = df_work["Id"].astype(str).str.strip()
        # tomar último registro por Id para obtener Unidad y pct representativos
        sort_key = _build_sort_key(df_work)
        df_work = df_work.reindex(sort_key.index)
        df_work["_sort_key"] = sort_key
        # Para cada Id tomar el último valor no nulo por columna (más robusto que .last())
        cols_to_preserve = [
            "Indicador",
            "Proceso",
            "Proceso_padre",
            "Unidad",
            "Meta",
            "Ejecucion",
            "_pct_num",
            "Tipo de proceso",
            "Frecuencia",
            "Subproceso_final",
        ]
        present_cols = [c for c in cols_to_preserve if c in df_work.columns]
        def _last_valid(s):
            s2 = s.dropna()
            return s2.iloc[-1] if not s2.empty else pd.NA

        grouped = df_work.sort_values("_sort_key").groupby("Id_norm", dropna=False)
        agg_dict = {c: (_last_valid) for c in present_cols}
        per_id = grouped.agg(agg_dict).reset_index()
        # garantizar columnas mínimas
        if "Unidad" not in per_id.columns:
            per_id["Unidad"] = "—"
        ranking = (
            per_id.groupby("Unidad", dropna=False)
            .agg(
                indicadores=("Id_norm", lambda s: int(s.dropna().nunique())),
                cumplimiento=("_pct_num", "mean"),
                criticos=("_pct_num", lambda x: int((x < 80).sum())),
            )
            .reset_index()
            .sort_values("cumplimiento", ascending=False)
        )
    else:
        ranking = (
            df_work.groupby("Unidad", dropna=False)
            .agg(
                indicadores=("Indicador", "count"),
                cumplimiento=("_pct_num", "mean"),
                criticos=("_pct_num", lambda x: int((x < 80).sum())),
            )
            .reset_index()
            .sort_values("cumplimiento", ascending=False)
        )
    ranking["cumplimiento"] = pd.to_numeric(ranking["cumplimiento"], errors="coerce").round(1)
    ranking["Estado"] = ranking["cumplimiento"].apply(
        lambda v: "🟢 Saludable"
        if v >= 100
        else ("🟡 Alerta" if v >= 80 else ("🔴 Crítico" if pd.notna(v) else "—"))
    )

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = go.Figure(
            go.Bar(
                y=ranking["Unidad"].astype(str),
                x=ranking["cumplimiento"],
                orientation="h",
                marker_color=[
                    "#2E7D32" if v >= 100 else ("#F9A825" if v >= 80 else "#C62828")
                    for v in ranking["cumplimiento"]
                ],
                text=ranking["cumplimiento"].astype(str) + "%",
                textposition="auto",
            )
        )
        fig.update_layout(
            height=max(300, len(ranking) * 38),
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="Cumplimiento promedio (%)",
            yaxis_title="",
            showlegend=False,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )

        # Generar una key determinista para evitar StreamlitDuplicateElementId
        try:
            unidades_list = ranking["Unidad"].astype(str).tolist()
            key_seed = "|".join(unidades_list) + f"|{pct_col or ''}|{len(unidades_list)}"
            base_key = "analisis_unidad_" + hashlib.md5(key_seed.encode("utf-8")).hexdigest()[:10]
        except Exception:
            base_key = None

        # Asegurar unicidad en la misma ejecución usando un contador incremental
        try:
            global _PLOT_KEY_COUNTER
            _PLOT_KEY_COUNTER += 1
            if base_key:
                unique_key = f"{base_key}_{_PLOT_KEY_COUNTER}"
            else:
                unique_key = f"analisis_unidad_auto_{_PLOT_KEY_COUNTER}"
        except Exception:
            unique_key = None

        st.plotly_chart(fig, use_container_width=True, key=unique_key)

    with c2:
        tabla_unidad = ranking.rename(
            columns={
                "Unidad": "Unidad",
                "indicadores": "# Indicadores",
                "cumplimiento": "Cumplimiento %",
                "criticos": "# Críticos",
            }
        )
        st.dataframe(
            tabla_unidad[["Unidad", "# Indicadores", "Cumplimiento %", "# Críticos", "Estado"]],
            use_container_width=True,
            hide_index=True,
        )


def render_historico_tab(df: pd.DataFrame, pct_col: str | None = None) -> None:
    """Análisis histórico: evolución temporal de indicadores seleccionados."""
    if df.empty:
        st.info("No hay datos históricos disponibles para este filtro.")
        return

    pct_col = pct_col or _resolve_pct_col(df)
    if pct_col is None or pct_col not in df.columns:
        st.info("No hay columna de cumplimiento disponible para el análisis histórico.")
        return

    indicadores = (
        sorted(df["Indicador"].dropna().astype(str).unique().tolist())
        if "Indicador" in df.columns
        else []
    )
    if not indicadores:
        st.info("No se encontraron indicadores en los datos.")
        return

    sel_ind = st.selectbox(
        "Selecciona un indicador para visualizar su evolución",
        options=indicadores,
        index=0,
        key="cmi_historico_selectbox",
    )
    if not sel_ind:
        st.caption("No hay indicadores disponibles para visualizar.")
        return
    
    sel_ind = [sel_ind]  # Convertir a lista para compatibilidad con resto del código

    period_col = next(
        (c for c in ("Mes", "Periodo", "Fecha", "Anio") if c in df.columns), None
    )
    if period_col is None:
        st.info("No se encontró columna temporal (Mes, Periodo, Fecha) para el gráfico.")
        return

    COLORS_CYCLE = [
        "#1A3A5C", "#43A047", "#FBAF17", "#E57373",
        "#6699FF", "#FB8C00", "#26A69A", "#AB47BC",
    ]

    fig = go.Figure()
    trend_rows = []

    for i, ind in enumerate(sel_ind):
        ind_df = df[df["Indicador"].astype(str) == ind].sort_values(period_col).copy()
        if ind_df.empty:
            continue
        vals = _normalize_pct(ind_df[pct_col], pct_col)
        ind_df["_pct"] = vals
        trend = _detect_trend(vals.tolist())
        color = COLORS_CYCLE[i % len(COLORS_CYCLE)]

        fig.add_trace(
            go.Scatter(
                x=ind_df[period_col].astype(str),
                y=ind_df["_pct"].round(1),
                mode="lines+markers",
                name=f"{trend} {ind[:40]}",
                line=dict(color=color, width=2),
                marker=dict(size=6),
                hovertemplate="%{y:.1f}%<extra>" + ind[:30] + "</extra>",
            )
        )
        avg_val = float(vals.mean()) if not vals.dropna().empty else 0.0
        trend_rows.append(
            {
                "Indicador": ind,
                "Tendencia": trend,
                "Promedio %": round(avg_val, 1),
                "Estado": _nivel_from_pct(avg_val).capitalize(),
                "# Períodos": int(vals.dropna().count()),
            }
        )

    fig.add_hline(y=100, line_dash="dash", line_color="#2E7D32", annotation_text="Meta 100%")
    fig.add_hline(y=80, line_dash="dot", line_color="#F9A825", annotation_text="Alerta 80%")
    fig.update_layout(
        height=420,
        margin=dict(t=20, b=40, l=10, r=10),
        xaxis_title="Período",
        yaxis_title="Cumplimiento (%)",
        legend_title="Indicadores",
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FFFFFF",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    if trend_rows:
        st.markdown("##### Resumen de tendencias")
        st.dataframe(pd.DataFrame(trend_rows), use_container_width=True, hide_index=True)
