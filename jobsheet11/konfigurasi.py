import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NAMA_DB = 'pengeluran_harian.db'
DB_PATH = os.path.join(BASE_DIR, NAMA_DB)
KATEGORI_PENGELUARAN = ['Makanan', 'Transportasi', 'Hiburan', 'Tagihan', 'Pendidikan', 'Kesehatan', 'Belanja', 'Lainnya']
KATEGORI_DEFAULT = 'Lainnya'