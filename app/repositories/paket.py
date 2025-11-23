from duckdb import DuckDBPyConnection
from fastapi import HTTPException

from app.core.config import LOGGER
from app.core.pagination import FilterType, PaginationHandler
from app.models.paket import PaketHelper, PaketModel, PaketPostRequest, PaketRequest


class PaketRepository:
    def __init__(self):
        self.base_select = "SELECT * FROM paket"
        self.paket_helper = PaketHelper()
        self.paginator = PaginationHandler(
            base_query=self.base_select,
            count_query="SELECT COUNT(*) as count FROM paket",
            model_class=PaketModel,
            map_function=self.paket_helper.map_to_model,
            default_sort="paket.nama",
            default_direction="ASC",
        )

    def get_page(self, db: DuckDBPyConnection, req: PaketRequest):
        return self.paginator.get_page(
            db=db,
            page=req.page,
            size=req.size,
            sort=req.sort,
            direction=req.direction,
            nama=FilterType(field="paket.nama", value=req.nama, operator="ILIKE"),
            kecepatan=FilterType(field="paket.kecepatan", value=req.kecepatan, operator="ILIKE"),
        )

    def create(self, db: DuckDBPyConnection, req: PaketPostRequest):
        try:
            query = "INSERT INTO paket (nama, harga, kecepatan) VALUES (?, ?, ?)"
            params = (req.nama, req.harga, req.kecepatan)
            db.execute(query, params)
            db.commit()
        except Exception as e:
            db.rollback()
            LOGGER.error(f"Error creating paket: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def get_by_id(self, db: DuckDBPyConnection, id: int):
        try:
            query = "SELECT * FROM paket WHERE id=?"
            params = (id,)
            result=db.execute(query, params).fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Paket not found")
            return self.paket_helper.map_from_tuple(result)
        except HTTPException as e:
            raise e
        except Exception as e:
            LOGGER.error(f"Error getting paket by id: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def update(self, db: DuckDBPyConnection, id: int, req: PaketPostRequest) -> bool:
        try:
            exist=self.get_by_id(db, id)
            if not exist:
                raise HTTPException(status_code=404, detail="Paket not found")
            query = "UPDATE paket SET nama=?, harga=?, kecepatan=? WHERE id=?"
            params = (req.nama, req.harga, req.kecepatan, id)
            db.execute(query, params)
            db.commit()
        except HTTPException as e:
            raise e
        except Exception as e:
            db.rollback()
            LOGGER.error(f"Error updating paket: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def delete(self, db: DuckDBPyConnection, id: int) -> bool:
        try:
            exist = self.get_by_id(db, id)
            if not exist:
                raise HTTPException(status_code=404, detail="Paket not found")

            query = "DELETE FROM paket WHERE id=?"
            params = (id,)
            db.execute(query, params)
            db.commit()
        except HTTPException as e:
            raise e
        except Exception as e:
            db.rollback()
            LOGGER.error(f"Error deleting paket: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
