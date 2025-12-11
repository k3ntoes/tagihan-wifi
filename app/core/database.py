from typing import Generator

import duckdb

from app.core.config import LOGGER, settings

con = duckdb.connect(settings.database_path)


def init_db():
    with con.cursor() as cursor:
        cursor.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_paket START 1 INCREMENT 1;
            CREATE SEQUENCE IF NOT EXISTS seq_pelanggan START 1 INCREMENT 1;
            CREATE SEQUENCE IF NOT EXISTS seq_tagihan START 1 INCREMENT 1;
            CREATE SEQUENCE IF NOT EXISTS seq_users START 1 INCREMENT 1;
        """)
        LOGGER.info("Sequences created")
        cursor.commit()

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS paket
                       (
                           id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_paket'),
                           nama TEXT NOT NULL,
                           harga INTEGER NOT NULL,
                           kecepatan VARCHAR(50) NOT NULL,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           UNIQUE(nama, kecepatan)
                       );
                       """)
        LOGGER.info("Table paket created")
        cursor.commit()

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS pelanggan
                       (
                           id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_pelanggan'),
                           nama TEXT NOT NULL,
                           alamat TEXT NOT NULL,
                           no_hp TEXT NOT NULL,
                           paket_id INTEGER NOT NULL,
                           is_aktif BOOLEAN DEFAULT TRUE,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY(paket_id) REFERENCES paket (id),
                           UNIQUE(nama, paket_id)
                       );
                       """)
        LOGGER.info("Table pelanggan created")
        cursor.commit()

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_users'),
                           username VARCHAR(50) NOT NULL UNIQUE,
                           email VARCHAR(255) NOT NULL UNIQUE,
                           hashed_password TEXT NOT NULL,
                           is_active BOOLEAN DEFAULT TRUE,
                           is_superuser BOOLEAN DEFAULT FALSE,
                           role VARCHAR(20) DEFAULT 'USER',
                           pelanggan_id INTEGER,
                           reset_token VARCHAR(255),
                           reset_token_expires TIMESTAMP,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY(pelanggan_id) REFERENCES pelanggan(id)
                       );
                       """)
        LOGGER.info("Table users created")
        cursor.commit()

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS tagihan
                       (
                           id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_tagihan'),
                           pelanggan_id INTEGER NOT NULL,
                           paket_id INTEGER NOT NULL,
                           tahun INTEGER NOT NULL,
                           bulan INTEGER NOT NULL,
                           tanggal_bayar DATE,
                           nominal INTEGER,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY(pelanggan_id) REFERENCES pelanggan(id),
                           FOREIGN KEY(paket_id) REFERENCES paket(id),
                           UNIQUE(tahun, bulan, pelanggan_id)
                       );
                       """)
        LOGGER.info("Table tagihan created")
        cursor.commit()

        cursor.execute("""
                       INSERT INTO paket (nama, harga, kecepatan)
                       FROM VALUES ('Paket 1', 50000, '5Mbps'), ('Paket 2', 100000, '10Mbps') 
                       AS t(nama, harga, kecepatan)
                       ON CONFLICT DO NOTHING;
                       """)
        LOGGER.info("Initial data paket inserted")
        cursor.commit()

        cursor.execute("""
                       INSERT INTO pelanggan (nama, alamat, no_hp, paket_id)
                       FROM VALUES ('Pelanggan 1', 'Alamat 1', '1234567890', 1), ('Pelanggan 2', 'Alamat 2', '0987654321', 2)
                       AS t(nama, alamat, no_hp, paket_id)
                       ON CONFLICT DO NOTHING;
                       """)
        LOGGER.info("Initial data pelanggan inserted")
        cursor.commit()

        cursor.execute("""
                       INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, tanggal_bayar, nominal)
                       FROM VALUES (1,1,2025,9,'2025-09-15', 50000), (1,1,2025,10,'2025-10-15', 50000)
                       AS t(pelanggan_id, paket_id, tahun, bulan)
                       ON CONFLICT DO NOTHING;
                       """)
        LOGGER.info("Initial data tagihan inserted")
        cursor.commit()

        # Create default admin user
        from app.core.auth import get_password_hash

        admin_password_hash = get_password_hash("admin123")
        cursor.execute(
            """
                       INSERT INTO users (username, email, hashed_password, is_superuser, role)
                       FROM VALUES ('admin', 'admin@example.com', ?, TRUE, 'ADMIN')
                       AS t(username, email, hashed_password, is_superuser, role)
                       ON CONFLICT DO NOTHING;
                       """,
            [admin_password_hash],
        )
        LOGGER.info("Initial admin user created")
        cursor.commit()


def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    db = con.cursor()
    try:
        yield db
    finally:
        db.close()
