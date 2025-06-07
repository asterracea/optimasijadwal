
import requests
import random
from datetime import datetime, timedelta
import time
import math
# import psycopg2
import pandas as pd
from sqlalchemy import create_engine,text

class Ruang:
    def __init__(self, nama, tipe_ruang):
        self.nama = nama
        self.tipe_ruang = tipe_ruang
    
    def __repr__(self):
        return f"Ruang(nama={self.nama}, tipe_ruang={self.tipe_ruang})"

class Matakuliah:
    def __init__(self, matkul, dosen, sks, kelas, status, id_perkuliahan, id_semester,kategori): #tambah id_perkuliahan
        self.id_perkuliahan = id_perkuliahan
        self.matkul = matkul
        self.dosen = dosen
        self.sks = sks
        self.status = status
        self.kelas = kelas
        self.id_semester = id_semester
        self.kategori = kategori

    def __repr__(self):
        return (f"Matakuliah(matkul={self.matkul}, dosen={self.dosen}, sks={self.sks}, status={self.status})")

class PenjadwalanSA:
    def __init__(self, initial_temperature, cooling_rate, max_iterations, id_generate):
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.id_generate = id_generate
        self.engine = create_engine('mysql+pymysql://root:@localhost/db_optimasi1')

        
        # Data penjadwalan
        self.daftar_dosen = []
        self.daftar_ruang = []
        self.daftar_matkul = []
        self.daftar_hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat']
        

        # Slot waktu 
        self.durasi_slot = timedelta(minutes=50)
        self.jam_mulai = datetime.strptime("07:00", "%H:%M")
        self.jam_selesai = datetime.strptime("19:05", "%H:%M")
        self.slot_istirahat = [
            (datetime.strptime("09:30", "%H:%M"), datetime.strptime("09:45", "%H:%M")),
            (datetime.strptime("12:15", "%H:%M"), datetime.strptime("12:45", "%H:%M")),
            (datetime.strptime("15:15", "%H:%M"), datetime.strptime("15:30", "%H:%M")),            
            (datetime.strptime("18:00", "%H:%M"), datetime.strptime("18:15", "%H:%M")),
        ]
        self.daftar_slot = []
        # self.setDataCsv()

        self.baca_datamk()
        self.baca_dataruang()

        # Generate slot waktu awal
        self.generate_slot_waktu() 

    def baca_datamk(self):
        query = text("""
        SELECT tb_rombel.nama_kelas AS kelas,
            tb_matakuliah.nama_matakuliah AS matakuliah,
            tb_dosen.nama_dosen AS dosen,
            tb_matakuliah.sks AS sks,
            tb_matakuliah.status AS status,
            tb_matakuliah.kategori AS kategori,
            id_perkuliahan,
            id_semester
        FROM tb_perkuliahan
        JOIN tb_matakuliah ON tb_perkuliahan.kode_matakuliah = tb_matakuliah.kode_matakuliah
        JOIN tb_rombel ON tb_perkuliahan.id_kelasrombel = tb_rombel.id_kelasrombel
        JOIN tb_dosen ON tb_perkuliahan.kode_dosen = tb_dosen.kode_dosen
        JOIN tb_generate 
        ON tb_generate.id_generate = tb_rombel.id_generate 
        AND tb_generate.id_generate = tb_matakuliah.id_generate 
        AND tb_generate.id_generate = tb_dosen.id_generate
        WHERE tb_generate.status = 'belum' 
        AND tb_generate.id_generate = :id_generate
        """)
        with self.engine.connect() as connection:
            df_matkul = pd.read_sql_query(query, connection, params={"id_generate": self.id_generate})

        # Iterasi per baris untuk menambahkan data
        for _, row in df_matkul.iterrows():
            self.tambah_matkul(row['matakuliah'], row['dosen'], row['sks'], row['kelas'], row['status'], row['id_perkuliahan'],row['id_semester'],row['kategori'])
            

    def baca_dataruang(self):
        query = text("""
        SELECT nama_ruangan, 
            status_ruangan 
        FROM tb_ruang 
        JOIN tb_generate ON tb_ruang.id_generate = tb_generate.id_generate
        WHERE tb_generate.status = 'belum' 
        AND tb_generate.id_generate = :id_generate
        """)
        with self.engine.connect() as connection:
            df_ruang = pd.read_sql_query(query, connection,params={"id_generate": self.id_generate})

        # Iterasi per baris untuk menambahkan data
        for _, row in df_ruang.iterrows():
            self.tambah_ruang(row['nama_ruangan'], row['status_ruangan'])
            
        
    def tambah_dosen(self, nama):
        dosen = Dosen(nama)
        self.daftar_dosen.append(dosen)
        return dosen
    
    def tambah_ruang(self, nama, tiperuang):
        ruang = Ruang(nama,tiperuang)
        self.daftar_ruang.append(ruang)
        return ruang
    
    def tambah_matkul(self,matkul, dosen, sks, kelas, status, id_perkuliahan,id_semester,kategori):
        matkul = Matakuliah(matkul, dosen, sks, kelas, status, id_perkuliahan,id_semester,kategori) #tambahkan id_perkuliahan
        self.daftar_matkul.append(matkul)
        return matkul
    
    def tambah_hari(self,hari):
        hari = Hari(hari)
        self.daftar_hari.append(hari)
        return hari

    def generate_slot_waktu(self):
        self.daftar_slot.clear()
        waktu_mulai = self.jam_mulai

        while waktu_mulai + self.durasi_slot <= self.jam_selesai:
            waktu_selesai = waktu_mulai + self.durasi_slot

            konflik_istirahat = False
            for istirahat_mulai, istirahat_selesai in self.slot_istirahat:
                if not (waktu_selesai <= istirahat_mulai or waktu_mulai >= istirahat_selesai):
                    # Slot tumpang tindih dengan istirahat
                    waktu_mulai = istirahat_selesai  # lanjut setelah istirahat
                    konflik_istirahat = True
                    break

            if not konflik_istirahat:
                self.daftar_slot.append((waktu_mulai.strftime("%H:%M"), waktu_selesai.strftime("%H:%M")))
                waktu_mulai = waktu_selesai

    def hitung_sks(self, sks, kategori):
        if kategori == "Teori":
            return sks 
        elif kategori == "Praktikum":
            return sks * 3
        elif kategori == "Gabungan":
            return 7 
        return  0
    
    def get_ruang(self,kategori):
        if kategori == "Teori":
            return {"Kelas"} 
        elif kategori == "Praktikum":
            return {"Lab"} 
        elif kategori == "Gabungan":
            return {"Lab"}  
        return set()

    def solusi_awal(self):
        jadwal_awal = []
        self.generate_slot_waktu()
        
        class_schedule = {}  # Menyimpan jadwal kelas yang sudah ada
        
        for matkul in self.daftar_matkul:
            tipe_valid = self.get_ruang(matkul.kategori)
            ruang_valid = [ruang for ruang in self.daftar_ruang if ruang.tipe_ruang in tipe_valid]
            if ruang_valid:
                ruang = random.choice(ruang_valid)
                hari = random.choice(self.daftar_hari)
                
                sukses = False
                for _ in range(1000):  # Dulu 100, sekarang 1000 agar lebih banyak mencoba
                    waktu_mulai = random.randint(0, len(self.daftar_slot) - self.hitung_sks(matkul.sks, matkul.kategori))
                    waktu_selesai = waktu_mulai + self.hitung_sks(matkul.sks, matkul.kategori)
                    waktu = (waktu_mulai, waktu_selesai)

                    class_key = (matkul.kelas, hari)
                    if class_key not in class_schedule:
                        class_schedule[class_key] = []

                    conflict = False
                    for existing_slot in class_schedule[class_key]:
                        if not (waktu_selesai <= existing_slot[0] or waktu_mulai >= existing_slot[1]):
                            conflict = True
                            break

                    if not conflict:
                        class_schedule[class_key].append(waktu)
                        jadwal_awal.append((matkul, ruang, hari, waktu))
                        sukses = True
                        break

                if not sukses:
                    # Tandai sebagai gagal dijadwalkan
                    jadwal_awal.append((matkul, ruang, hari, (-1, -1)))
        return jadwal_awal

    def evaluate_solution(self, solution):
        score = 0
        slot_used = {}
        class_schedule = {}

        for matkul, ruang, hari, waktu in solution:
            if waktu == (-1, -1):
                score += 1000  # Penalti sangat tinggi agar SA memprioritaskan perbaikannya
                continue

            slot_key = (ruang.nama, hari, waktu)
            class_key = (matkul.kelas, hari)

            # Cek konflik ruang
            if slot_key in slot_used:
                score += 5
            else:
                slot_used[slot_key] = True

            # Cek konflik jadwal kelas
            if class_key not in class_schedule:
                class_schedule[class_key] = []
            
            waktu_mulai, waktu_selesai = waktu
            conflict = False
            for existing_start, existing_end in class_schedule[class_key]:
                if not (waktu_selesai <= existing_start or waktu_mulai >= existing_end):
                    conflict = True
                    break

            if conflict:
                score += 10
            else:
                class_schedule[class_key].append((waktu_mulai, waktu_selesai))

        return score

    def get_neighbor(self, solution):
        neighbor = solution[:]

        # Prioritaskan yang gagal dijadwalkan (waktu == (-1, -1))
        index_gagal = [i for i, (_, _, _, waktu) in enumerate(neighbor) if waktu == (-1, -1)]

        if index_gagal:
            idx = random.choice(index_gagal)
        else:
            idx = random.randint(0, len(solution) - 1)

        matkul, _, _, _ = neighbor[idx]

        # Cari ruang yang sesuai
        tipe_valid = self.get_ruang(matkul.kategori)
        ruang_valid = [r for r in self.daftar_ruang if r.tipe_ruang in tipe_valid]
        
        if not ruang_valid:
            return neighbor  # Tidak ada ruang valid, tidak bisa perbaiki

        ruang = random.choice(ruang_valid)
        hari = random.choice(self.daftar_hari)

        max_start_index = len(self.daftar_slot) - self.hitung_sks(matkul.sks, matkul.kategori)
        if max_start_index <= 0:
            waktu = (-1, -1)
        else:
            waktu_mulai = random.randint(0, max_start_index)
            waktu_selesai = waktu_mulai + self.hitung_sks(matkul.sks, matkul.kategori)
            waktu = (waktu_mulai, waktu_selesai)

        # Perbarui
        neighbor[idx] = (matkul, ruang, hari, waktu)
        return neighbor

    def anneal(self):
        current_solution = self.solusi_awal()
        current_score = self.evaluate_solution(current_solution)
        best_solution, best_score = current_solution, current_score
        temperature = self.initial_temperature

        for iteration in range(self.max_iterations):
            if temperature <= 0:
                break

            neighbor_solution = self.get_neighbor(current_solution)
            neighbor_score = self.evaluate_solution(neighbor_solution)

            delta_score = neighbor_score - current_score
            acceptance_probability = math.exp(-delta_score / temperature) if delta_score > 0 else 1

            if random.random() < acceptance_probability:
                current_solution, current_score = neighbor_solution, neighbor_score
                if current_score < best_score:
                    best_solution, best_score = current_solution, current_score

            temperature *= self.cooling_rate

        return best_solution, best_score

    def tampilkan_jadwal(self, solution):
        jadwal_terjadwal = {}

        for matkul, ruang, hari, waktu in solution:
            if hari not in jadwal_terjadwal:
                jadwal_terjadwal[hari] = []
            jadwal_terjadwal[hari].append((matkul, ruang, waktu))

        for hari, jadwal in sorted(jadwal_terjadwal.items()):
            print(f"\nHari: {hari}")
            for matkul, ruang, waktu in sorted(jadwal, key=lambda x: x[2][0]):  # Urutkan berdasarkan waktu mulai
                waktu_mulai = self.daftar_slot[waktu[0]][0]  # Ambil waktu mulai dari daftar slot
                waktu_selesai = self.daftar_slot[waktu[1] - 1][1]  # Ambil waktu selesai dari daftar slot
                
                print(f"  Slot: {waktu_mulai} - {waktu_selesai}, "
                    f"Kelas: {matkul.kelas}, "
                    f"Mata Kuliah: {matkul.matkul}, "
                    f"Dosen: {matkul.dosen}, "
                    f"Ruang: {ruang.nama}")
    
    def tampilkan_slot_waktu(self):
        print("Daftar Slot Waktu:")
        for i, slot in enumerate(self.daftar_slot, 1):
            print(f"{i}. {slot[0]} - {slot[1]}")

        
    def simpan_optimasi(self, df, table_name='tb_hasil'):
        df.to_sql(table_name, con=self.engine, if_exists='append', index=False)
        print(f'Data berhasil disimpan ke database {table_name}')
        with self.engine.begin() as conn:
            query = text("UPDATE tb_generate SET status = :status WHERE id_generate = :id_generate")
            conn.execute(query, {"status": "sudah", "id_generate": self.id_generate})
            
    def df_jadwaloptimasi(self, solution):
        data = []
        for matkul, ruang, hari, waktu in solution:
            waktu_mulai = self.daftar_slot[waktu[0]][0]  # Ambil waktu mulai dari daftar slot
            waktu_selesai = self.daftar_slot[waktu[1] - 1][1]  # Ambil waktu selesai dari daftar slot

            data.append({
                "id_perkuliahan" : matkul.id_perkuliahan,
                "hari": hari,
                "waktu_mulai": waktu_mulai,
                "waktu_selesai": waktu_selesai,
                "kelas": matkul.kelas,
                "mata_kuliah": matkul.matkul,
                "nama_dosen": matkul.dosen,
                "ruang": ruang.nama,
                "semester":matkul.id_semester,
            })

        df_jadwal = pd.DataFrame(data)
        return df_jadwal

# sa = PenjadwalanSA()

# best_solution, best_score = sa.anneal()

# df_jadwal = sa.df_jadwaloptimasi(best_solution) 
# print(df_jadwal)
# sa.simpan_optimasi(df_jadwal)