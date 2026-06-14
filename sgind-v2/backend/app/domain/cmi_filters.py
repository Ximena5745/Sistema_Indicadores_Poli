"""Filtros CMI — portado desde services/cmi_filters (sin dependencia de Streamlit)."""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from app.services.excel_reader import ExcelReaderService

_CMI_CANDIDATES = [
    "raw/Indicadores por CMI.xlsx",
    "raw/Excel_Entrada/CMI.xlsx",
]


def _normalize_flag_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raw = series.astype(str).str.strip().str.lower()
        mapped = raw.map(
            {
                "1": 1,
                "1.0": 1,
                "si": 1,
                "true": 1,
                "x": 1,
                "0": 0,
                "0.0": 0,
                "no": 0,
                "false": 0,
                "": 0,
            }
        )
        numeric = numeric.fillna(mapped)
    return numeric


def _normalize_id_value(val) -> str:
    if pd.isna(val):
        return ""
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(int(val)) if val.is_integer() else str(val).strip()
    text = str(val).strip()
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except Exception:
        return text
    return text


class CMIFilterService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def _resolve_cmi_path(self) -> str | None:
        for candidate in _CMI_CANDIDATES:
            if (self._excel.data_root / candidate).exists():
                return candidate
        return None

    def load_cmi_worksheet(self) -> pd.DataFrame:
        path = self._resolve_cmi_path()
        if not path:
            return pd.DataFrame()
        try:
            df = self._excel.read_excel(path, sheet_name="Worksheet")
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            return pd.DataFrame()

    def get_estrategico_ids(self) -> set[str]:
        df = self.load_cmi_worksheet()
        if df.empty:
            return set()
        col_plan = next(
            (c for c in df.columns if "plan estrateg" in c.lower() or c == "Indicadores Plan estrategico"),
            None,
        )
        if not col_plan or "Proyecto" not in df.columns or "Id" not in df.columns:
            return set()

        flag_estrategico = _normalize_flag_series(df[col_plan])
        flag_proyecto = _normalize_flag_series(df["Proyecto"])
        filtered = df[(flag_estrategico == 1) & (flag_proyecto != 1)]
        return {_normalize_id_value(v) for v in filtered["Id"].dropna() if _normalize_id_value(v)}

    def get_proyectos_ids(self) -> set[str]:
        df = self.load_cmi_worksheet()
        if df.empty or "Proyecto" not in df.columns or "Id" not in df.columns:
            return set()
        flag_proyecto = _normalize_flag_series(df["Proyecto"])
        filtered = df[flag_proyecto == 1]
        return {_normalize_id_value(v) for v in filtered["Id"].dropna() if _normalize_id_value(v)}

    def get_procesos_ids(self, year: Optional[int] = None) -> set[str]:
        df = self.load_cmi_worksheet()
        if df.empty or "Subprocesos" not in df.columns or "Id" not in df.columns:
            return set()
        flag_sub = _normalize_flag_series(df["Subprocesos"])
        filtered = df[flag_sub == 1]
        base_ids = {_normalize_id_value(v) for v in filtered["Id"].dropna() if _normalize_id_value(v)}
        if year is None:
            return base_ids
        kawak_ids = self._load_kawak_active_ids(year)
        if not kawak_ids:
            return set()
        intersect = base_ids.intersection(kawak_ids)
        return intersect if intersect else set()

    def _load_kawak_active_ids(self, year: int) -> set[str]:
        folder = self._excel.data_root / "raw" / "Fuentes Consolidadas"
        if not folder.exists():
            return set()
        ids: set[str] = set()
        for path in folder.glob("*.xlsx"):
            try:
                df_k = self._excel.read_excel(str(path.relative_to(self._excel.data_root)))
                if df_k.empty:
                    continue
                id_col = next(
                    (c for c in df_k.columns if str(c).strip().lower() in ("id", "id_indicador", "idindicador")),
                    None,
                )
                if id_col is None:
                    continue
                year_col = next(
                    (c for c in df_k.columns if str(c).strip().lower() in ("anio", "año", "year")),
                    None,
                )
                if year_col is not None:
                    df_k = df_k[pd.to_numeric(df_k[year_col], errors="coerce").fillna(0).astype(int) == int(year)]
                else:
                    match = re.search(r"(20\d{2})", path.name)
                    if match and int(match.group(1)) != int(year):
                        continue
                for val in df_k[id_col].dropna():
                    norm = _normalize_id_value(val)
                    if norm:
                        ids.add(norm)
            except Exception:
                continue
        return ids

    def filter_estrategico(self, df: pd.DataFrame, id_column: str = "Id") -> pd.DataFrame:
        if df.empty or id_column not in df.columns:
            return df
        valid_ids = self.get_estrategico_ids()
        if not valid_ids:
            return df
        norm = df[id_column].apply(_normalize_id_value)
        return df[norm.isin(valid_ids)].copy()

    def filter_proyectos(self, df: pd.DataFrame, id_column: str = "Id") -> pd.DataFrame:
        if df.empty or id_column not in df.columns:
            return df
        valid_ids = self.get_proyectos_ids()
        if not valid_ids:
            return df.iloc[0:0]
        norm = df[id_column].apply(_normalize_id_value)
        return df[norm.isin(valid_ids)].copy()

    def get_procesos_subprocesos(self, map_df: pd.DataFrame) -> set[str]:
        """Subprocesos válidos: intersección CMI (Subprocesos=1) y mapa maestro."""
        if map_df.empty or "Subproceso" not in map_df.columns:
            return set()
        cmi_df = self.load_cmi_worksheet()
        if cmi_df.empty or "Subprocesos" not in cmi_df.columns or "Subproceso" not in cmi_df.columns:
            return set()
        sub_cmi = set(
            cmi_df.loc[_normalize_flag_series(cmi_df["Subprocesos"]) == 1, "Subproceso"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )
        sub_map = set(map_df["Subproceso"].dropna().astype(str).str.strip().tolist())
        return sub_cmi & sub_map

    def filter_procesos(
        self,
        df: pd.DataFrame,
        *,
        anio: int | None = None,
        id_column: str = "Id",
        map_df: pd.DataFrame | None = None,
        omit_if_no_cross: bool = True,
    ) -> pd.DataFrame:
        if df.empty or id_column not in df.columns:
            return df
        valid_ids = self.get_procesos_ids(anio)
        if not valid_ids:
            return df.iloc[0:0]
        norm = df[id_column].apply(_normalize_id_value)
        filtered = df[norm.isin(valid_ids)].copy()
        if map_df is not None and not map_df.empty and "Subproceso" in filtered.columns:
            valid_subs = self.get_procesos_subprocesos(map_df)
            if valid_subs:
                filtered = filtered[filtered["Subproceso"].astype(str).str.strip().isin(valid_subs)]
            elif omit_if_no_cross:
                return df.iloc[0:0]
        return filtered
