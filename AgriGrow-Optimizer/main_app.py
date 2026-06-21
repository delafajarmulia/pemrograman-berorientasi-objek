# main_app.py
import streamlit as st
import datetime
import database
from konfigurasi import LIST_TANAMAN
from manajer_kebun import ManajerKebun

# ── Inisialisasi ─────────────────────────────────────────────────────────────
database.setup_database_initial()
manajer = ManajerKebun()

# ── Konfigurasi Halaman ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgriGrow Optimizer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Header Utama ──────────────────────────────────────────────────────────────
st.title("🌿 AgriGrow Optimizer")
st.caption("Smart Hydroponic Hub — Sistem Manajemen Nutrisi & Pemantauan Kualitas Air Hidroponik")
st.markdown("---")

# ── Navigasi Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/plant-under-rain.png", width=72)
    st.markdown("### 🌿 AgriGrow Optimizer")
    st.caption("D4 TRK — Politeknik Negeri Semarang")
    st.markdown("---")
    menu = st.selectbox(
        "Navigasi Menu:",
        [
            "🌱 Registrasi Slot Tanam",
            "💧 Catat Air & Dosis Nutrisi",
            "📊 Pusat Kendali Analitik",
        ],
    )
    st.markdown("---")
    st.caption("AgriGrow Optimizer v1.0\nDela Fajar Mulia / 4.33.25.2.07")


