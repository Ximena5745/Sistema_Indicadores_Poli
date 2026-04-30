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


# ── Helpers internos ──────────────────────────────────────────────────────────

def _resolve_pct_col(df: pd.DataFrame) -> str | None:
    """Resuelve el nombre de la columna de cumplimiento disponible en el DataFrame."""
    for col in ("cumplimiento_pct", "Cumplimiento_pct", "Cumplimiento_norm"):
        if col in df.columns:
            return col
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


# ── Componentes públicos ───────────────────────────────────────────────────────

def render_executive_kpis(df: pd.DataFrame, pct_col: str | None = None) -> None:
    """Fila de 4 KPIs ejecutivos: en meta, en alerta, críticos, cumplimiento global."""
    if df.empty:
        return
    pct_col = pct_col or _resolve_pct_col(df)
    if pct_col is None or pct_col not in df.columns:
        return

    vals = _normalize_pct(df[pct_col], pct_col)
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
    if "Unidad" in df.columns:
        filtro_defs["Unidad"] = "Unidad"

    filtered = df.copy()
    if filtro_defs:
        fcols = st.columns(min(len(filtro_defs), 3))
        for idx, (label, col_actual) in enumerate(filtro_defs.items()):
            opts = sorted(filtered[col_actual].dropna().astype(str).unique().tolist())
            with fcols[idx % len(fcols)]:
                sel = st.multiselect(
                    f"Filtrar por {label}",
                    options=opts,
                    key=f"cmi_tabla_filter_{label}",
                )
                if sel:
                    filtered = filtered[filtered[col_actual].astype(str).isin(sel)]

    # ── Construir tabla de visualización ─────────────────────────────────────
    col_priority = [
        ("Indicador", "Indicador"),
        ("Proceso_padre", "Proceso"),
        ("Proceso", "Proceso"),
        ("Tipo de proceso", "Tipo"),
        ("Unidad", "Unidad"),
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

    if pct_col and pct_col in filtered.columns:
        vals = _normalize_pct(filtered[pct_col], pct_col)
        tabla["Cumplimiento %"] = vals.round(1)
        tabla["Estado"] = vals.apply(
            lambda v: "🟢 Meta"
            if v >= 100
            else ("🟡 Alerta" if v >= 80 else ("🔴 Crítico" if pd.notna(v) else "⬜ Sin dato"))
        )

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
    """Fichas expandibles por indicador: meta, ejecución, cumplimiento, tendencia."""
    if df.empty:
        st.info("No hay indicadores para mostrar en este corte.")
        return

    pct_col = pct_col or _resolve_pct_col(df)
    df_work = df.copy()

    if pct_col and pct_col in df_work.columns:
        vals = _normalize_pct(df_work[pct_col], pct_col)
        df_work["_pct_num"] = vals
        df_work = df_work.sort_values("_pct_num", ascending=True)
    else:
        df_work["_pct_num"] = pd.NA

    shown = 0
    for _, row in df_work.iterrows():
        if shown >= max_fichas:
            break

        nombre = str(row.get("Indicador", f"Indicador {shown + 1}"))
        pct_raw = row.get("_pct_num", None)
        pct_val_f: float | None = float(pct_raw) if pd.notna(pct_raw) else None
        nivel = _nivel_from_pct(pct_val_f)
        color = NIVELES_COLORS.get(nivel, "#9E9E9E")
        icono = (
            "🔴" if nivel == "peligro"
            else "🟡" if nivel == "alerta"
            else "🟢" if nivel in ("cumplimiento", "sobrecumplimiento")
            else "⬜"
        )
        pct_label = f"{pct_val_f:.1f}%" if pct_val_f is not None else "Sin dato"
        proceso = str(row.get("Proceso", row.get("Proceso_padre", "—")))
        tipo = str(row.get("Tipo de proceso", "—"))
        unidad = str(row.get("Unidad", "—"))
        meta_val = row.get("Meta", "—")
        ejec_val = row.get("Ejecucion", "—")
        freq = str(row.get("Frecuencia", row.get("Periodicidad", "—")))

        with st.expander(f"{icono} {nombre} — {pct_label}", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    f"""<div class="cmi-ficha-meta">
                        <div class="cmi-ficha-label">Meta</div>
                        <div class="cmi-ficha-value">{meta_val}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"""<div class="cmi-ficha-meta">
                        <div class="cmi-ficha-label">Ejecución</div>
                        <div class="cmi-ficha-value">{ejec_val}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"""<div class="cmi-ficha-meta">
                        <div class="cmi-ficha-label">Cumplimiento</div>
                        <div class="cmi-ficha-value" style="color:{color};">{pct_label}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"""<div class="cmi-ficha-detail">
                    📁 <strong>Proceso:</strong> {proceso} &nbsp;|&nbsp;
                    🏷️ <strong>Tipo:</strong> {tipo} &nbsp;|&nbsp;
                    🏢 <strong>Unidad:</strong> {unidad} &nbsp;|&nbsp;
                    📅 <strong>Frecuencia:</strong> {freq}
                </div>""",
                unsafe_allow_html=True,
            )
        shown += 1

    if len(df_work) > max_fichas:
        st.caption(
            f"Mostrando {max_fichas} de {len(df_work)} indicadores. "
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
    ranking["cumplimiento"] = ranking["cumplimiento"].round(1)
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
        st.plotly_chart(fig, use_container_width=True)

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

    sel_ind = st.multiselect(
        "Selecciona indicadores para comparar (máx. 8)",
        options=indicadores,
        max_selections=8,
        key="cmi_historico_multiselect",
    )
    if not sel_ind:
        st.caption("Selecciona al menos un indicador para visualizar su evolución.")
        return

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
