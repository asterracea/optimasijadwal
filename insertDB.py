from sqlalchemy import create_engine,text
import pandas as pd
from datetime import datetime

def simpanData(df_setjadwal):
    db = 'mysql+pymysql://root:@localhost/db_optimasi1'
    engine = create_engine(db)
    tgl = datetime.now().strftime("%d%m%Y")

    try:
        with engine.begin() as connection:
            jumlahId = connection.execute(
                text("SELECT COUNT(*) FROM tb_generate WHERE id_generate LIKE :prefix"), {"prefix": tgl + "%"}
            )
            hitung = jumlahId.scalar() + 1
            idGenerate = f"{tgl}-{hitung:02d}"

            connection.execute(
                text("INSERT INTO tb_generate (id_generate, waktu_generate) VALUES (:id_generate, NOW())"),
                {"id_generate": idGenerate}
            )

        df_dosen = df_setjadwal[['kode_dosen', 'nama_dosen']].drop_duplicates()
        df_semester = df_setjadwal[['id_semester', 'nama_semester']].drop_duplicates()
        df_rombel = df_setjadwal[['id_kelasrombel', 'nama_kelas']].drop_duplicates()
        df_matkul = df_setjadwal[['kode_matakuliah', 'nama_matakuliah','sks','status','nama_semester']].drop_duplicates()
        # df_ruang = df_setruang[['kode_ruang', 'nama_ruangan', 'status_ruangan']].drop_duplicates()

        df_dosen["nipnidn"] = df_dosen["kode_dosen"]
        df_dosen["id_generate"] = idGenerate
        df_dosen["kode_dosen"] = df_dosen["id_generate"].astype(str) + "_" + df_dosen["kode_dosen"].astype(str)

        df_semester["id_generate"] = idGenerate
        df_semester["id_semester"] = df_semester["id_generate"].astype(str) + "_" + df_semester["id_semester"].astype(str)

        df_rombel["id_generate"] = idGenerate
        df_rombel["id_kelasrombel"] = df_rombel["id_generate"].astype(str) + "_" + df_rombel["id_kelasrombel"].astype(str)

        df_matkul["id_generate"] = idGenerate
        df_matkul["kode_matakuliah"] = df_matkul["id_generate"].astype(str) + "_" + df_matkul["kode_matakuliah"].astype(str)

        # df_ruang["kode_ruangan"] = df_ruang["kode_ruang"]
        # df_ruang["id_generate"] = idGenerate
        # df_ruang["kode_ruang"] = df_ruang["id_generate"].astype(str)+ "_" +df_ruang["kode_ruang"].astype(str)

        df_perkuliahan = df_setjadwal[['kode_matakuliah','id_kelasrombel','nama_kelas']]
        df_perkuliahan['id_kelasrombel'] = idGenerate + "_" + df_setjadwal["id_kelasrombel"].astype(str)
        df_perkuliahan['kode_matakuliah'] = idGenerate + "_" + df_setjadwal["kode_matakuliah"].astype(str)
        df_perkuliahan['kode_dosen'] = idGenerate + "_" + df_setjadwal["kode_dosen"].astype(str)

        with engine.begin() as connection:
            df_dosen.to_sql("tb_dosen", con=engine, if_exists="append", index=False)
            df_semester.to_sql("tb_semester", con=engine, if_exists="append", index=False)
            df_rombel.to_sql("tb_rombel", con=engine, if_exists="append", index=False)
            df_matkul.to_sql("tb_matakuliah", con=engine, if_exists="append", index=False)
            # df_ruang.to_sql("tb_ruang", con=engine, if_exists="append", index=False)
            df_perkuliahan.to_sql("tb_perkuliahan", con=engine, if_exists="append", index=False)

    except Exception as e:
        print(f"Error terjadi: {e}")
