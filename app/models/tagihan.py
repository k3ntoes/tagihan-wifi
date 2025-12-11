from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.core.sqids_manager import SqidsManager
from app.models.base import BasePageRequest
from app.models.paket import PaketModelHelper, PaketMiniResponse
from app.models.pelanggan import PelangganModelHelper, PelangganMiniResponse


class BaseTagihan(BaseModel):
    pelanggan_id: int
    paket_id: int
    tahun: int
    bulan: int
    tanggal_bayar: date


class TagihanModel(BaseTagihan):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagihanResponse(BaseModel):
    id: str
    pelanggan: PelangganMiniResponse
    paket: PaketMiniResponse
    tahun: int
    bulan: int
    tanggal_bayar: str
    created_at: str
    updated_at: str


now = datetime.now()


class TagihanRequest(BasePageRequest):
    tahun: int
    bulan: int
    pelanggan_id: Optional[int] = None
    paket_id: Optional[int] = None


class TagihanPostRequest(BaseModel):
    pelanggan_id: str
    paket_id: str
    tahun: int
    bulan: int
    tanggal_bayar: date


class TagihanModelHelper:
    def __init__(self, ):
        self.sqids = SqidsManager()
        self.pelanggan_helper = PelangganModelHelper()
        self.paket_helper = PaketModelHelper()

    def map_to_model(self, row: dict) -> Optional[TagihanResponse]:
        if not row:
            return None

        pelanggan = PelangganMiniResponse(
            id=self.sqids.encode(row.get("pelanggan_id")),
            nama=row.get("nama_pelanggan"),
        )

        paket = PaketMiniResponse(
            id=self.sqids.encode(row.get("pelanggan_id")),
            nama=row.get("nama_pelanggan"),
            kecepatan=row.get("kecepatan"),
            harga=row.get("harga"),
        )

        return TagihanResponse(
            id=self.sqids.encode(row.get('id')),
            tanggal_bayar=row.get('tanggal_bayar').strftime('%Y-%m-%d'),
            tahun=row.get("tahun"),
            bulan=row.get("bulan"),
            pelanggan=pelanggan,
            paket=paket,
            created_at=row.get('created_at').strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=row.get('updated_at').strftime('%Y-%m-%d %H:%M:%S'),
        )
