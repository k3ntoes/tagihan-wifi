from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.sqids_manager import SqidsManager
from app.models.base import BasePageableModel, BasePageRequest
from app.models.paket import PaketModelHelper, PaketModel, PaketResponse


class PelangganModel(BaseModel):
    id: int
    nama: str
    alamat: str
    no_hp: str
    paket: PaketModel
    created_at: datetime
    updated_at: datetime

class PelangganMiniResponse(BaseModel):
    id: str
    nama: str

class PelangganResponse(PelangganMiniResponse):
    paket: PaketResponse
    created_at: datetime
    updated_at: datetime

class PelangganPageableModel(BasePageableModel):
    content: list[PelangganResponse]

class PelangganRequest(BasePageRequest):
    nama: Optional[str]=None
    paket_id: Optional[int]=None

class PelangganPostRequest(BaseModel):
    nama: str
    alamat: str
    no_hp: str
    paket_id: int

class PelangganModelHelper:
    def __init__(self):
        self.sqids=SqidsManager()
        self.paket_helper=PaketModelHelper()


    def map_to_model(self, row: dict) -> PelangganResponse:
            """Map database row to PelangganModel."""
            if not row:
                return None
                
            # Extract paket data from the joined row
            paket_data = {
                "id": row.get("paket_id"),
                "nama": row.get(
                    "nama_paket"
                ),  # assuming the column is named 'nama_paket' in the result
                "harga": row.get("harga"),
                "kecepatan": row.get("kecepatan"),
                "created_at": row.get("paket_created_at"),
                "updated_at": row.get("paket_updated_at"),
            }
            
            # Create PaketModel instance
            paket = self.paket_helper.map_to_model(paket_data)
            
            # Create PelangganModel with the nested PaketModel
            pelanggan_id=self.sqids.encode(row.get("id"))
            pelanggan_data = {
                "id": f"pel_{pelanggan_id}",
                "nama": row.get("nama"),
                "alamat": row.get("alamat"),
                "no_hp": row.get("no_hp"),
                "paket": paket,
                "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            return PelangganResponse(**pelanggan_data)