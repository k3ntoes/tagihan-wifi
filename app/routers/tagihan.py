from typing import Annotated

import duckdb
from fastapi import APIRouter, Query, Depends, HTTPException, status
from starlette.responses import JSONResponse

from app.core.config import LOGGER
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.rbac import require_admin
from app.core.sqids_manager import SqidsManager
from app.models.enums import Role
from app.models.tagihan import TagihanRequest, TagihanPostRequest
from app.models.user import UserInDB
from app.repositories.tagihan import TagihanRepository

router = APIRouter(
    tags=["Tagihan"],
    prefix="/tagihan",
)


@router.get("")
async def get_tagihan(
    request: Annotated[TagihanRequest, Query()],
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
    repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
):
    # ADMIN sees all tagihan, USER sees only their own
    if current_user.role == Role.USER:
        # User must have pelanggan_id set
        if not current_user.pelanggan_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not linked to any pelanggan",
            )
        # Filter by user's pelanggan_id
        data = repo.get_page_by_pelanggan(db, request, current_user.pelanggan_id)
    else:
        # Admin sees all
        data = repo.get_page(db, request)

    if data is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return data


@router.get("/{id}", summary="Get Tagihan Pelanggan")
async def get_tagihan_by_id(
    id: str,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
    repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
    sqids: Annotated[SqidsManager, Depends(SqidsManager)],
):
    data = repo.fetch_by_id(sqids.decode(id), db)
    LOGGER.info(data)
    if data is None:
        raise HTTPException(status_code=404, detail="Tagihan not found")
    return data


@router.post("", summary="Input Tagihan Pelanggan")
async def input_tagihan(
    req: TagihanPostRequest,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
    repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
    sqids: Annotated[SqidsManager, Depends(SqidsManager)],
):
    repo.save(db, req, sqids)
    return JSONResponse(status_code=200, content={"message": "saved successfully"})


@router.put("/{id}", summary="Edit Tagihan Pelanggan")
async def edit_tagihan(
    id: str,
    req: TagihanPostRequest,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
    repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
    sqids: Annotated[SqidsManager, Depends(SqidsManager)],
):
    repo.update(db, sqids.decode(id), req, sqids)
    return JSONResponse(status_code=200, content={"message": "updated successfully"})


@router.delete("/{id}", summary="Delete Tagihan Pelanggan")
async def delete_tagihan(
    id: str,
    current_user: Annotated[UserInDB, Depends(require_admin)],
    db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
    repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
    sqids: Annotated[SqidsManager, Depends(SqidsManager)],
):
    repo.delete(sqids.decode(id), db)
    return JSONResponse(status_code=200, content={"message": "deleted successfully"})


@router.get("/summary/{tahun}", summary="Summary tagihan per tahun")
async def get_summary(
    tahun: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
    repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
    sqids: Annotated[SqidsManager, Depends(SqidsManager)],
):
    # ADMIN sees all tagihan summary, USER sees only their own
    if current_user.role == Role.USER:
        # User must have pelanggan_id set
        if not current_user.pelanggan_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not linked to any pelanggan",
            )
        # Filter by user's pelanggan_id
        result = repo.fetch_summary_by_pelanggan(
            tahun, db, sqids, current_user.pelanggan_id
        )
    else:
        # Admin sees all
        result = repo.fetch_summary(tahun, db, sqids)

    return JSONResponse(status_code=200, content=result)
