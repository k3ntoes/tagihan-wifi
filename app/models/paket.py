import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.sqids_manager import SqidsManager
from app.models.base import BasePageableModel, BasePageRequest


class BasePaket(BaseModel):
    nama: str
    harga: int
    kecepatan: str


class PaketModel(BasePaket):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class PaketMiniResponse(BaseModel):
    id: str
    nama: str
    harga: int
    kecepatan: str


class PaketResponse(PaketMiniResponse):
    created_at: str
    updated_at: str


class PaketPageableModel(BasePageableModel[PaketResponse]):
    content: list[PaketResponse]


class PaketRequest(BasePageRequest):
    nama: Optional[str] = None
    kecepatan: Optional[str] = None


class PaketPostRequest(BaseModel):
    nama: str
    harga: int
    kecepatan: str


class PaketModelHelper:
    def __init__(self):
        self.sqids = SqidsManager()

    def map_to_model(self, row: dict) -> Optional[PaketResponse]:
        if not row:
            return None

        try:
            created_at = row.get("created_at")
            updated_at = row.get("updated_at")

            if not isinstance(created_at, (datetime.datetime, str)):
                raise ValueError("Invalid created_at format")
            if not isinstance(updated_at, (datetime.datetime, str)):
                raise ValueError("Invalid updated_at format")

            if isinstance(created_at, datetime.datetime):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at_str = str(created_at)

            if isinstance(updated_at, datetime.datetime):
                updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                updated_at_str = str(updated_at)

            paket_data = {
                "id": self.sqids.encode(row.get("id")),
                "nama": row.get("nama"),
                "harga": row.get("harga"),
                "kecepatan": row.get("kecepatan"),
                "created_at": created_at_str,
                "updated_at": updated_at_str,
            }
            return PaketResponse(**paket_data)
        except Exception as e:
            raise ValueError(f"Error mapping row to PaketResponse: {e}")

    def map_from_tuple(self, row: tuple) -> Optional[PaketResponse]:
        if not row:
            return None
        try:
            created_at = row[4]
            updated_at = row[5]

            if not isinstance(created_at, (datetime.datetime, str)):
                raise ValueError("Invalid created_at format")
            if not isinstance(updated_at, (datetime.datetime, str)):
                raise ValueError("Invalid updated_at format")

            if isinstance(created_at, datetime.datetime):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at_str = str(created_at)

            if isinstance(updated_at, datetime.datetime):
                updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                updated_at_str = str(updated_at)

            paket_data = {
                "id": self.sqids.encode(row[0]),
                "nama": row[1],
                "harga": row[2],
                "kecepatan": row[3],
                "created_at": created_at_str,
                "updated_at": updated_at_str,
            }
            return PaketResponse(**paket_data)
        except Exception as e:
            raise ValueError(f"Error mapping row to PaketResponse: {e}")
