from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.database import get_db
from app.core.rbac import require_admin
from app.core.sqids_manager import SqidsManager
from app.models.paket import PaketPostRequest, PaketRequest
from app.models.user import UserInDB
from app.repositories.paket import PaketRepository

router = APIRouter(tags=["Paket"], prefix="/paket")


@router.get("", summary="Get all paket")
def get_all(
    req: Annotated[PaketRequest, Query()],
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: DuckDBPyConnection = Depends(get_db),
    repo: PaketRepository = Depends(PaketRepository),
):
    data = repo.get_page(db, req)
    return JSONResponse(content=data.model_dump())


@router.post("", summary="Create new paket")
def create(
    req: PaketPostRequest,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: DuckDBPyConnection = Depends(get_db),
    repo: PaketRepository = Depends(PaketRepository),
):
    try:
        repo.create(db, req)
        return JSONResponse(
            content={"message": "Paket created successfully"}, status_code=201
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"errors": e.detail})


@router.get("/{id}", summary="Get paket by id")
def get_by_id(
    id: str,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: DuckDBPyConnection = Depends(get_db),
    repo: PaketRepository = Depends(PaketRepository),
    sqids: SqidsManager = Depends(SqidsManager),
):
    try:
        if not sqids.decode(id):
            raise HTTPException(status_code=404, detail="Paket not found")
        data = repo.get_by_id(db, sqids.decode(id))
        return JSONResponse(content=data.model_dump())
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"errors": e.detail})


@router.put("/{id}", summary="Update paket")
def update(
    id: str,
    req: PaketPostRequest,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: DuckDBPyConnection = Depends(get_db),
    repo: PaketRepository = Depends(PaketRepository),
    sqids: SqidsManager = Depends(SqidsManager),
):
    try:
        if not sqids.decode(id):
            raise HTTPException(status_code=404, detail="Paket not found")
        repo.update(db, sqids.decode(id), req)
        return JSONResponse(
            content={"message": "Paket updated successfully"}, status_code=200
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"errors": e.detail})


@router.delete("/{id}", summary="Delete paket")
def delete(
    id: str,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: DuckDBPyConnection = Depends(get_db),
    repo: PaketRepository = Depends(PaketRepository),
    sqids: SqidsManager = Depends(SqidsManager),
):
    try:
        if not sqids.decode(id):
            raise HTTPException(status_code=404, detail="Paket not found")
        repo.delete(db, sqids.decode(id))
        return JSONResponse(
            content={"message": "Paket deleted successfully"}, status_code=200
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"errors": e.detail})
