filepath = r"streamlit_app\pages\resumen_por_proceso.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

# Bloque antiguo: desde _AUDITORIA_XLSX hasta el final de _render_auditoria_tab
START_MARKER = "_AUDITORIA_XLSX = Path(__file__).resolve().parents[2]"
END_MARKER = "\n\n\n@st.cache_data(show_spinner=False)\ndef _load_auditoria_mentions"

if START_MARKER not in content:
    print("MARKER INICIO NO ENCONTRADO")
    exit(1)
if END_MARKER not in content:
    print("MARKER FIN NO ENCONTRADO — buscando alternativa")
    END_MARKER = "\n\ndef _load_auditoria_mentions"
    if END_MARKER not in content:
        print("MARKER FIN ALTERNATIVO NO ENCONTRADO")
        exit(1)

start_idx = content.index(START_MARKER)
end_idx = content.index(END_MARKER, start_idx)

NEW_BLOCK = '''_AUDITORIA_XLSX = Path(__file__).resolve().parents[2] / "data" / "raw" / "Auditoria" / "auditoria_resultado.xlsx"

# campo → (label, color_acento, simbolo)
_AUD_LABELS = {
    "fortalezas":              ("Fortalezas",              "#0d6e55", "✦"),
    "oportunidades_mejora":    ("Oportunidades de Mejora", "#7a5c00", "◈"),
    "hallazgos":               ("Hallazgos",               "#1b4f8a", "◉"),
    "no_conformidades":        ("No Conformidades",        "#8b1a1a", "▲"),
    "recomendacion_desempeno": ("Recomendacion Desempeno", "#3d2b8e", "◆"),
}


@st.cache_data(show_spinner=False)
def _load_auditoria_excel() -> tuple:
    if not _AUDITORIA_XLSX.exists():
        return pd.DataFrame(), f"No existe el archivo: {_AUDITORIA_XLSX.name}. Ejecuta scripts/generar_auditoria_csv.py primero."
    try:
        df = pd.read_excel(_AUDITORIA_XLSX, sheet_name="Auditoria", engine="openpyxl")
        df = df.fillna("")
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"Error leyendo Excel de auditoria: {e}"


def _render_ficha_html(row: dict, tipo: str) -> str:
    """HTML completamente inline (sin clases CSS) para evitar issues con st.markdown."""
    es_interna = tipo.lower() == "interna"
    grad = "linear-gradient(135deg,#1b3f72 0%,#2563a8 100%)" if es_interna else "linear-gradient(135deg,#5a3000 0%,#b06000 100%)"
    tipo_label = "Auditoria Interna" if es_interna else "Auditoria Externa - Icontec 2025"
    proceso = str(row.get("proceso", "")).upper()

    secciones = ""
    for campo, (label, accent, sym) in _AUD_LABELS.items():
        valor = str(row.get(f"{campo}_{tipo.lower()}", "")).strip()
        if not valor:
            continue
        items = [v.strip() for v in valor.replace("\\n", " | ").split(" | ") if v.strip()]
        items_html = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:8px;padding:4px 0;font-size:0.86rem;color:#333;line-height:1.5;">'
            f'<span style="color:{accent};font-size:0.65rem;margin-top:5px;flex-shrink:0;">{sym}</span>'
            f'<span>{item}</span></div>'
            for item in items
        )
        secciones += (
            f'<div style="padding:8px 18px;border-bottom:1px solid #f0f0f0;">'
            f'<div style="display:flex;align-items:center;gap:6px;font-size:0.7rem;font-weight:700;'
            f'letter-spacing:0.08em;text-transform:uppercase;color:{accent};margin-bottom:5px;">'
            f'<span style="width:8px;height:8px;border-radius:2px;background:{accent};display:inline-block;flex-shrink:0;"></span>'
            f'{label}</div>{items_html}</div>'
        )

    if not secciones:
        return ""

    return (
        f'<div style="background:#fafafa;border:1px solid #e4e4e4;border-radius:12px;overflow:hidden;'
        f'box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:16px;">'
        f'<div style="background:{grad};padding:12px 18px;color:#fff;font-size:0.88rem;'
        f'font-weight:700;letter-spacing:0.03em;text-transform:uppercase;">{tipo_label}</div>'
        f'<div style="padding:14px 18px 6px 18px;font-size:1rem;font-weight:700;color:#1a1a2e;'
        f'border-bottom:2px solid #f0f0f0;margin-bottom:2px;">{proceso}</div>'
        f'{secciones}'
        f'</div>'
    )


def _render_auditoria_tab(proceso_filtro: str) -> None:
    """Renderiza la pestana Auditoria como fichas ejecutivas por proceso."""
    df, msg = _load_auditoria_excel()
    if msg:
        st.warning(msg)
        return
    if df.empty:
        st.info("No hay datos de auditoria disponibles.")
        return

    if proceso_filtro and proceso_filtro.upper() != "TODOS":
        mask = df["proceso"].str.upper().str.contains(proceso_filtro.upper(), na=False)
        df_filtrado = df[mask]
    else:
        df_filtrado = df

    if df_filtrado.empty:
        st.info(f"No hay hallazgos de auditoria para el proceso: {proceso_filtro}")
        return

    def _seccion(tipo: str, titulo: str, header_color: str) -> None:
        cols_check = [f"{c}_{tipo}" for c in _AUD_LABELS]
        df_tipo = df_filtrado[
            df_filtrado[[c for c in cols_check if c in df_filtrado.columns]]
            .apply(lambda r: r.str.strip().ne("").any(), axis=1)
        ]
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;margin:24px 0 10px 0;">'
            f'<div style="width:4px;height:32px;border-radius:2px;background:{header_color};flex-shrink:0;"></div>'
            f'<div><div style="font-size:1rem;font-weight:700;color:#1a1a2e;">{titulo}</div>'
            f'<div style="font-size:0.75rem;color:#888;">{len(df_tipo)} proceso(s)</div></div></div>',
            unsafe_allow_html=True,
        )
        if df_tipo.empty:
            st.info(f"No hay hallazgos de {titulo.lower()} para el proceso seleccionado.")
            return
        for _, row in df_tipo.iterrows():
            html = _render_ficha_html(row.to_dict(), tipo)
            if html:
                st.markdown(html, unsafe_allow_html=True)

    _seccion("interna", "Auditoria Interna", "#1b3f72")
    st.markdown('<hr style="border:none;border-top:1px solid #e8e8e8;margin:8px 0;">', unsafe_allow_html=True)
    _seccion("externa", "Auditoria Externa - Icontec 2025", "#b06000")

'''

new_content = content[:start_idx] + NEW_BLOCK + content[end_idx:]
with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)
print("REEMPLAZADO OK")

