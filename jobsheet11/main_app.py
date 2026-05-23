# main_app.py
import datetime
import locale
import pandas as pd
from manajer_anggaran import AnggaranHarian
from konfigurasi import KATEGORI_PENGELUARAN  # Ambil list kategori
from model import Transaksi
import streamlit as st

# --- Pengaturan Lokalisasi Mata Uang ---
try:
    locale.setlocale(locale.LC_ALL, "id_ID.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, "Indonesian_Indonesia.1252")
    except Exception:
        print("Locale id_ID/Indonesian tidak tersedia.")


def format_rp(angka):
    """Mengubah format angka biasa menjadi format Rupiah (Rp)."""
    try:
        return locale.currency(angka or 0, grouping=True, symbol="Rp ")[:-3]
    except Exception:
        return f"Rp {angka or 0:,.0f}".replace(",", ".")


# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Catatan Pengeluaran",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Inisialisasi Pengelola Anggaran (Gunakan Cache) ---
@st.cache_resource
def get_anggaran_manager():
    print(
        ">>> STREAMLIT: (Cache Resource) Menginisialisasi AnggaranHarian..."
    )
    return AnggaranHarian()  # Ini akan memicu cek DB/Tabel di __init__


anggaran = get_anggaran_manager()


# --- Fungsi Halaman / UI ---
def halaman_input(anggaran: AnggaranHarian):
    st.header("📝 Tambah Pengeluaran Baru")

    with st.form("form_transaksi_baru", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            deskripsi = st.text_input(
                "Deskripsi*", placeholder="Contoh: Makan siang"
            )
        with col2:
            kategori = st.selectbox(
                "Kategori*:", KATEGORI_PENGELUARAN, index=0
            )

        col3, col4 = st.columns([1, 1])
        with col3:
            jumlah = st.number_input(
                "Jumlah (Rp)*:",
                min_value=0.01,
                step=1000.0,
                format="%.0f",
                value=None,
                placeholder="Contoh: 25000",
            )
        with col4:
            tanggal = st.date_input("Tanggal*:", value=datetime.date.today())

        submitted = st.form_submit_button("💾 Simpan Transaksi")

        if submitted:
            if not deskripsi:
                st.warning("Deskripsi wajib diisi!", icon="⚠️")
            elif jumlah is None or jumlah <= 0:
                st.warning("Jumlah pengeluaran wajib diisi!", icon="⚠️")
            else:
                with st.spinner("Menyimpan ke database..."):
                    tx = Transaksi(deskripsi, float(jumlah), kategori, tanggal)
                    if anggaran.tambah_transaksi(tx):
                        st.success("Transaksi Berhasil Disimpan!", icon="✅")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Gagal menyimpan transaksi.", icon="❌")


def halaman_riwayat(anggaran: AnggaranHarian):
    st.subheader("📋 Detail Semua Transaksi")

    if st.button("🔄 Refresh Riwayat"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Memuat riwayat..."):
        df_transaksi = anggaran.get_dataframe_transaksi()

    if df_transaksi is None:
        st.error("Gagal mengambil data riwayat.")
    elif df_transaksi.empty:
        st.info("Belum ada data transaksi yang tercatat.")
    else:
        df_tampil = df_transaksi.copy()
        df_tampil["Pilih Hapus"] = False

        st.info("💡 **Tips:** Centang kotak pada kolom **Hapus** untuk memilih transaksi yang ingin dihapus.", icon="ℹ️")

        editor_event = st.data_editor(
            df_tampil,
            use_container_width=True,
            hide_index=True,
            # Kunci semua kolom data asli agar tidak bisa diedit oleh user, KECUALI kolom checkbox
            disabled=["ID", "tanggal", "kategori", "deskripsi", "Jumlah (Rp)"], 
            column_config={
                "Pilih Hapus": st.column_config.CheckboxColumn(
                    "Hapus",
                    help="Centang untuk menghapus baris ini",
                    default=False,
                    width="small"
                )
            },
            key="editor_hapus_baris"
        )

        # Cek jika ada checkbox yang diklik/diubah oleh pengguna
        if st.session_state.editor_hapus_baris["edited_rows"]:
            # Ambil nomor index baris yang diubah
            index_terpilih = list(st.session_state.editor_hapus_baris["edited_rows"].keys())[0]
            
            # Cek apakah user mencentang (True), bukan menghilangkan centang
            if st.session_state.editor_hapus_baris["edited_rows"][index_terpilih].get("Pilih Hapus", False) == True:
                if index_terpilih < len(df_transaksi):
                    # Ambil nilai ID database asli dari baris tersebut
                    id_otomatis = int(df_transaksi.iloc[index_terpilih]["ID"])
                    # Masukkan ID otomatis ini ke dalam session state konfirmasi
                    st.session_state.konfirmasi_hapus_id = id_otomatis

        st.markdown("---")
        
        # hapus manual
        st.write("### 🗑️ Hapus Transaksi Berdasarkan ID")
        st.caption(
            "Silakan lihat nomor **ID** pada tabel di atas, atau centang langsung pada tabel untuk mengisi otomatis input di bawah."
        )

        col_id, col_tombol = st.columns([1, 2])

        with col_id:
            # Jika user mengklik dari tabel, kotak inputan ini otomatis akan mengikuti ID tersebut!
            nilai_default = st.session_state.get("konfirmasi_hapus_id", 1)
            
            id_yang_dipilih = st.number_input(
                "ID Transaksi Hapus:", min_value=1, step=1, value=int(nilai_default)
            )

        with col_tombol:
            st.write("##")  
            tombol_hapus = st.button("Hapus Transaksi Terpilih")

        if tombol_hapus:
            st.session_state.konfirmasi_hapus_id = id_yang_dipilih

        if "konfirmasi_hapus_id" in st.session_state:
            id_eksekusi = st.session_state.konfirmasi_hapus_id

            st.warning(
                f"Apakah Anda benar-benar yakin ingin menghapus Transaksi dengan ID **{id_eksekusi}**?",
                icon="⚠️",
            )

            col_ya, col_batal, _ = st.columns([1, 1, 4])
            with col_ya:
                tombol_konfirmasi = st.button("Konfirmasi Hapus", type="primary")
            with col_batal:
                tombol_batal = st.button("Batal")

            # JIKA USER KLIK "KONFIRMASI HAPUS"
            if tombol_konfirmasi:
                with st.spinner("Menghapus transaksi..."):
                    if anggaran.hapus_transaksi(id_eksekusi):
                        st.success(
                            f"Transaksi dengan ID {id_eksekusi} Berhasil Dihapus!",
                            icon="✅",
                        )
                        # Bersihkan session state pengingat
                        if "konfirmasi_hapus_id" in st.session_state:
                            del st.session_state.konfirmasi_hapus_id
                        # Clear cache data dan paksa reload halaman agar tabel langsung bersih
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(
                            f"Gagal menghapus transaksi ID {id_eksekusi} dari database.",
                            icon="❌",
                        )

            # JIKA USER KLIK "BATAL"
            if tombol_batal:
                if "konfirmasi_hapus_id" in st.session_state:
                    del st.session_state.konfirmasi_hapus_id
                st.rerun()

def halaman_ringkasan(anggaran: AnggaranHarian):
    st.subheader("📊 Ringkasan Pengeluaran")

    col_filter1, col_filter2 = st.columns([1, 2])

    with col_filter1:
        pilihan_periode = st.selectbox(
            "Filter Periode:",
            ["Semua Waktu", "Hari Ini", "Pilih Tanggal Tertentu"],
            key="filter_periode",
            on_change=lambda: st.cache_data.clear(),
        )

        tanggal_filter = None
        label_periode = "(Semua Waktu)"

        if pilihan_periode == "Hari Ini":
            tanggal_filter = datetime.date.today()
            label_periode = f"({tanggal_filter.strftime('%d %b')})"
        elif pilihan_periode == "Pilih Tanggal Tertentu":
            if "tanggal_pilihan_state" not in st.session_state:
                st.session_state.tanggal_pilihan_state = datetime.date.today()

            tanggal_filter = st.date_input(
                "Pilih Tanggal:",
                value=st.session_state.tanggal_pilihan_state,
                key="tanggal_pilihan",
                on_change=lambda: setattr(
                    st.session_state,
                    "tanggal_pilihan_state",
                    st.session_state.tanggal_pilihan,
                )
                or st.cache_data.clear(),
            )
            label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"

    with col_filter2:

        @st.cache_data(ttl=300)  # Cache hasil total pengeluaran
        def hitung_total_cached(tgl_filter):
            return anggaran.hitung_total_pengeluaran(tanggal=tgl_filter)

        total_pengeluaran = hitung_total_cached(tanggal_filter)
        st.metric(
            label=f"Total Pengeluaran {label_periode}",
            value=format_rp(total_pengeluaran),
        )

    st.divider()
    st.subheader(f"🗂️ Pengeluaran per Kategori {label_periode}")

    @st.cache_data(ttl=300)  # Cache hasil ringkasan kategori
    def get_kategori_cached(tgl_filter):
        return anggaran.get_pengeluaran_per_kategori(tanggal=tgl_filter)

    with st.spinner("Memuat ringkasan kategori..."):
        dict_per_kategori = get_kategori_cached(tanggal_filter)

    if not dict_per_kategori:
        st.info("Tidak ada data transaksi untuk periode ini.")
    else:
        try:
            data_kategori = [
                {"Kategori": kat, "Total": jml}
                for kat, jml in dict_per_kategori.items()
            ]
            df_kategori = (
                pd.DataFrame(data_kategori)
                .sort_values(by="Total", ascending=False)
                .reset_index(drop=True)
            )
            df_kategori["Total (Rp)"] = df_kategori["Total"].apply(format_rp)

            col_kat1, col_kat2 = st.columns(2)
            with col_kat1:
                st.write("**Tabel:**")
                st.dataframe(
                    df_kategori[["Kategori", "Total (Rp)"]],
                    hide_index=True,
                    use_container_width=True,
                )
            with col_kat2:
                st.write("**Grafik:**")
                st.bar_chart(
                    df_kategori.set_index("Kategori")["Total"],
                    use_container_width=True,
                )
        except Exception as e:
            st.error(f"Gagal menampilkan ringkasan data: {e}")


# --- Fungsi Utama Aplikasi Streamlit ---
def main():
    st.sidebar.title("💰 Catatan Pengeluaran")
    menu_pilihan = st.sidebar.radio(
        "Pilih Menu:", ["Tambah", "Riwayat", "Ringkasan"], key="menu_utama"
    )
    st.sidebar.markdown("---")
    st.sidebar.info("Jobsheet - Aplikasi Keuangan")

    manajer_anggaran = get_anggaran_manager()

    if menu_pilihan == "Tambah":
        halaman_input(manajer_anggaran)
    elif menu_pilihan == "Riwayat":
        halaman_riwayat(manajer_anggaran)
    elif menu_pilihan == "Ringkasan":
        halaman_ringkasan(manajer_anggaran)

    st.markdown("---")
    st.caption("⚡ Pengembangan Aplikasi Berbasis OOP & Streamlit")


if __name__ == "__main__":
    main()  # Jalankan fungsi utama