from typing import Annotated

import duckdb
from fastapi import APIRouter, Query, Depends, HTTPException
from starlette.responses import JSONResponse

from app.core.config import LOGGER
from app.core.database import get_db
from app.core.sqids_manager import SqidsManager
from app.models.tagihan import TagihanRequest, TagihanPostRequest
from app.repositories.tagihan import TagihanRepository

router = APIRouter(
    tags=["Tagihan"],
    prefix="/tagihan",
)


@router.get("")
async def get_tagihan(
        request: Annotated[TagihanRequest, Query()],
        db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
        repo: Annotated[TagihanRepository, Depends(TagihanRepository)]
):
    data = repo.get_page(db, request)
    if data is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return data


@router.get("/{id}", summary="Get Tagihan Pelanggan")
async def get_tagihan(
        id: str,
        db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
        repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
        sqids: Annotated[SqidsManager, Depends(SqidsManager)]
):
    data = repo.fetch_by_id(sqids.decode(id), db)
    LOGGER.info(data)
    if data is None:
        raise HTTPException(status_code=404, detail="Tagihan not found")
    return data


@router.post("", summary="Input Tagihan Pelanggan")
async def input_tagihan(
        req: TagihanPostRequest,
        db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
        repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
        sqids: Annotated[SqidsManager, Depends(SqidsManager)]
):
    repo.save(db, req, sqids)
    return JSONResponse(status_code=200, content={"message": "saved successfully"})


@router.put("/{id}", summary="Edit Tagihan Pelanggan")
async def edit_tagihan(
        id: str,
        req: TagihanPostRequest,
        db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
        repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
        sqids: Annotated[SqidsManager, Depends(SqidsManager)]
):
    repo.update(db, sqids.decode(id), req, sqids)
    return JSONResponse(status_code=200, content={"message": "updated successfully"})


@router.delete("/{id}", summary="Delete Tagihan Pelanggan")
async def delete_tagihan(
        id: str,
        db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
        repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
        sqids: Annotated[SqidsManager, Depends(SqidsManager)]
):
    repo.delete(sqids.decode(id), db)
    return JSONResponse(status_code=200, content={"message": "deleted successfully"})


@router.get("/summary/{tahun}", summary="Summary tagihan per tahun")
async def get_summary(
        tahun: str,
        db: Annotated[duckdb.DuckDBPyConnection, Depends(get_db)],
        repo: Annotated[TagihanRepository, Depends(TagihanRepository)],
        sqids: Annotated[SqidsManager, Depends(SqidsManager)]
):
    result = repo.fetch_summary(tahun, db,sqids)
    return JSONResponse(status_code=200, content=result)
