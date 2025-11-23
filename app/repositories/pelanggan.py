from duckdb import DuckDBPyConnection
from fastapi import HTTPException

from app.core.pagination import FilterType, PaginationHandler
from app.models.pelanggan import (
    PelangganModel,
    PelangganModelHelper,
    PelangganPostRequest,
    PelangganRequest,
)


class PelangganRepository:
    def __init__(self):
        self.base_select = """
            SELECT 
                p.*,
                pk.nama as nama_paket,
                pk.harga,
                pk.kecepatan,
                pk.created_at as paket_created_at,
                pk.updated_at as paket_updated_at
            FROM pelanggan p
            JOIN paket pk ON p.paket_id = pk.id
        """
        self.pelanggan_model_helper = PelangganModelHelper()
        
        # Initialize pagination handler
        self.paginator = PaginationHandler(
            base_query=self.base_select,
            count_query="SELECT COUNT(*) as count FROM pelanggan p",
            model_class=PelangganModel,
            map_function=self.pelanggan_model_helper.map_to_model,
            default_sort="p.nama",
            default_direction="ASC"
        )

    def get_page(self, db: DuckDBPyConnection, req: PelangganRequest):
        """
        Get a paginated list of pelanggan with their associated paket data.
        
        Args:
            req: PelangganRequest containing pagination and filtering parameters
            
        Returns:
            PelangganPageableModel containing paginated results and metadata
        """
        # Convert request to pagination parameters
        return self.paginator.get_page(
            db=db, page=req.page, size=req.size, sort=req.sort, direction=req.direction,
            nama=FilterType(field="p.nama", value=req.nama, operator="ILIKE"),
            paket_id=FilterType(field="p.paket_id", value=req.paket_id, operator="=")
        )
        
    def get_by_id(self, db: DuckDBPyConnection, id: int):
        """Get a single pelanggan by ID with associated paket data."""
        try:
            query = self.base_select + "WHERE p.id = ?"
            row = db.execute(query, (id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Pelanggan not found")
            return self.pelanggan_model_helper.map_from_tuple(row)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create(self, db: DuckDBPyConnection, req: PelangganPostRequest):
        try:
            query = "INSERT INTO pelanggan (nama, alamat, paket_id) VALUES (?, ?, ?)"
            params = (req.nama, req.alamat, req.paket_id)
            db.execute(query, params)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def update(self, db: DuckDBPyConnection, id: int, req: PelangganPostRequest):
        try:
            exist=self.get_by_id(db, id)
            if not exist:
                raise HTTPException(status_code=404, detail="Pelanggan not found")
            query = "UPDATE pelanggan SET nama=?, alamat=?, paket_id=? WHERE id=?"
            params = (req.nama, req.alamat, req.paket_id, id)
            db.execute(query, params)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def delete(self, db: DuckDBPyConnection, id: int):
        try:
            exist=self.get_by_id(db, id)
            if not exist:
                raise HTTPException(status_code=404, detail="Pelanggan not found")
            query = "DELETE FROM pelanggan WHERE id=?"
            params = (id,)
            db.execute(query, params)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        