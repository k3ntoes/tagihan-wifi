# Tambahkan API Paket
update aplikasi untuk mendukung manajemen paket layanan internet.
Fitur yang harus ditambahkan:
1. **Model Paket Baru**:
   - Buat model database baru bernama `Package` dengan field berikut:
     - `id`: Primary Key, Integer, Auto-increment
     - `name`: String, nama paket (misal: "Basic", "Premium")
     - `speed`: Integer, kecepatan paket dalam Mbps
     - `price`: Integer, harga paket dalam Rupiah
2. **Relasi Pelanggan dan Paket**:
   - Tambahkan field `package_id` pada model `Customer` sebagai Foreign Key yang mengacu pada `Package.id`.
3. **Endpoint CRUD untuk Paket**:
   - Buat endpoint API berikut untuk mengelola paket:
     - `POST /packages`: Menambahkan paket baru (hanya untuk admin)
     - `GET /packages`: Mendapatkan daftar semua paket
     - `GET /packages/{id}`: Mendapatkan detail paket berdasarkan ID
     - `PUT /packages/{id}`: Memperbarui detail paket (hanya untuk admin)
     - `DELETE /packages/{id}`: Menghapus paket (hanya untuk admin)
4. **Validasi dan Error Handling**:
   - Pastikan semua input divalidasi dengan benar menggunakan Pydantic.
   - Tangani error seperti paket tidak ditemukan atau pelanggaran constraint foreign key.
5. **Integrasi dengan Pembayaran**:
   - Saat mencatat pembayaran, pastikan untuk memeriksa paket pelanggan dan menyesuaikan jumlah pembayaran sesuai dengan harga paket yang dipilih.
6. **Dokumentasi**:
   - Perbarui dokumentasi API untuk mencakup endpoint baru dan perubahan pada model `Customer`.
Pastikan semua perubahan diuji dengan unit test yang sesuai.endpoints/
│   ├── auth.py
│   ├── customers.py
│   ├── payments.py
│   ├── billing.py
│   └── packages.py      ← Paket endpoints baru
├── core/
│   ├── config.py
│   └── auth.py
├── db/
│   ├── database.py      ← Table Package baru
│   └── models.py        ← Model Package baru ditambahkan di sini
├── schemas/
│   ├── __init__.py
│   ├── customer_schemas.py ← Tambahkan package_id di sini
│   ├── payment_schemas.py
│   └── package_schemas.py ← Skema Pydantic untuk Package baru
└── utils/
    └── ...
    └── sqids_helper.py
```
