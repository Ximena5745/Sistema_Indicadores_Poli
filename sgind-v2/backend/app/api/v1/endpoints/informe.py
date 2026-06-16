from fastapi import APIRouter, Depends, Query

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.services.excel_reader import ExcelReaderService
from app.services.informe_service import InformeService

router = APIRouter()


def _service(excel: ExcelReaderService = Depends(get_excel_service)) -> InformeService:
    return InformeService(excel)


@router.get("/dashboard")
async def informe_dashboard(
    anio: int = Query(...),
    mes: int | None = Query(None, ge=1, le=12),
    unidad: str | None = Query(None),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    clasificacion: str | None = Query(None),
    frecuencia: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: InformeService = Depends(_service),
) -> dict:
    return service.get_dashboard(
        anio=anio,
        mes=mes or 12,
        unidad=unidad,
        proceso=proceso,
        subproceso=subproceso,
        clasificacion=clasificacion,
        frecuencia=frecuencia,
    )
