import os
import sqlite3
import pandas as pd
from konfigurasi import DB_PATH, LIST_TANAMAN

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db_connection() -> sqlite3.Connection | None:
    """Membuka dan mengembalikan koneksi ke database SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        # fk active for delete cascading
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Error koneksi ke database: {e}")
        return None


def execute_query(query: str, params: tuple = None):
    """Mengeksekusi query non-SELECT (INSERT, UPDATE, DELETE) dengan parameter opsional."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"ERROR: Query gagal: {e} | Query: {query[:80]}")
        conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def get_dataframe(query: str, params: tuple = None) -> pd.DataFrame:
    """Mengeksekusi query SELECT dan mengembalikan objek Pandas DataFrame."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        print(f"ERROR: Gagal membaca DataFrame: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def seed_master_data():
    """Mengisi data master standar PPM tanaman berdasarkan konfigurasi awal."""
    ppm_presets = {
        'Selada':   (400,  600, 900),
        'Bayam':    (400,  700, 1000),
        'Kangkung': (400,  800, 1100),
        'Sawi':     (500,  900, 1200),
        'Pakcoy':   (500,  900, 1300),
        'Tomat':    (600, 1200, 1800),
        'Cabai':    (600, 1300, 1900),
    }

    for jenis in LIST_TANAMAN:
        if jenis in ppm_presets:
            semaian, veg, gen = ppm_presets[jenis]
            sql = """
            INSERT OR IGNORE INTO config_tanaman(jenis_tanaman, ppm_semaian, ppm_vegetatif, ppm_generatif)
            VALUES (?, ?, ?, ?)
            """
            execute_query(sql, (jenis, semaian, veg, gen))


def setup_database_initial() -> bool:
    """Membuat tabel dan mengisi data master awal jika belum ada."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()

        # for fk
        cursor.execute("PRAGMA foreign_keys = ON")

        # Tabel master: konfigurasi PPM per jenis tanaman
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_tanaman (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis_tanaman   TEXT    UNIQUE NOT NULL,
            ppm_semaian     INTEGER NOT NULL,
            ppm_vegetatif   INTEGER NOT NULL,
            ppm_generatif   INTEGER NOT NULL
        );
        """)

        # Tabel parent: slot / bak tanam aktif
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS slot_tanam (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_slot        TEXT    NOT NULL,
            jenis_tanaman    TEXT    NOT NULL,
            tanggal_tanam    DATE    NOT NULL,
            volume_air_liter REAL    NOT NULL CHECK(volume_air_liter > 0),
            FOREIGN KEY (jenis_tanaman) REFERENCES config_tanaman(jenis_tanaman)
        );
        """)

        # Tabel child: log historis kondisi air — CASCADE DELETE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_kondisi_air (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id     INTEGER NOT NULL,
            tanggal_cek DATE    NOT NULL,
            ppm_aktual  INTEGER NOT NULL CHECK(ppm_aktual >= 0),
            ph_aktual   REAL    NOT NULL CHECK(ph_aktual BETWEEN 0 AND 14),
            FOREIGN KEY (slot_id) REFERENCES slot_tanam(id) ON DELETE CASCADE
        );
        """)

        conn.commit()
        seed_master_data()
        return True
    except sqlite3.Error as e:
        print(f"Error saat inisialisasi tabel: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Mengeksekusi inisialisasi database AgriGrow...")
    sukses = setup_database_initial()
    if sukses:
        print("Selesai! File database dan tabel master berhasil dibuat.")
    else:
        print("Gagal membuat database. Silakan cek pesan kesalahan di atas.")