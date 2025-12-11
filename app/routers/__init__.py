from .paket import router as paket_router
from .pelanggan import router as pelanggan_router
from .tagihan import router as tagihan_router

__all__ = [
    "paket_router",
    "pelanggan_router",
    "tagihan_router"
]
