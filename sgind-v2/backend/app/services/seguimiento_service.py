"""Servicio Seguimiento Operativo."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.domain.seguimiento_builders import apply_filters, build_dashboard, load_tracking
from app.services.excel_reader import ExcelReaderService


class SeguimientoService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def get_dashboard(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        df = load_tracking(self._excel)
        if df.empty:
            return {"error": "No se encontró Tracking Mensual en Seguimiento_Reporte.xlsx", "kpis": {}}
        filtros = build_dashboard(df, anio=anio, mes=mes, proceso=proceso, estado=estado)
        if anio is None:
            anio = filtros["filtros"].get("anio_default")
        if mes is None:
            mes = filtros["filtros"].get("mes_default")
        return build_dashboard(df, anio=anio, mes=mes, proceso=proceso, estado=estado)

    def export_excel(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> bytes:
        df = load_tracking(self._excel)
        df_view = apply_filters(df, anio=anio, mes=mes, proceso=proceso, estado=estado)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_view.to_excel(writer, index=False, sheet_name="Tracking Filtrado")
        return buffer.getvalue()
