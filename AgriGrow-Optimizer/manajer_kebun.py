import datetime
import database


class ManajerKebun:
    """Kelas logika bisnis utama dengan pola Singleton."""

    _instance = None

    def __new__(cls):
        """Pola Singleton: hanya satu instance ManajerKebun yang hidup."""
        if cls._instance is None:
            cls._instance = super(ManajerKebun, cls).__new__(cls)
        return cls._instance

    # CRUD Methods
    def tambah_slot_tanam(self, nama: str, jenis: str, tgl_tanam, volume: float) -> bool:
        sql = """
        INSERT INTO slot_tanam(nama_slot, jenis_tanaman, tanggal_tanam, volume_air_liter)
        VALUES (?, ?, ?, ?)
        """
        return database.execute_query(sql, (nama, jenis, str(tgl_tanam), volume)) is not None

    def catat_kondisi_air(self, slot_id: int, tgl_cek, ppm: int, ph: float) -> bool:
        sql = """
        INSERT INTO log_kondisi_air(slot_id, tanggal_cek, ppm_aktual, ph_aktual)
        VALUES (?, ?, ?, ?)
        """
        return database.execute_query(sql, (slot_id, str(tgl_cek), ppm, ph)) is not None

    def hapus_slot_panen(self, slot_id: int) -> bool:
        """Menghapus slot tanam; CASCADE DELETE otomatis membersihkan log air terkait."""
        sql = "DELETE FROM slot_tanam WHERE id = ?"
        return database.execute_query(sql, (slot_id,)) is not None

    # Kalkulasi Nutrisi
    def hitung_rekomendasi_nutrisi(self, slot_id: int, ppm_aktual: int) -> dict:
        """Menghitung rekomendasi dosis AB Mix berdasarkan fase HST dan defisit PPM."""
        query = """
            SELECT s.volume_air_liter, s.tanggal_tanam, s.jenis_tanaman,
                   c.ppm_semaian, c.ppm_vegetatif, c.ppm_generatif
            FROM slot_tanam s
            JOIN config_tanaman c ON s.jenis_tanaman = c.jenis_tanaman
            WHERE s.id = ?
        """
        df = database.get_dataframe(query, (slot_id,))
        if df.empty:
            return {"status": "Error", "rekomendasi_ml": 0}

        # Parsing tanggal tanam
        tgl_tanam = datetime.datetime.strptime(
            df['tanggal_tanam'].iloc[0], "%Y-%m-%d"
        ).date()
        hst = max(0, (datetime.date.today() - tgl_tanam).days)
        
        if hst <= 7:
            target_ppm = int(df['ppm_semaian'].iloc[0])
            fase = "Semaian"
        elif hst <= 21:
            target_ppm = int(df['ppm_vegetatif'].iloc[0])
            fase = "Vegetatif"
        else:
            target_ppm = int(df['ppm_generatif'].iloc[0])
            fase = "Generatif"

        defisit = target_ppm - ppm_aktual
        volume_air = df['volume_air_liter'].iloc[0]

        rekomendasi_ml = 0.0
        if defisit > 0:
            # Rumus: (Defisit / 1000) × Volume Air × 5 ml/liter/1000PPM
            rekomendasi_ml = (defisit / 1000) * volume_air * 5

        return {
            "jenis":          df['jenis_tanaman'].iloc[0],
            "hst":            hst,
            "fase":           fase,
            "target_ppm":     target_ppm,
            "defisit":        max(0, defisit),
            "rekomendasi_ml": round(rekomendasi_ml, 1),
        }