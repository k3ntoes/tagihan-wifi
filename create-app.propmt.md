# AI Prompt: Backend System for Wifi Billing (FastAPI + DuckDB)

**Context:**
Saya ingin membangun sistem backend untuk manajemen tagihan WiFi pelanggan berdasarkan struktur data dari spreadsheet tahunan (2025-2026). Sistem ini akan mencatat pelanggan, tarif bulanan (tag), dan status pembayaran bulanan.

**Technical Stack:**
1. **Language:** Python
2. **Framework:** FastAPI
3. **Database:** DuckDB (untuk penyimpanan data relasional yang ringan namun kuat)
4. **ID Objek:** Sqids (untuk meng-encode Integer ID menjadi string pendek unik)
5. **Security:** JWT (JSON Web Token) dengan implementasi RBAC (Role-Based Access Control)
   - Roles: `admin` (Full access) & `user` (View only)

**Database Schema & Entities:**
1. **Customer Table:** - `id` (Primary Key)
   - `sqid` (Generated via Sqids)
   - `name` (String)
   - `monthly_fee` (Integer - mengacu pada kolom 'tag' di spreadsheet)
2. **Payment Table:**
   - `id` (Primary Key)
   - `customer_id` (Foreign Key)
   - `payment_date` (Date)
   - `billing_month` (1-12)
   - `billing_year` (Integer, e.g., 2025, 2026)
   - `amount` (Integer)

**Features & Requirements:**
1. **Authentication:** - Buat sistem Login yang menghasilkan JWT.
   - Gunakan RBAC: Hanya `admin` yang bisa menambah/mengedit data pembayaran dan pelanggan.
2. **Payment Processing:**
   - Buat endpoint untuk mencatat pembayaran. 
   - Sertakan fungsi parser untuk menangani input log manual seperti pada spreadsheet (Contoh: "02-05-2025 opi" menjadi tanggal bayar 2 Mei 2025, untuk pelanggan bernama 'opi').
3. **Billing Matrix API:** - Buat endpoint GET yang mengembalikan data dalam format matriks tahunan. 
   - Output harus menunjukkan status pembayaran Januari - Desember untuk setiap pelanggan di tahun tertentu.
4. **Integration:** - Gunakan DuckDB dalam mode *persistent storage* (file `.db`).
   - Gunakan Sqids untuk setiap ID yang diekspos di URL API (misal: `/customers/{sqid}`).

**Instructions for Code Generation:**
- Gunakan Pydantic untuk validasi data (Schemas).
- Implementasikan struktur project yang bersih (main.py, models.py, database.py, auth.py).
- Berikan contoh file `.env` untuk SECRET_KEY JWT.
- Sertakan komentar pada kode untuk menjelaskan logika integrasi DuckDB dan Sqids.