import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(
    page_title="Generator Laporan Karantina",
    layout="wide"
)

# ==================================================
# FUNGSI BACA FILE KARANTINA
# ==================================================

def baca_laporan(file):

    isi = file.getvalue().decode(
        "utf-8",
        errors="ignore"
    )

    baris = isi.splitlines()

    header_idx = None

    for i, line in enumerate(baris):

        if line.startswith('No.,') or line.startswith('No.,"'):
            header_idx = i
            break

    if header_idx is None:
        raise Exception(
            "Header tabel tidak ditemukan."
        )

    csv_bersih = "\n".join(
        baris[header_idx:]
    )

    df = pd.read_csv(
        StringIO(csv_bersih)
    )

    return df


# ==================================================
# JUDUL
# ==================================================

st.title("Generator Laporan Karantina")

# ==================================================
# UPLOAD FILE
# ==================================================

file_penugasan = st.file_uploader(
    "Upload File Penugasan",
    type=["csv"]
)

file_pelepasan = st.file_uploader(
    "Upload File Pelepasan (maksimal 3 file)",
    type=["csv"],
    accept_multiple_files=True
)

if file_pelepasan and len(file_pelepasan) > 3:

    st.error(
        "Maksimal 3 file pelepasan."
    )

    st.stop()

# ==================================================
# PROSES
# ==================================================

if file_penugasan and file_pelepasan:

    try:

        # ==========================================
        # BACA PENUGASAN
        # ==========================================

        df_penugasan = baca_laporan(
            file_penugasan
        )

        if "No Permohonan" not in df_penugasan.columns:

            st.error(
                "Kolom 'No Permohonan' tidak ditemukan."
            )

            st.stop()

        nomor_dokumen = (
            df_penugasan["No Permohonan"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        st.success(
            f"Ditemukan {len(nomor_dokumen)} nomor dokumen unik."
        )

        # ==========================================
        # BACA PELEPASAN
        # ==========================================

        list_df = []

        for file in file_pelepasan:

            df = baca_laporan(file)

            list_df.append(df)

        df_pelepasan = pd.concat(
            list_df,
            ignore_index=True
        )

        if "No. K.1.1" not in df_pelepasan.columns:

            st.error(
                "Kolom 'No. K.1.1' tidak ditemukan."
            )

            st.stop()

        # ==========================================
        # FILTER
        # ==========================================

        df_filter = df_pelepasan[
            df_pelepasan["No. K.1.1"]
            .astype(str)
            .isin(nomor_dokumen)
        ]

        st.info(
            f"Ditemukan {len(df_filter)} baris yang cocok."
        )

        nomor_opsi = sorted(
            df_filter["No. K.1.1"]
            .astype(str)
            .unique()
            .tolist()
        )

        # ==========================================
        # OPSI HASIL
        # ==========================================

        st.subheader(
            "Pengaturan Hasil Pemeriksaan"
        )

        semua_admin = st.checkbox(
            "Semua Administrasi = Lengkap, sah dan benar",
            value=True
        )

        semua_kesehatan = st.checkbox(
            "Semua Kesehatan = BEBAS OPTK",
            value=True
        )

        semua_kesimpulan = st.checkbox(
            "Semua Kesimpulan = PEMBEBASAN",
            value=True
        )

        admin_override = {}
        kesehatan_override = {}
        kesimpulan_override = {}

        # ==========================================
        # ADMINISTRASI
        # ==========================================

        if not semua_admin:

            st.subheader(
                "Pengecualian Administrasi"
            )

            for nomor in nomor_opsi:

                admin_override[nomor] = st.text_input(
                    f"Administrasi - {nomor}",
                    value="Lengkap, sah dan benar"
                )

        # ==========================================
        # KESEHATAN
        # ==========================================

        if not semua_kesehatan:

            st.subheader(
                "Pengecualian Kesehatan"
            )

            for nomor in nomor_opsi:

                kesehatan_override[nomor] = st.text_input(
                    f"Kesehatan - {nomor}",
                    value="BEBAS OPTK"
                )

        # ==========================================
        # KESIMPULAN
        # ==========================================

        if not semua_kesimpulan:

            st.subheader(
                "Pengecualian Kesimpulan"
            )

            for nomor in nomor_opsi:

                kesimpulan_override[nomor] = st.text_input(
                    f"Kesimpulan - {nomor}",
                    value="PEMBEBASAN"
                )

        # ==========================================
        # GENERATE
        # ==========================================

        if st.button(
            "Generate TXT"
        ):

            hasil = []

            nomor_urut = 1

            for nomor, grup in df_filter.groupby(
                "No. K.1.1"
            ):

                tanggal = grup.iloc[0][
                    "Tgl Dokumen"
                ]

                satpel = grup.iloc[0][
                    "Satpel"
                ]

                nomor_dok_hasil = grup.iloc[0][
                    "Nomor Dokumen"
                ]

                tujuan = grup.iloc[0][
                    "Daerah Tujuan"
                ]

                komoditas = ", ".join(
                    grup["Komoditas"]
                    .dropna()
                    .astype(str)
                    .unique()
                )

                nomor_seri = ", ".join(
                    grup["Nomor Seri"]
                    .dropna()
                    .astype(str)
                    .unique()
                )

                administrasi = (
                    "Lengkap, sah dan benar"
                    if semua_admin
                    else admin_override.get(
                        nomor,
                        "Lengkap, sah dan benar"
                    )
                )

                kesehatan = (
                    "BEBAS OPTK"
                    if semua_kesehatan
                    else kesehatan_override.get(
                        nomor,
                        "BEBAS OPTK"
                    )
                )

                kesimpulan = (
                    "PEMBEBASAN"
                    if semua_kesimpulan
                    else kesimpulan_override.get(
                        nomor,
                        "PEMBEBASAN"
                    )
                )

                hasil.append([
                    nomor_urut,
                    tanggal,
                    satpel,
                    nomor,
                    nomor_dok_hasil,
                    komoditas,
                    tujuan,
                    nomor_seri,
                    administrasi,
                    kesehatan,
                    kesimpulan
                ])

                nomor_urut += 1

            df_hasil = pd.DataFrame(
                hasil,
                columns=[
                    "No.",
                    "Tgl Dokumen",
                    "Satpel",
                    "K.1.1",
                    "Nomor Dokumen",
                    "Komoditas",
                    "Tujuan",
                    "Nomor Seri",
                    "Administrasi",
                    "Kesehatan",
                    "Kesimpulan"
                ]
            )

            st.success(
                f"Berhasil membuat {len(df_hasil)} data laporan."
            )

            st.dataframe(
                df_hasil,
                use_container_width=True
            )

            txt_buffer = StringIO()

            df_hasil.to_csv(
                txt_buffer,
                sep="\t",
                index=False
            )

            st.download_button(
                label="Download TXT",
                data=txt_buffer.getvalue(),
                file_name="laporan_hasil.txt",
                mime="text/plain"
            )

    except Exception as e:

        st.error(
            f"Terjadi kesalahan: {e}"
        )