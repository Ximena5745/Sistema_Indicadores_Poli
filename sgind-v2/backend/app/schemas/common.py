from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str


class MessageResponse(BaseModel):
    message: str
    detail: dict[str, Any] | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str | None = None
    role: RoleResponse
    is_active: bool
    created_at: datetime


class LoginResponse(BaseModel):
    authorization_url: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegistroOMBase(BaseModel):
    id_indicador: str
    nombre_indicador: str | None = None
    proceso: str | None = None
    periodo: str | None = None
    anio: int | None = None
    sede: str | None = None
    tiene_om: int = 0
    tipo_accion: str = "OM Kawak"
    numero_om: str | None = None
    comentario: str | None = None
    registrado_por: str = ""


class RegistroOMCreate(RegistroOMBase):
    pass


class RegistroOMUpdate(BaseModel):
    nombre_indicador: str | None = None
    proceso: str | None = None
    periodo: str | None = None
    anio: int | None = None
    sede: str | None = None
    tiene_om: int | None = None
    tipo_accion: str | None = None
    numero_om: str | None = None
    comentario: str | None = None


class RegistroOMCerrar(BaseModel):
    comentario: str | None = None


class RegistroOMResponse(RegistroOMBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_registro: str | None = None
    created_at: datetime
    updated_at: datetime


class KPIResponse(BaseModel):
    label: str
    value: float | int | str
    unit: str | None = None
    trend: str | None = None


class DashboardKPIsResponse(BaseModel):
    anio: int | None = None
    periodo: str | None = None
    kpis: list[KPIResponse] = Field(default_factory=list)
    source: str = "excel"


class SemaphoreItem(BaseModel):
    categoria: str
    count: int
    percent: float


class TrendItem(BaseModel):
    periodo: str
    cumplimiento: float | None = None


class IndicatorListResponse(BaseModel):
    total: int
    items: list[dict[str, Any]] = Field(default_factory=list)
    limit: int = 500
    offset: int = 0
    error: str | None = None


class CMILineaItem(BaseModel):
    linea: str
    total_indicadores: int
    cumplimiento_promedio: float | None = None
    en_riesgo: int = 0


class CMIEstrategicoResponse(BaseModel):
    anio: int | None = None
    total_indicadores: int = 0
    lineas: list[CMILineaItem] = Field(default_factory=list)


class CMIProcesoItem(BaseModel):
    proceso: str
    total_indicadores: int
    cumplimiento_promedio: float | None = None
    categorias: dict[str, int] = Field(default_factory=dict)


class CMIProcesosResponse(BaseModel):
    anio: int | None = None
    total_indicadores: int = 0
    procesos: list[CMIProcesoItem] = Field(default_factory=list)


class CMIProcesosFiltrosResponse(BaseModel):
    anios: list[int] = Field(default_factory=list)
    anio_default: int
    meses: list[int] = Field(default_factory=list)
    mes_default: int = 12
    meses_nombres: list[str] = Field(default_factory=list)
    unidades: list[str] = Field(default_factory=list)
    procesos: list[str] = Field(default_factory=list)
    subprocesos: list[str] = Field(default_factory=list)
    subprocesos_por_proceso: dict[str, list[str]] = Field(default_factory=dict)
    clasificaciones: list[str] = Field(default_factory=list)
    frecuencias: list[str] = Field(default_factory=list)


class CMIProcesosDashboardResponse(BaseModel):
    anio: int
    mes: int
    mes_nombre: str
    anios_disponibles: list[int] = Field(default_factory=list)
    meses_disponibles: list[int] = Field(default_factory=list)
    filtros_aplicados: dict[str, str] = Field(default_factory=dict)
    total_indicadores: int = 0
    kpis: dict[str, Any] = Field(default_factory=dict)
    banner: dict[str, Any] = Field(default_factory=dict)
    distribucion_nivel: list[dict[str, Any]] = Field(default_factory=list)
    tipo_proceso_cards: list[dict[str, Any]] = Field(default_factory=list)
    proceso_bars: list[dict[str, Any]] = Field(default_factory=list)
    catalog_charts: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    procesos_detalle: list[dict[str, Any]] = Field(default_factory=list)
    unidades_detalle: list[dict[str, Any]] = Field(default_factory=list)
    indicadores_summary: dict[str, int] = Field(default_factory=dict)
    indicadores: list[dict[str, Any]] = Field(default_factory=list)
    alertas: dict[str, Any] = Field(default_factory=dict)
    variacion: dict[str, Any] = Field(default_factory=dict)
    analisis_avanzado: dict[str, Any] = Field(default_factory=dict)
    calidad: dict[str, Any] = Field(default_factory=dict)
    vista_global: dict[str, Any] = Field(default_factory=dict)
    ejecucion_variacion: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


class CMIAlertasResponse(BaseModel):
    anio: int | None = None
    mes: int | None = None
    total: int = 0
    peligro: int = 0
    alerta: int = 0
    alertas: list[dict[str, Any]] = Field(default_factory=list)


class CMIFiltrosResponse(BaseModel):
    anios: list[int] = Field(default_factory=list)
    anio_default: int
    corte_default: str
    cortes: list[str] = Field(default_factory=list)


class CMIDashboardResponse(BaseModel):
    anio: int
    mes: int
    corte: str
    anios_disponibles: list[int] = Field(default_factory=list)
    cortes: list[str] = Field(default_factory=list)
    total_indicadores: int = 0
    kpis: dict[str, Any] = Field(default_factory=dict)
    cumplimiento_por_linea: list[dict[str, Any]] = Field(default_factory=list)
    distribucion_nivel: list[dict[str, Any]] = Field(default_factory=list)
    vista_rapida_lineas: list[dict[str, Any]] = Field(default_factory=list)
    insights: list[dict[str, str]] = Field(default_factory=list)
    lineas_detalle: list[dict[str, Any]] = Field(default_factory=list)
    indicadores: list[dict[str, Any]] = Field(default_factory=list)
    alertas: dict[str, Any] = Field(default_factory=dict)


class ExcelFileInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    modified_at: datetime
