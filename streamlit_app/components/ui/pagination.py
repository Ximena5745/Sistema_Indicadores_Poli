"""
streamlit_app/components/ui/pagination.py

Componente reutilizable de paginación para tabs que muestren listas/tablas.

Características:
- Gestión automática de página con session_state
- Reset automático al cambiar filtros (key digest)
- Controles de navegación (primera/anterior/siguiente/última)
- Información de página actual
- Callback para renderizar filas personalizadas

Uso:
    from streamlit_app.components.ui.pagination import PaginationManager
    
    pm = PaginationManager(
        df=filtered_df,
        key_prefix="my_tab",
        rows_per_page=25,
        on_render_row=lambda row, idx: st.write(row)
    )
    total, page, df_page = pm.paginate()
    # Renderizar df_page y controles de navegación
"""

import streamlit as st
import pandas as pd
from math import ceil
from typing import Callable, Optional, Tuple


class PaginationManager:
    """Gestor de paginación para DataFrames en Streamlit."""

    def __init__(
        self,
        df: pd.DataFrame,
        key_prefix: str = "pagination",
        rows_per_page: int = 25,
        on_render_row: Optional[Callable] = None,
    ):
        """
        Inicializa el gestor de paginación.

        Args:
            df: DataFrame a paginar
            key_prefix: Prefijo para las claves en session_state
            rows_per_page: Número de filas por página
            on_render_row: Callback opcional para renderizar cada fila (row, idx) -> None
        """
        self.df = df.reset_index(drop=True) if not df.empty else df
        self.key_prefix = key_prefix
        self.rows_per_page = rows_per_page
        self.on_render_row = on_render_row

    def _page_key(self) -> str:
        """Retorna la clave para el número de página en session_state."""
        return f"{self.key_prefix}_page"

    def _filter_key(self) -> str:
        """Retorna la clave para el digest de filtros en session_state."""
        return f"{self.key_prefix}_filter_digest"

    def _compute_digest(self) -> str:
        """Computa un digest simple basado en el tamaño y hash del DataFrame."""
        if self.df.empty:
            return "empty"
        return f"{len(self.df)}_{hash(tuple(self.df.columns))}"

    def reset_if_filter_changed(self) -> None:
        """Reseta la página a 1 si los filtros han cambiado."""
        current_digest = self._compute_digest()
        stored_digest = st.session_state.get(self._filter_key())
        
        if stored_digest != current_digest:
            st.session_state[self._page_key()] = 1
            st.session_state[self._filter_key()] = current_digest

    def paginate(self) -> Tuple[int, int, pd.DataFrame]:
        """
        Realiza la paginación y retorna (total_filas, página_actual, df_pagina).

        Maneja automáticamente el reset de página y boundaries.
        """
        self.reset_if_filter_changed()

        total = len(self.df)
        total_pages = max(1, ceil(total / self.rows_per_page))

        # Inicializar o recuperar página actual
        if self._page_key() not in st.session_state:
            st.session_state[self._page_key()] = 1

        page = st.session_state[self._page_key()]
        page = max(1, min(page, total_pages))
        st.session_state[self._page_key()] = page

        # Slicear el DataFrame
        start_idx = (page - 1) * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        df_page = self.df.iloc[start_idx:end_idx].reset_index(drop=True)

        return total, page, df_page

    def render_controls(
        self,
        total: int,
        page: int,
        total_pages: int,
        start_idx: int,
        end_idx: int,
        position: str = "bottom",
    ) -> None:
        """
        Renderiza los controles de navegación (botones y información de página).

        Args:
            total: Total de filas
            page: Página actual
            total_pages: Total de páginas
            start_idx: Índice inicial de la página
            end_idx: Índice final de la página
            position: "top" o "bottom" (posición relativa)
        """
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        
        p1, p2, p3, p4, p5 = st.columns([1.1, 1.1, 2.5, 1.1, 1.1])

        with p1:
            if st.button(
                "⟨⟨ Primera",
                disabled=(page == 1),
                use_container_width=True,
                key=f"{self.key_prefix}_pg_first_{position}",
            ):
                st.session_state[self._page_key()] = 1
                st.rerun()

        with p2:
            if st.button(
                "⟨ Anterior",
                disabled=(page == 1),
                use_container_width=True,
                key=f"{self.key_prefix}_pg_prev_{position}",
            ):
                st.session_state[self._page_key()] = page - 1
                st.rerun()

        with p3:
            st.markdown(
                f"<div style='text-align:center;font-size:0.83rem;color:#64748B;padding-top:8px'>"
                f"Página <b>{page}</b> de <b>{total_pages}</b> "
                f"({start_idx + 1}–{min(end_idx, total)} de {total})</div>",
                unsafe_allow_html=True,
            )

        with p4:
            if st.button(
                "Siguiente ⟩",
                disabled=(page >= total_pages),
                use_container_width=True,
                key=f"{self.key_prefix}_pg_next_{position}",
            ):
                st.session_state[self._page_key()] = page + 1
                st.rerun()

        with p5:
            if st.button(
                "Última ⟩⟩",
                disabled=(page >= total_pages),
                use_container_width=True,
                key=f"{self.key_prefix}_pg_last_{position}",
            ):
                st.session_state[self._page_key()] = total_pages
                st.rerun()

    def render_rows(self, df_page: pd.DataFrame, render_func: Callable) -> None:
        """
        Renderiza las filas de la página actual usando la función proporcionada.

        Args:
            df_page: DataFrame de la página actual
            render_func: Función que renderiza una fila: (row, idx, global_idx) -> None
        """
        if df_page.empty:
            st.warning("No hay filas para mostrar en esta página.")
            return

        total = len(self.df)
        page = st.session_state.get(self._page_key(), 1)
        start_idx = (page - 1) * self.rows_per_page

        for idx, (_, row) in enumerate(df_page.iterrows()):
            global_idx = start_idx + idx
            render_func(row, idx, global_idx)
