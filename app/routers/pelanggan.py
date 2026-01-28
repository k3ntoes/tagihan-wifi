from typing import Annotated

from duckdb import DuckDBPyConnection
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.database import get_db
from app.core.rbac import require_admin
from app.core.sqids_manager import SqidsManager
from app.models.pelanggan import PelangganPostRequest, PelangganRequest
from app.models.user import UserInDB
from app.repositories.pelanggan import PelangganRepository

router = APIRouter(tags=["Pelanggan"], prefix="/pelanggan")


@router.get("")
def get_all(
    request: Annotated[PelangganRequest, Query()],
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[DuckDBPyConnection, Depends(get_db)],
    repo: PelangganRepository = Depends(PelangganRepository),
):
    data = repo.get_page(db, request)
    if data:
        return data
    raise HTTPException(status_code=404, detail="Data not found")


@router.get("/{id}")
def get_by_id(
    id: str,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[DuckDBPyConnection, Depends(get_db)],
    repo: PelangganRepository = Depends(PelangganRepository),
    sqids: SqidsManager = Depends(),
):
    if not sqids.decode(id.split("_")[-1]):
        raise HTTPException(status_code=404, detail="Data not found")
    data = repo.get_by_id(db, sqids.decode(id.split("_")[-1]))
    if data:
        return data
    raise HTTPException(status_code=404, detail="Data not found")


@router.post("", status_code=201)
def create(
    req: PelangganPostRequest,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[DuckDBPyConnection, Depends(get_db)],
    repo: PelangganRepository = Depends(PelangganRepository),
):
    repo.create(db, req)
    return JSONResponse(status_code=201,content={"message": "Data created successfully"})


@router.put("/{id}")
def update(
    id: str,
    req: PelangganPostRequest,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[DuckDBPyConnection, Depends(get_db)],
    repo: PelangganRepository = Depends(PelangganRepository),
    sqids: SqidsManager = Depends(),
):
    if not sqids.decode(id.split("_")[-1]):
        raise HTTPException(status_code=404, detail="Data not found")
    repo.update(db, sqids.decode(id.split("_")[-1]), req)
    return JSONResponse(content={"message": "Data updated successfully"}, status_code=200)


@router.delete("/{id}")
def delete(
    id: str,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[DuckDBPyConnection, Depends(get_db)],
    repo: PelangganRepository = Depends(PelangganRepository),
    sqids: SqidsManager = Depends(),
):
    if not sqids.decode(id.split("_")[-1]):
        raise HTTPException(status_code=404, detail="Data not found")
    repo.delete(db, sqids.decode(id.split("_")[-1]))
    return JSONResponse(content={"message": "Data deleted successfully"})
