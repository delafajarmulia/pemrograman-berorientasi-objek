# setup_db_pengeluaran.py
import os
import sqlite3
import pandas as pd
from konfigurasi import DB_PATH  # Mengambil path database dari konfigurasi


def get_db_connection() -> sqlite3.Connection | None:
    """Membuka koneksi baru ke file database SQLite."""
    try:
        conn = sqlite3.connect(
            DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row  # Supaya data bisa diakses lewat nama kolom
        return conn
    except sqlite3.Error as e:
        print(f"ERROR [setup_db_pengeluaran.py] Koneksi DB gagal: {e}")
        return None


def setup_database():
    """FUNGSI DARI DOSEN: Membuat tabel transaksi jika belum ada."""
    print(f"Checking or reloading database at: {DB_PATH}")
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS transaksi(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deskripsi TEXT NOT NULL,
            jumlah REAL NOT NULL CHECK(jumlah > 0),
            kategori TEXT,
            tanggal DATE NOT NULL
        );
        """
        print("Creating table if not exists...")
        cursor.execute(sql_create_table)
        conn.commit()
        print("Database setup completed successfully.")
        return True
    except sqlite3.Error as e:
        print(f" -> Error sqlite while setup: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


def execute_query(query: str, params: tuple = None):
    """Menjalankan query INSERT / UPDATE / DELETE."""
    conn = get_db_connection()
    if not conn:
        return None
    last_id = None
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        last_id = cursor.lastrowid
        return last_id
    except sqlite3.Error as e:
        print(f"ERROR [setup_db_pengeluaran.py] Query gagal: {e}")
        conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def fetch_query(query: str, params: tuple = None, fetch_all: bool = True):
    """Menjalankan query SELECT biasa."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall() if fetch_all else cursor.fetchone()
        return result
    except sqlite3.Error as e:
        print(f"ERROR [setup_db_pengeluaran.py] Fetch gagal: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_dataframe(query: str, params: tuple = None) -> pd.DataFrame:
    """Menjalankan query SELECT dan mengubahnya jadi Pandas DataFrame."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        print(f"ERROR [setup_db_pengeluaran.py] Gagal baca ke DataFrame: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# Agar file ini bisa dijalankan mandiri via terminal
if __name__ == "__main__":
    print("Starting database setup...")
    if setup_database():
        print(f"\nDatabase setup successful at: {DB_PATH}")
    else:
        print("\nDatabase setup failed.")
    print("setup db done")