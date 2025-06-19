from sqlalchemy import create_engine, text
import pandas as pd
from config import db_url
from datetime import datetime

def simpanData(json_data, id_user):
    try:
        df_setjadwal = pd.json_normalize(json_data['setJadwal'])
        df_setruang = pd.json_normalize(json_data['setRuang'])
        df_setwaktu = pd.json_normalize(json_data['setWaktu'])

        with db_url.begin() as connection:
            prefix = datetime.now().strftime("G%d%m")  
            jumlahId = connection.execute(
                text("SELECT COUNT(*) FROM tb_generate WHERE id_generate LIKE :prefix"),
                {"prefix": prefix + "%"}
            )
            hitung = jumlahId.scalar() + 1
            idGenerate = f"{prefix}-{hitung:02d}"

            connection.execute(
                text("INSERT INTO tb_generate (id_generate, id_user, waktu_generate) VALUES (:id_generate, :id_user,NOW())"),
                {"id_generate": idGenerate,"id_user" : id_user}
            )

        # dataframe yang dibutuhkan untuk dimasukkan ke database
        df_dosen = df_setjadwal[['kode_dosen', 'nama_dosen']].drop_duplicates()
        df_semester = df_setjadwal[['id_semester', 'nama_semester']].drop_duplicates()
        df_rombel = df_setjadwal[['id_kelasrombel', 'nama_kelas']].drop_duplicates()
        df_prodi = df_setjadwal[['kode_prodi','nama_prodi']].drop_duplicates()
        df_matkul = df_setjadwal[['kode_matakuliah', 'nama_matakuliah', 'sks', 'status', 'nama_semester','kategori','kode_pasangan']].drop_duplicates()
        df_ruang = df_setruang[['kode_ruang', 'nama_ruangan', 'status_ruangan']].drop_duplicates()
        df_waktu = df_setwaktu[['id_waktu','jam_mulai','jam_selesai','nama_hari']].drop_duplicates()

        df_dosen["nipnidn"] = df_dosen["kode_dosen"]
        df_dosen["id_generate"] = idGenerate
        df_dosen["kode_dosen"] = df_dosen["id_generate"].astype(str) + "_" + df_dosen["kode_dosen"].astype(str)

        df_semester["id_generate"] = idGenerate
        df_semester["id_semester"] = df_semester["id_generate"].astype(str) + "_" + df_semester["id_semester"].astype(str)

        df_rombel["id_generate"] = idGenerate
        df_rombel["id_kelasrombel"] = df_rombel["id_generate"].astype(str) + "_" + df_rombel["id_kelasrombel"].astype(str)

 
        df_matkul["id_generate"] = idGenerate
        df_matkul["kode_matakuliah"] = df_matkul["id_generate"].astype(str) + "_" + df_matkul["kode_matakuliah"].astype(str)

        df_ruang["kode_ruangan"] = df_ruang["kode_ruang"]
        df_ruang["id_generate"] = idGenerate
        df_ruang["kode_ruang"] = df_ruang["id_generate"].astype(str) + "_" + df_ruang["kode_ruang"].astype(str)

        df_waktu["id_generate"] = idGenerate
        df_waktu["id_waktu"] = df_waktu["id_generate"].astype(str) + "_" + df_waktu["id_waktu"].astype(str)

        df_prodi["id_generate"] = idGenerate
        df_prodi["kode_prodi"] = df_prodi["id_generate"].astype(str) + "_" + df_prodi["kode_prodi"].astype(str)

        df_perkuliahan = df_setjadwal[['id_kelasrombel','id_semester','kode_matakuliah','kode_dosen','kode_prodi']]
        df_perkuliahan["id_generate"] = idGenerate
        df_perkuliahan['id_kelasrombel'] = idGenerate + "_" + df_perkuliahan["id_kelasrombel"].astype(str)
        df_perkuliahan['id_semester'] = idGenerate + "_" + df_setjadwal["id_semester"].astype(str)
        df_perkuliahan['kode_matakuliah'] = idGenerate + "_" + df_perkuliahan["kode_matakuliah"].astype(str)
        df_perkuliahan['kode_dosen'] = idGenerate + "_" + df_setjadwal["kode_dosen"].astype(str)
        df_perkuliahan['kode_prodi'] = idGenerate + "_" + df_setjadwal["kode_prodi"].astype(str)
        df_perkuliahan['temp_perkuliahan'] = df_setjadwal['id_perkuliahan']


        # SIMPAN KE DATABASE
        with db_url.begin() as connection:
            df_dosen.to_sql("tb_dosen", con=connection, if_exists="append", index=False)
            df_semester.to_sql("tb_semester", con=connection, if_exists="append", index=False)
            df_rombel.to_sql("tb_rombel", con=connection, if_exists="append", index=False)            
            df_matkul.to_sql("tb_matakuliah", con=connection, if_exists="append", index=False)
            df_ruang.to_sql("tb_ruang", con=connection, if_exists="append", index=False)
            df_prodi.to_sql("tb_prodi", con=connection, if_exists="append", index=False)
            df_waktu.to_sql("tb_waktu", con=connection, if_exists="append", index=False)
            df_perkuliahan.to_sql("tb_perkuliahan", con=connection, if_exists="append", index=False)

        print("Data berhasil disimpan ke database.")

    except Exception as e:
        print(f"Error terjadi: {e}")
