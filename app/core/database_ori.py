import threading
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional, Union, Iterator, Any

import duckdb
from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

DB_NAME = settings.database_path


class DuckDBConnectionPool:
    """Thread-safe connection pool untuk DuckDB dengan context manager."""
    
    def __init__(self, database_path: str, pool_size: int = 5):
        self.database_path = database_path
        self.pool_size = pool_size
        self.connections: List[duckdb.DuckDBPyConnection] = []
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Initialize connection pool dengan ukuran yang ditentukan."""
        for _ in range(self.pool_size):
            conn = duckdb.connect(database=self.database_path)
            # Optimasi konfigurasi DuckDB
            conn.execute("PRAGMA threads=4")
            conn.execute("PRAGMA memory_limit='1GB'")
            self.connections.append(conn)

    @contextmanager
    def get_connection(self) -> Iterator[duckdb.DuckDBPyConnection]:
        """Context manager untuk mendapatkan koneksi dari pool."""
        conn = None
        try:
            with self.lock:
                if self.connections:
                    conn = self.connections.pop()
                else:
                    # Buat koneksi baru jika pool kosong
                    logger.warning("Connection pool exhausted, creating new connection")
                    conn = duckdb.connect(database=self.database_path)
                    conn.execute("PRAGMA threads=4")
            
            yield conn
        except Exception as e:
            logger.error(f"Error with database connection: {e}")
            if conn:
                conn.close()  # Tutup koneksi yang error
            raise
        finally:
            # Kembalikan koneksi ke pool
            if conn:
                try:
                    # Cek apakah ada transaksi aktif sebelum rollback
                    try:
                        result = conn.execute("SELECT current_setting('transaction_state')").fetchone()
                        if result and result[0] == 'in_transaction':
                            try:
                                conn.execute("ROLLBACK")
                            except Exception as e:
                                logger.debug(f"Rollback not needed or failed: {e}")
                    except Exception as e:
                        logger.debug(f"Could not check transaction state: {e}")
                    
                    with self.lock:
                        if len(self.connections) < self.pool_size:
                            # Coba eksekusi query sederhana untuk memeriksa koneksi
                            try:
                                conn.execute("SELECT 1")
                                self.connections.append(conn)
                                return
                            except Exception as e:
                                logger.debug(f"Connection no longer valid, discarding: {e}")
                        
                        # Jika sampai di sini, koneksi tidak valid atau pool penuh
                        try:
                            conn.close()
                        except Exception as close_error:
                            logger.debug(f"Error while closing connection: {close_error}")
                            
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {e}")
                    try:
                        conn.close()
                    except Exception as close_error:
                        logger.debug(f"Error while closing connection: {close_error}")

    def close_all(self) -> None:
        """Tutup semua koneksi dalam pool."""
        with self.lock:
            while self.connections:
                conn = self.connections.pop()
                try:
                    conn.close()
                except Exception as e:
                    logger.debug(f"Error closing connection: {e}")
                finally:
                    # Pastikan koneksi dihapus dari pool meskipun close gagal
                    if conn in self.connections:
                        self.connections.remove(conn)
            self.connections.clear()


# Global connection pool instance
pool = DuckDBConnectionPool(settings.database_path, pool_size=3)


class DBHelper:
    """Helper class untuk operasi database dengan error handling yang lebih baik."""
    
    @staticmethod
    def _execute_with_connection(operation: str, func, *args, **kwargs) -> Any:
        """Helper method untuk mengeksekusi operasi database dengan connection pool."""
        try:
            with pool.get_connection() as conn:
                return func(conn, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            raise

    @staticmethod
    def fetch_data(query: str, params: Optional[Union[tuple, dict]] = None) -> List[Dict]:
        """Fetch multiple rows dari database."""
        def _fetch(conn: duckdb.DuckDBPyConnection) -> List[Dict]:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]
        
        return DBHelper._execute_with_connection("fetch_data", _fetch)

    @staticmethod
    def fetch_one(query: str, params: Optional[Union[tuple, dict]] = None) -> Optional[Dict]:
        """Fetch single row dari database."""
        def _fetch_one(conn: duckdb.DuckDBPyConnection) -> Optional[Dict]:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
                return None
        
        return DBHelper._execute_with_connection("fetch_one", _fetch_one)

    @staticmethod
    def execute(query: str, params: Optional[Union[tuple, dict]] = None) -> int:
        """Execute query (INSERT, UPDATE, DELETE) dan return rowcount."""
        def _execute(conn: duckdb.DuckDBPyConnection) -> int:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                conn.commit()
                return cursor.rowcount
        
        return DBHelper._execute_with_connection("execute", _execute)

    @staticmethod
    def execute_many(query: str, params: List[Union[tuple, dict]]) -> int:
        """Execute batch query dan return total rowcount."""
        def _execute_many(conn: duckdb.DuckDBPyConnection) -> int:
            with conn.cursor() as cursor:
                cursor.executemany(query, params)
                conn.commit()
                return cursor.rowcount
        
        return DBHelper._execute_with_connection("execute_many", _execute_many)

    @staticmethod
    def execute_script(script: str) -> bool:
        """Execute SQL script."""
        def _execute_script(conn: duckdb.DuckDBPyConnection) -> bool:
            with conn.cursor() as cursor:
                cursor.execute(script)
                conn.commit()
                return True
        
        return DBHelper._execute_with_connection("execute_script", _execute_script)


class DatabaseInitializer:
    """Class untuk inisialisasi database dan data awal."""
    
    def __init__(self) -> None:
        self.initial_data_paket = [
            {"nama": "Paket 1", "harga": 50000, "kecepatan": "5Mbps"},
            {"nama": "Paket 2", "harga": 100000, "kecepatan": "10Mbps"},
        ]
        self.initial_data_pelanggan = [
            {
                "nama": "Pelanggan 1",
                "alamat": "Alamat 1",
                "no_hp": "1234567890",
                "paket_id": 1,
            },
            {
                "nama": "Pelanggan 2",
                "alamat": "Alamat 2",
                "no_hp": "0987654321",
                "paket_id": 2,
            },
        ]

    def initialize(self) -> bool:
        """Initialize semua tabel dan data."""
        try:
            logger.info("Starting database initialization...")
            
            self._create_sequences()
            self._create_paket_table()
            self._create_pelanggan_table()
            self._create_tagihan_table()
            
            self._insert_initial_data()
            
            logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    def _create_sequences(self) -> None:
        """Create sequences untuk primary keys."""
        sequences = [
            "CREATE SEQUENCE IF NOT EXISTS seq_paket START 1 INCREMENT 1;",
            "CREATE SEQUENCE IF NOT EXISTS seq_pelanggan START 1 INCREMENT 1;",
            "CREATE SEQUENCE IF NOT EXISTS seq_tagihan START 1 INCREMENT 1;"
        ]
        
        for seq in sequences:
            DBHelper.execute_script(seq)

    def _create_paket_table(self) -> None:
        """Create table paket."""
        script = """
        CREATE TABLE IF NOT EXISTS paket (
            id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_paket'),
            nama TEXT NOT NULL,
            harga INTEGER NOT NULL,
            kecepatan VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (nama, kecepatan)
        );
        """
        DBHelper.execute_script(script)

    def _create_pelanggan_table(self) -> None:
        """Create table pelanggan."""
        script = """
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
        """
        DBHelper.execute_script(script)

    def _create_tagihan_table(self) -> None:
        """Create table tagihan."""
        script = """
        CREATE TABLE IF NOT EXISTS tagihan (
            id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_tagihan'),
            pelanggan_id INTEGER NOT NULL,
            paket_id INTEGER NOT NULL,
            periode VARCHAR(6) NOT NULL,
            tanggal_bayar DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pelanggan_id) REFERENCES pelanggan(id),
            FOREIGN KEY (paket_id) REFERENCES paket(id),
            UNIQUE (periode, pelanggan_id)
        );
        """
        DBHelper.execute_script(script)

    def _insert_initial_data(self) -> None:
        """Insert data awal."""
        # Insert paket
        paket_query = """
        INSERT INTO paket (nama, harga, kecepatan)
        VALUES (?, ?, ?) 
        ON CONFLICT (nama, kecepatan) DO NOTHING;
        """
        paket_params = [(p["nama"], p["harga"], p["kecepatan"]) 
                       for p in self.initial_data_paket]
        DBHelper.execute_many(paket_query, paket_params)
        
        # Insert pelanggan
        pelanggan_query = """
        INSERT INTO pelanggan (nama, alamat, no_hp, paket_id)
        VALUES (?, ?, ?, ?) 
        ON CONFLICT (nama, paket_id) DO NOTHING;
        """
        pelanggan_params = [(p["nama"], p["alamat"], p["no_hp"], p["paket_id"]) 
                          for p in self.initial_data_pelanggan]
        DBHelper.execute_many(pelanggan_query, pelanggan_params)


# Fungsi utilitas untuk shutdown yang clean
def shutdown_database() -> None:
    """Clean shutdown database connections."""
    logger.info("Shutting down database connections...")
    pool.close_all()


# Backward compatibility
InitialDatabase = DatabaseInitializer