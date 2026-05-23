import datetime
import locale


class Transaksi:
    """Merepresentasikan satu entitas transaksi pengeluaran (Data Class)."""

    def __init__(
        self,
        deskripsi: str,
        jumlah: float,
        kategori: str,
        tanggal: datetime.date | str,
        id_transaksi: int | None = None,
    ):
        self.id = id_transaksi

        # 1. VALIDASI DESKRIPSI
        self.deskripsi = str(deskripsi) if deskripsi else "Tanpa Deskripsi"

        # 2. VALIDASI JUMLAH (Harus berupa angka positif)
        try:
            jumlah_float = float(jumlah)
            if jumlah_float > 0:
                self.jumlah = jumlah_float
            else:
                self.jumlah = 0.0
                print(f"Peringatan: Jumlah '{jumlah}' harus positif.")
        except (ValueError, TypeError):
            self.jumlah = 0.0
            print(f"Peringatan: Jumlah '{jumlah}' tidak valid.")

        # 3. VALIDASI KATEGORI
        self.kategori = str(kategori) if kategori else "Lainnya"

        # 4. VALIDASI TANGGAL (Bisa menerima objek date atau string format YYYY-MM-DD)
        if isinstance(tanggal, datetime.date):
            self.tanggal = tanggal
        elif isinstance(tanggal, str):
            try:
                # Mengubah string 'YYYY-MM-DD' menjadi objek date
                self.tanggal = datetime.datetime.strptime(
                    tanggal, "%Y-%m-%d"
                ).date()
            except ValueError:
                self.tanggal = datetime.date.today()
                print(f"Peringatan: Format tgl '{tanggal}' salah.")
        else:
            self.tanggal = datetime.date.today()
            print(f"Peringatan: Tipe tgl '{type(tanggal)}' tidak valid.")

    # Metode khusus (magic method) untuk memberikan representasi string objek Transaksi yang rapi dan informatif guna mempermudah proses debugging di bagian backend.
    def __repr__(self) -> str:
        """Mengatur tampilan objek saat dicetak (print)."""
        try:
            # Mengatur format mata uang/angka sesuai standar Indonesia (IDN)
            locale.setlocale(locale.LC_ALL, "id_ID.UTF-8")
            jml_str = locale.format_string(
                "%.0f", self.jumlah, grouping=True
            )
        except Exception:
            # Jika sistem komputer tidak mendukung locale IDN, pakai format biasa
            jml_str = f"{self.jumlah:.0f}"

        tgl_str = self.tanggal.strftime("%Y-%m-%d")
        return (
            f"Transaksi(ID:{self.id}, Tgl:{tgl_str}, Jml:{jml_str}, "
            f"Kat:'{self.kategori}', Desc:'{self.deskripsi}')"
        )

    def to_dict(self) -> dict:
        """Mengubah data objek Transaksi menjadi bentuk Dictionary."""
        return {
            "deskripsi": self.deskripsi,
            "jumlah": self.jumlah,
            "kategori": self.kategori,
            "tanggal": self.tanggal.strftime("%Y-%m-%d"),
        }