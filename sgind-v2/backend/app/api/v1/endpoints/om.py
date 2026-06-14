from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin, require_reader
from app.models.user import User
from app.schemas.common import RegistroOMCreate, RegistroOMResponse, RegistroOMUpdate
from app.services.om_service import OMService

router = APIRouter()
_om_service = OMService()


@router.get("", response_model=list[RegistroOMResponse])
async def list_om(
    anio: int | None = Query(None),
    periodo: str | None = Query(None),
    _user: User = Depends(require_reader),
    db: AsyncSession = Depends(get_db),
) -> list[RegistroOMResponse]:
    registros = await _om_service.list_registros(db, anio=anio, periodo=periodo)
    return registros


@router.post("", response_model=RegistroOMResponse, status_code=status.HTTP_201_CREATED)
async def create_om(
    data: RegistroOMCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RegistroOMResponse:
    data.registrado_por = user.email
    return await _om_service.create(db, data)


@router.put("/{registro_id}", response_model=RegistroOMResponse)
async def update_om(
    registro_id: int,
    data: RegistroOMUpdate,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RegistroOMResponse:
    registro = await _om_service.update(db, registro_id, data)
    if registro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
    return registro


@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_om(
    registro_id: int,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await _om_service.delete(db, registro_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
