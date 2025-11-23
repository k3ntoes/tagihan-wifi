from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.sqids_manager import SqidsManager
from app.models.base import BasePageableModel, BasePageRequest
from app.models.paket import PaketHelper, PaketModel, PaketResponse


class PelangganModel(BaseModel):
    id: int
    nama: str
    alamat: str
    no_hp: str
    paket: PaketModel
    created_at: datetime
    updated_at: datetime

class PelangganResponse(PelangganModel):
    id: str
    paket: PaketResponse
    created_at: str
    updated_at: str

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
        self.paket_helper=PaketHelper()


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
            pelanggan_data = {
                "id": self.sqids.encode(row.get("id")),
                "nama": row.get("nama"),
                "alamat": row.get("alamat"),
                "no_hp": row.get("no_hp"),
                "paket": paket,
                "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            return PelangganResponse(**pelanggan_data)
    
    def map_from_tuple(self, row: tuple) -> PelangganResponse:
        if not row:
            raise ValueError("Invalid row format")
        try:
            created_at = row[6]
            updated_at = row[7]
            
            if not isinstance(created_at, (datetime, str)):
                raise ValueError("Invalid created_at format")
            if not isinstance(updated_at, (datetime, str)):
                raise ValueError("Invalid updated_at format")
                
            if isinstance(created_at, datetime):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at_str = str(created_at)
                
            if isinstance(updated_at, datetime):
                updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                updated_at_str = str(updated_at)

            pelanggan_data = {
                "id": self.sqids.encode(row[0]),
                "nama": row[1],
                "alamat": row[2],
                "no_hp": row[3],
                "paket": self.paket_helper.map_from_tuple(
                    (row[4], row[7], row[8], row[9], row[10], row[11])
                ),
                "created_at": created_at_str,
                "updated_at": updated_at_str,
            }
            return PelangganResponse(**pelanggan_data)
        except Exception as e:
            raise ValueError(f"Error mapping row to PelangganResponse: {e}")