# ==============================================================================
# HALAMAN 1 — REGISTRASI SLOT TANAM
# ==============================================================================
if menu == "🌱 Registrasi Slot Tanam":
    st.header("🌱 Pendaftaran Bak / Slot Instalasi Baru")
    st.info("Daftarkan wadah/bak hidroponik baru beserta jenis komoditas dan kapasitas airnya.")

    with st.form("form_tambah_slot", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama_slot = st.text_input(
                "Nama Identitas Slot / Blok Fisik *",
                placeholder="Contoh: Rak Depan Polines 01",
            )
            jenis_tanaman = st.selectbox("Varietas Komoditas Tanaman *", LIST_TANAMAN)
        with col2:
            volume_air = st.number_input(
                "Kapasitas Air Wadah Baku (Liter) *",
                min_value=0.5,
                value=10.0,
                step=0.5,
                format="%.1f",
            )
            tanggal_tanam = st.date_input(
                "Tanggal Mulai Penyemaian *",
                value=datetime.date.today(),
                max_value=datetime.date.today(),
            )

        st.markdown("&nbsp;")
        tombol_simpan = st.form_submit_button(
            "💾 Simpan Data Instalasi", use_container_width=True, type="primary"
        )

        if tombol_simpan:
            if not nama_slot.strip():
                st.error("⚠️ Nama identitas slot tidak boleh kosong!")
            else:
                sukses = manajer.tambah_slot_tanam(
                    nama_slot.strip(), jenis_tanaman, tanggal_tanam, volume_air
                )
                if sukses:
                    st.success(
                        f"✅ Berhasil mendaftarkan **{nama_slot}** "
                        f"({jenis_tanaman}, {volume_air} L) ke dalam sistem!"
                    )
                else:
                    st.error("❌ Gagal menyimpan data. Cek koneksi database.")

    # Tabel inventaris ringkas di bawah form
    st.markdown("---")
    st.subheader("📋 Daftar Slot Instalasi Aktif")
    df_preview = database.get_dataframe("""
        SELECT nama_slot AS 'Nama Slot', jenis_tanaman AS 'Varietas',
               tanggal_tanam AS 'Tgl Tanam', volume_air_liter AS 'Volume (L)'
        FROM slot_tanam ORDER BY id DESC
    """)
    if df_preview.empty:
        st.info("Belum ada slot yang terdaftar.")
    else:
        st.dataframe(df_preview, use_container_width=True, hide_index=True)


# ==============================================================================
# HALAMAN 2 — CATAT AIR & REKOMENDASI DOSIS
# ==============================================================================
elif menu == "💧 Catat Air & Dosis Nutrisi":
    st.header("💧 Buku Log Air & Kalkulator Nutrisi AB Mix")

    df_slot = database.get_dataframe("SELECT id, nama_slot FROM slot_tanam ORDER BY nama_slot")

    if df_slot.empty:
        st.warning("⚠️ Belum ada slot instalasi aktif. Silakan daftarkan slot baru di Menu Pertama.")
    else:
        pilihan_slot = {row["nama_slot"]: row["id"] for _, row in df_slot.iterrows()}

        col_sel, _ = st.columns([2, 3])
        with col_sel:
            slot_terpilih_nama = st.selectbox(
                "Pilih Instalasi Bak Tanam:", list(pilihan_slot.keys())
            )
        slot_terpilih_id = pilihan_slot[slot_terpilih_nama]

        st.markdown("---")
        col_input, col_tabel = st.columns([1, 2])

        # ── Kolom Kiri: Input Pengukuran ──────────────────────────────────────
        with col_input:
            st.subheader("🔬 Input Indikator Alat Ukur")
            ppm_aktual = st.number_input(
                "Hasil Bacaan TDS Meter (PPM):",
                min_value=0,
                max_value=5000,
                value=500,
                step=10,
            )
            ph_aktual = st.number_input(
                "Derajat Keasaman (pH Meter):",
                min_value=0.0,
                max_value=14.0,
                value=6.0,
                step=0.1,
                format="%.1f",
            )
            tanggal_cek = st.date_input(
                "Tanggal Pemeriksaan:",
                value=datetime.date.today(),
                max_value=datetime.date.today(),
            )

            # Status pH preview
            if 5.5 <= ph_aktual <= 6.5:
                st.success(f"✅ pH {ph_aktual:.1f} — Status NORMAL (ideal: 5.5–6.5)")
            else:
                st.error(f"🚨 pH {ph_aktual:.1f} — ANOMALI! Di luar rentang ideal (5.5–6.5)")

            st.markdown("&nbsp;")
            if st.button("⚗️ Hitung & Simpan Log", use_container_width=True, type="primary"):
                hasil = manajer.hitung_rekomendasi_nutrisi(slot_terpilih_id, ppm_aktual)
                simpan_log = manajer.catat_kondisi_air(
                    slot_terpilih_id, tanggal_cek, ppm_aktual, ph_aktual
                )

                if simpan_log:
                    st.success("✅ Data pengukuran berhasil diarsipkan!")
                    st.markdown("---")
                    if hasil.get("rekomendasi_ml", 0) > 0:
                        st.info(
                            f"💡 **Sistem Rekomendasi Pintar**\n\n"
                            f"Tanaman berumur **{hasil['hst']} HST** "
                            f"(Fase **{hasil['fase']}**).\n\n"
                            f"- **Target Optimal:** {hasil['target_ppm']} PPM\n"
                            f"- **PPM Aktual:** {ppm_aktual} PPM\n"
                            f"- **Defisit:** {hasil['defisit']} PPM\n\n"
                            f"📌 Tuangkan masing-masing **{hasil['rekomendasi_ml']} ml** "
                            f"Larutan Stok **A** dan **B** ke dalam bak!"
                        )
                    else:
                        st.success(
                            f"✅ **Status Aman** — Fase **{hasil['fase']}** "
                            f"({hasil['hst']} HST). "
                            f"Kepekatan nutrisi sudah memenuhi target "
                            f"**{hasil['target_ppm']} PPM**. Tidak perlu penambahan pupuk."
                        )
                else:
                    st.error("❌ Gagal merekam log kondisi air.")

        # ── Kolom Kanan: Inventaris & Hapus ──────────────────────────────────
        with col_tabel:
            st.subheader("📦 Inventaris Seluruh Bak Tanam")
            df_all = database.get_dataframe("""
                SELECT id, nama_slot AS 'Nama Instalasi',
                       jenis_tanaman AS 'Varietas',
                       tanggal_tanam AS 'Tgl Tanam',
                       volume_air_liter AS 'Kapasitas (L)'
                FROM slot_tanam ORDER BY id
            """)
            st.dataframe(df_all, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🚨 Siklus Akhir — Panen / Bongkar Instalasi")
            st.warning(
                "⚠️ Tindakan ini bersifat **permanen**. "
                "Seluruh log air terkait akan ikut terhapus (Cascade Delete)."
            )
            slot_hapus_nama = st.selectbox(
                "Pilih Bak yang Selesai Dipanen:",
                list(pilihan_slot.keys()),
                key="del_box",
            )
            slot_hapus_id = pilihan_slot[slot_hapus_nama]

            if st.button(
                f"🗑️ Eksekusi Panen / Hapus '{slot_hapus_nama}'",
                type="primary",
                use_container_width=True,
            ):
                if manajer.hapus_slot_panen(slot_hapus_id):
                    st.success(f"✅ Bak **'{slot_hapus_nama}'** berhasil dikosongkan!")
                    st.rerun()
                else:
                    st.error("❌ Gagal menghapus data.")


# ==============================================================================
# HALAMAN 3 — PUSAT KENDALI ANALITIK
# ==============================================================================
elif menu == "📊 Pusat Kendali Analitik":
    st.header("📊 Dashboard Visualisasi Eksekutif Kebun")

    df_slot = database.get_dataframe("SELECT * FROM slot_tanam")
    df_log = database.get_dataframe("SELECT * FROM log_kondisi_air ORDER BY tanggal_cek")

    # ── KPI Metrics ───────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            label="🌱 Total Slot Instalasi Aktif",
            value=len(df_slot),
            help="Jumlah bak/wadah hidroponik yang sedang beroperasi",
        )

    with c2:
        total_air = df_slot["volume_air_liter"].sum() if not df_slot.empty else 0.0
        st.metric(
            label="💧 Total Volume Air Terkelola",
            value=f"{total_air:.1f} Liter",
            help="Akumulasi kapasitas air dari seluruh bak aktif",
        )

    with c3:
        if not df_log.empty:
            ph_terakhir = df_log.iloc[-1]["ph_aktual"]
            if 5.5 <= ph_terakhir <= 6.5:
                st.metric(
                    "🩺 Status Alarm Kesehatan Air",
                    "NORMAL ✅",
                    delta=f"pH {ph_terakhir:.1f}",
                    delta_color="normal",
                )
            else:
                st.metric(
                    "🩺 Status Alarm Kesehatan Air",
                    "ANOMALI 🚨",
                    delta=f"pH {ph_terakhir:.1f} — Di luar rentang!",
                    delta_color="inverse",
                )
        else:
            st.metric("🩺 Status Alarm Kesehatan Air", "NO DATA", help="Belum ada log air tercatat")

    st.markdown("---")

    # ── Grafik ────────────────────────────────────────────────────────────────
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("🌾 Sebaran Populasi Varietas Komoditas")
        if not df_slot.empty:
            df_chart = (
                df_slot.groupby("jenis_tanaman")
                .size()
                .reset_index(name="Jumlah Bak")
                .set_index("jenis_tanaman")
            )
            st.bar_chart(df_chart, use_container_width=True)
        else:
            st.info("📭 Belum ada data slot untuk ditampilkan.")

    with col_g2:
        st.subheader("📈 Tren Fluktuasi Nilai PPM Harian")
        if not df_log.empty:
            df_trend = (
                df_log[["tanggal_cek", "ppm_aktual"]]
                .copy()
                .sort_values("tanggal_cek")
                .set_index("tanggal_cek")
            )
            st.line_chart(df_trend, use_container_width=True)
        else:
            st.info("📭 Pemeriksaan instrumen belum tercatat untuk memetakan tren.")

    # ── Tabel Log Lengkap ─────────────────────────────────────────────────────
    if not df_log.empty:
        st.markdown("---")
        st.subheader("🗂️ Riwayat Log Kondisi Air (Seluruh Slot)")
        df_log_display = database.get_dataframe("""
            SELECT l.tanggal_cek AS 'Tanggal', s.nama_slot AS 'Nama Slot',
                   s.jenis_tanaman AS 'Varietas',
                   l.ppm_aktual AS 'PPM Aktual',
                   l.ph_aktual AS 'pH Aktual'
            FROM log_kondisi_air l
            JOIN slot_tanam s ON l.slot_id = s.id
            ORDER BY l.tanggal_cek DESC, l.id DESC
        """)
        st.dataframe(df_log_display, use_container_width=True, hide_index=True)