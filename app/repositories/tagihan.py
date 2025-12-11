import secrets

import duckdb
from fastapi import HTTPException

from app.core import PaginationHandler
from app.core.config import LOGGER
from app.core.pagination import FilterType
from app.core.sqids_manager import SqidsManager
from app.models.tagihan import (
    TagihanModelHelper,
    TagihanModel,
    TagihanRequest,
    TagihanPostRequest,
)


class TagihanRepository:
    def __init__(self):
        self.base_select = """
                           SELECT t.id            AS id,
                                  t.tahun         AS tahun,
                                  t.bulan         AS bulan,
                                  t.pelanggan_id  AS pelanggan_id,
                                  p.nama          AS nama_pelanggan,
                                  t.paket_id      AS paket_pelanggan,
                                  pk.nama         AS nama_paket,
                                  pk.kecepatan    AS kecepatan,
                                  pk.harga        as harga,
                                  t.tanggal_bayar AS tanggal_bayar,
                                  t.created_at    as created_at,
                                  t.updated_at    as updated_at
                           FROM tagihan t
                                    JOIN pelanggan p ON t.pelanggan_id = p.id
                                    JOIN paket pk ON t.paket_id = pk.id
                           """
        self.model = TagihanModelHelper()

        self.paginator = PaginationHandler(
            base_query=self.base_select,
            count_query="""
                        SELECT COUNT(*)
                        FROM tagihan t
                                 JOIN pelanggan p ON t.pelanggan_id = p.id
                                 JOIN paket pk ON t.paket_id = pk.id
                        """,
            model_class=TagihanModel,
            map_function=self.model.map_to_model,
            default_sort="t.tanggal_bayar",
            default_direction="DESC",
        )

    def get_page(self, db: duckdb.DuckDBPyConnection, req: TagihanRequest):
        return self.paginator.get_page(
            db=db,
            page=req.page,
            size=req.size,
            sort=req.sort,
            direction=req.direction,
            tahun=FilterType(field="t.tahun", value=req.tahun),
            bulan=FilterType(field="t.bulan", value=req.bulan),
            pelanggan_id=FilterType(field="p.pelanggan_id", value=req.pelanggan_id),
            paket_id=FilterType(field="p.paket_id", value=req.paket_id),
        )

    def get_page_by_pelanggan(
        self, db: duckdb.DuckDBPyConnection, req: TagihanRequest, pelanggan_id: int
    ):
        """Get paginated tagihan filtered by pelanggan_id for USER role."""
        return self.paginator.get_page(
            db=db,
            page=req.page,
            size=req.size,
            sort=req.sort,
            direction=req.direction,
            tahun=FilterType(field="t.tahun", value=req.tahun),
            bulan=FilterType(field="t.bulan", value=req.bulan),
            pelanggan_id=FilterType(
                field="t.pelanggan_id", value=pelanggan_id
            ),  # Force filter
            paket_id=FilterType(field="p.paket_id", value=req.paket_id),
        )

    def fetch_by_id(self, id: int, db: duckdb.DuckDBPyConnection):
        query = """
                SELECT t.id            AS id,
                       t.tahun         AS tahun,
                       t.bulan         AS bulan,
                       t.pelanggan_id  AS pelanggan_id,
                       p.nama          AS nama_pelanggan,
                       t.paket_id      AS paket_pelanggan,
                       pk.nama         AS nama_paket,
                       pk.kecepatan    AS kecepatan,
                       pk.harga        as harga,
                       t.tanggal_bayar AS tanggal_bayar,
                       t.created_at    as created_at,
                       t.updated_at    as updated_at
                FROM tagihan t
                         JOIN pelanggan p ON t.pelanggan_id = p.id
                         JOIN paket pk ON t.paket_id = pk.id
                WHERE t.id = ?
                """
        params = (id,)
        try:
            cursor = db.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            row = dict(zip(columns, cursor.fetchone()))
            return self.model.map_to_model(row)
        except Exception as e:
            LOGGER.error(e)
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def save(
        db: duckdb.DuckDBPyConnection, req: TagihanPostRequest, sqids: SqidsManager
    ):
        query = """
                INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, tanggal_bayar)
                FROM VALUES (?, ?, ?, ?) AS t(pelanggan_id, paket_id, periode, tanggal_bayar)
                ON CONFLICT (pelanggan_id, periode) DO NOTHING;
                """
        params = (
            sqids.decode(req.pelanggan_id),
            sqids.decode(req.paket_id),
            req.periode,
            req.tanggal_bayar.strftime("%Y-%m-%d"),
        )
        try:
            db.execute(query, params)
            db.commit()
            LOGGER.info(params)
            LOGGER.info("saved")
        except Exception as e:
            db.rollback()
            LOGGER.error(e)
            raise HTTPException(status_code=400, detail="Internal Server Error")

    @staticmethod
    def update(
        db: duckdb.DuckDBPyConnection,
        id: int,
        req: TagihanPostRequest,
        sqids: SqidsManager,
    ):
        query = """
                UPDATE tagihan
                SET pelanggan_id=?,
                    paket_id=?,
                    tahun=?,
                    bulan=?,
                    tanggal_bayar=?
                WHERE id = ?
                """
        params = (
            sqids.decode(req.pelanggan_id),
            sqids.decode(req.paket_id),
            req.tahun,
            req.bulan,
            req.tanggal_bayar.strftime("%Y-%m-%d"),
            id,
        )
        try:
            db.execute(query, params)
            db.commit()
        except Exception as e:
            db.rollback()
            LOGGER.error(e)
            raise HTTPException(status_code=400, detail="Internal Server Error")

    @staticmethod
    def delete(id: int, db: duckdb.DuckDBPyConnection):
        exist = db.execute("SELECT id FROM tagihan WHERE id=?", (id,)).fetchone()
        if not exist:
            raise HTTPException(status_code=404, detail="Tagihan Not Found")

        try:
            db.execute("DELETE FROM tagihan WHERE id=?", (id,))
            db.commit()
        except Exception as e:
            db.rollback()
            LOGGER.error(e)
            raise HTTPException(status_code=400, detail="Internal Server Error")

    def fetch_summary(
        self, tahun: str, db: duckdb.DuckDBPyConnection, sqids: SqidsManager
    ):
        query = """
                SELECT *
                FROM tagihan
                WHERE tahun = ?
                """
        params = (tahun,)
        try:
            cursor = db.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            items = [dict(zip(columns, row)) for row in rows]
            sqids_salt = secrets.randbelow(1_000)
            result = [
                {
                    "id": sqids.encode(item["id"], salt=sqids_salt),
                    "pelanggan_id": sqids.encode(item["pelanggan_id"], salt=sqids_salt),
                    "paket_id": sqids.encode(item["paket_id"], salt=sqids_salt),
                    "tahun": item["tahun"],
                    "bulan": item["bulan"],
                    "tanggal_bayar": item["tanggal_bayar"].strftime("%Y-%m-%d"),
                    "created_at": item["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": item["updated_at"].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for item in items
            ]
            return result
        except Exception as e:
            LOGGER.error(e)
            raise HTTPException(status_code=400, detail=str(e))

    def fetch_summary_by_pelanggan(
        self,
        tahun: str,
        db: duckdb.DuckDBPyConnection,
        sqids: SqidsManager,
        pelanggan_id: int,
    ):
        """Fetch summary filtered by pelanggan_id for USER role."""
        query = """
                SELECT *
                FROM tagihan
                WHERE tahun = ? AND pelanggan_id = ?
                """
        params = (tahun, pelanggan_id)
        try:
            cursor = db.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            items = [dict(zip(columns, row)) for row in rows]
            sqids_salt = secrets.randbelow(1_000)
            result = [
                {
                    "id": sqids.encode(item["id"], salt=sqids_salt),
                    "pelanggan_id": sqids.encode(item["pelanggan_id"], salt=sqids_salt),
                    "paket_id": sqids.encode(item["paket_id"], salt=sqids_salt),
                    "tahun": item["tahun"],
                    "bulan": item["bulan"],
                    "tanggal_bayar": item["tanggal_bayar"].strftime("%Y-%m-%d"),
                    "created_at": item["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": item["updated_at"].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for item in items
            ]
            return result
        except Exception as e:
            LOGGER.error(e)
            raise HTTPException(status_code=400, detail=str(e))
