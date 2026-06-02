import datetime

class LogAir:
    """Model data enkapsulasi untuk pencatatan kondisi air."""
    def __init__(self, log_id: int, slot_id: int, tanggal_cek:datetime.date, ppm_aktual: int, ph_aktual: float):
        self.__id = log_id
        self.__slot_id = slot_id
        self.tanggal_cek = tanggal_cek
        self.ppm_aktual = ppm_aktual
        self.ph_aktual = ph_aktual

    @property
    def status_ph(self) -> str:
        """Absatraksi logika penentuan status kesehatan pH air baku"""
        if 5.5 <= self.ph_aktual <= 6.5:
            return 'NORMAL'
        return 'ANOMALI/BAHAYA'
    
class SlotTanam:
    """Model data utama yg menerapkan prinsip komposisi terhadap LogAir"""
    def __init__(self, slot_id: int, nama_slot: str, jenis_tanaman: str, tanggal_tanam: datetime.date, volume_air: float):
        self.__id = slot_id
        self.nama_slot = nama_slot
        self.jenis_tanaman = jenis_tanaman
        self.tanggal_tanam = tanggal_tanam
        self.volume_air = volume_air
        self.log_kondisi_air = []  # List untuk menyimpan objek LogAir terkait slot ini

    def hitung_umur_hst(self) -> int:
        """Menghitung umur tanaman dinamis: Hari Setelah Tanam (HST)"""
        selisih = datetime.date.today() - self.tanggal_tanam
        return max(0, selisih.days)  # Pastikan tidak negatif
    
    def tentukan_fase(self) -> str:
        """Mengklasifikasikan dase pertumbuhan vegetatif atau generatif"""
        hst = self.hitung_umur_hst()
        if hst <= 7:
            return 'Semaian'
        elif hst <= 21:
            return 'Vegetatif'
        else:
            return 'Generatif'
        
    def get_id(self) -> int:
        return self.__id