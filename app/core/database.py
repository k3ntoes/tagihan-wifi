from typing import Generator

import duckdb

from app.core.config import LOGGER, Settings

con=duckdb.connect(Settings().database_path)

def init_db():
    with con.cursor() as cursor:
        cursor.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_paket START 1 INCREMENT 1;
            CREATE SEQUENCE IF NOT EXISTS seq_pelanggan START 1 INCREMENT 1;
            CREATE SEQUENCE IF NOT EXISTS seq_tagihan START 1 INCREMENT 1;
        """)
        LOGGER.info("Sequences created")
        cursor.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paket (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_paket'),
                nama TEXT NOT NULL,
                harga INTEGER NOT NULL,
                kecepatan VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (nama, kecepatan)
            );
        """)
        LOGGER.info("Table paket created")
        cursor.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pelanggan (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_pelanggan'),
                nama TEXT NOT NULL,
                alamat TEXT NOT NULL,
                no_hp TEXT NOT NULL,
                paket_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paket_id) REFERENCES paket(id),
                UNIQUE (nama, paket_id)
            );
        """)
        LOGGER.info("Table pelanggan created")
        cursor.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tagihan (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_tagihan'),
                pelanggan_id INTEGER NOT NULL,
                paket_id INTEGER NOT NULL,
                periode VARCHAR(6) NOT NULL,
                tanggal_bayar DATE,
                status VARCHAR(20) DEFAULT 'BELUM BAYAR',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pelanggan_id) REFERENCES pelanggan(id),
                FOREIGN KEY (paket_id) REFERENCES paket(id),
                UNIQUE (periode, pelanggan_id)
            );
        """)
        LOGGER.info("Table tagihan created")
        cursor.commit()

        cursor.execute("""
            INSERT INTO paket (nama, harga, kecepatan) FROM
            VALUES ('Paket 1', 50000, '5Mbps'),
                   ('Paket 2', 100000, '10Mbps') AS t(nama, harga, kecepatan)
            ON CONFLICT DO NOTHING;
        """)
        LOGGER.info("Initial data paket inserted")
        cursor.commit()

        cursor.execute("""
            INSERT INTO pelanggan (nama, alamat, no_hp, paket_id)
            FROM VALUES ('Pelanggan 1', 'Alamat 1', '1234567890', 1),
                   ('Pelanggan 2', 'Alamat 2', '0987654321', 2)
            AS t(nama, alamat, no_hp, paket_id)
            ON CONFLICT DO NOTHING;
        """)
        LOGGER.info("Initial data pelanggan inserted")
        cursor.commit()
        

def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    db = con.cursor()
    try:
        yield db
    finally:
        db.close()