filepath = r"streamlit_app\pages\resumen_por_proceso.py"
with open(filepath, encoding="utf-8") as f:
    content = f.read()

if "def _load_auditoria_excel" in content:
    print("YA EXISTE - nada que hacer")
else:
    func = (
        "\n\n@st.cache_data(show_spinner=False)\n"
        "def _load_auditoria_excel() -> tuple:\n"
        '    if not _AUDITORIA_XLSX.exists():\n'
        '        return pd.DataFrame(), f"No existe el archivo: {_AUDITORIA_XLSX.name}. Ejecuta scripts/generar_auditoria_csv.py primero."\n'
        "    try:\n"
        '        df = pd.read_excel(_AUDITORIA_XLSX, sheet_name="Auditoria", engine="openpyxl")\n'
        '        df = df.fillna("")\n'
        "        return df, None\n"
        "    except Exception as e:\n"
        '        return pd.DataFrame(), f"Error leyendo Excel de auditoria: {e}"\n'
        "\n\n"
    )
    marker = "def _render_ficha(row: dict, tipo: str) -> str:"
    if marker not in content:
        print("MARKER NO ENCONTRADO")
    else:
        content = content.replace(marker, func + marker, 1)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("INSERTADO OK")
