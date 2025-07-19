
from sqlalchemy import text
import requests
import random
from datetime import datetime, timedelta
import time
import math
from collections import defaultdict
import pandas as pd
from config import db_url

class Ruang:
    def __init__(self, nama, tipe_ruang): #membuat objek dari kelas, inisialisasi nilai awal dari atribut objek
        self.nama = nama
        self.tipe_ruang = tipe_ruang
        self.jadwal = defaultdict(lambda: defaultdict(lambda: None))
    
    def __repr__(self): #untuk cetak string tanpa keteranagn main
        return f"Ruang(nama={self.nama}, tipe_ruang={self.tipe_ruang})"
class Dosen:
    def __init__(self, nama): #membuat objek dari kelas, inisialisasi nilai awal dari atribut objek
        self.nama = nama
        self.jadwal = defaultdict(lambda: defaultdict(lambda: None))
    def __repr__(self):
        return f"Dosen(nama={self.nama})"

class Matakuliah:
    def __init__(self, matkul, dosen, sks, kelas, id_perkuliahan, id_semester, semester,kategori,prodi,status = None): #tambah id_perkuliahan
        self.id_perkuliahan = id_perkuliahan
        self.matkul = matkul
        self.dosen = dosen
        self.sks = sks
        self.status = status
        self.kelas = kelas
        self.id_semester = id_semester
        self.semester = semester
        self.kategori = kategori
        self.prodi=prodi
        self.butuh_tipe = self.set_ruang(kategori,status)

    def __repr__(self):
        return (f"matkul(matkul={self.matkul}, dosen={self.dosen}, sks={self.sks}, status={self.status})")
    
    def set_ruang(self, kategori, status = None):
        if kategori == "Teori":
            return [status] if status else ["Kelas"]
        elif kategori == "Praktikum":
            return ["Lab"]
        elif kategori == "Gabungan":
            return [status] if status else ["Kelas", "Lab"]
        else:
            return []
        
class PenjadwalanSA:
    def __init__(self, initial_temperature, cooling_rate, max_iterations, id_generate): #membuat objek dari kelas, inisialisasi nilai awal dari atribut objek
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.id_generate = id_generate
        self.engine = db_url
        
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
        self.daftar_slot = self.generate_slot_waktu()
        self.prodi_jadwal = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None))))

        self.baca_datamk()
        self.baca_dataruang()

    def baca_datamk(self):
        query = text("""
        WITH filtered_generate AS (
            SELECT id_generate
            FROM tb_generate
            WHERE tb_generate.status = 'belum' AND tb_generate.id_generate = :id_generate
        )
        SELECT 
            tb_rombel.nama_kelas AS kelas,
            tb_matakuliah.nama_matakuliah AS matakuliah,
            tb_dosen.nama_dosen AS dosen,
            tb_matakuliah.sks AS sks,
            tb_matakuliah.status AS status,
            tb_matakuliah.kategori AS kategori,
            tb_perkuliahan.id_perkuliahan,
            tb_perkuliahan.id_semester,
            tb_matakuliah.nama_semester AS semester,
            tb_prodi.nama_prodi AS prodi
        FROM filtered_generate g
        JOIN tb_rombel ON g.id_generate = tb_rombel.id_generate
        JOIN tb_perkuliahan ON tb_perkuliahan.id_kelasrombel = tb_rombel.id_kelasrombel
        JOIN tb_matakuliah ON tb_perkuliahan.kode_matakuliah = tb_matakuliah.kode_matakuliah AND tb_matakuliah.id_generate = g.id_generate
        JOIN tb_dosen ON tb_perkuliahan.kode_dosen = tb_dosen.kode_dosen AND tb_dosen.id_generate = g.id_generate
        JOIN tb_prodi ON tb_perkuliahan.kode_prodi = tb_prodi.kode_prodi AND tb_prodi.id_generate = g.id_generate;
        
        """)
        with self.engine.connect() as connection:
            df_matkul = pd.read_sql_query(query, connection, params={"id_generate": self.id_generate})
        
        
        # Iterasi per baris untuk menambahkan data
        for row in df_matkul.itertuples(index=False):
            dosen_obj = self.tambah_dosen(row.dosen)

            self.tambah_matkul(
                    row.matakuliah, dosen_obj, row.sks, row.kelas, row.status,
                    row.id_perkuliahan, row.id_semester, row.semester, row.kategori, row.prodi
                )
    def baca_datadosen(self):
        query = text("""
            SELECT nama_dosen AS dosen
            FROM tb_dosen
            JOIN tb_generate ON tb_dosen.id_generate = tb_generate.id_generate
            WHERE tb_generate.status = 'belum' 
            AND tb_generate.id_generate = :id_generate
        """)

        with self.engine.connect() as connection:
            df_dosen = pd.read_sql_query(query, connection,params={"id_generate": self.id_generate})
        for row in df_dosen.itertuples(index=False):
            self.tambah_dosen(row.dosen)

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
        for row in df_ruang.itertuples(index=False):
            self.tambah_ruang(row.nama_ruangan, row.status_ruangan)
            
        
    def tambah_dosen(self, nama):
        for d in self.daftar_dosen:
            if d.nama == nama:
                return d
        dosen = Dosen(nama)
        self.daftar_dosen.append(dosen)
        return dosen
    
    def tambah_ruang(self, nama, tiperuang):
        ruang = Ruang(nama,tiperuang)
        self.daftar_ruang.append(ruang)
        return ruang
    
    def tambah_matkul(self,matkul, dosen, sks, kelas, status,id_perkuliahan,id_semester,semester,kategori,prodi):
        matkul = Matakuliah(matkul, dosen, sks, kelas, id_perkuliahan, id_semester,semester,kategori,prodi,status) #tambahkan id_perkuliahan
        self.daftar_matkul.append(matkul)
        return matkul

    def generate_slot_waktu(self):
        daftar_slot = []
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
                daftar_slot.append((
                    waktu_mulai.strftime("%H:%M"),
                    waktu_selesai.strftime("%H:%M")
                ))
                waktu_mulai = waktu_selesai
        return daftar_slot

    def jam_sks(self, sks, kategori):
        if kategori == "Teori":
            menit_total = sks * 50
        elif kategori == "Praktikum":
            menit_total = sks * 150
        elif kategori == "Gabungan":
            menit_total = 350 
        else:
            menit_total = 0
        return math.ceil(menit_total / 50)
    
    def get_ruang_valid(self, matkul):
        if matkul.matkul == "Praktik Jaringan Komputer" and matkul.status == "Lab":
            for ruang in self.daftar_ruang:
                if ruang.nama == "Lab 216":
                    return ruang

        if matkul.matkul == "Jaringan Komputer" and matkul.status == "Lab":
            for ruang in self.daftar_ruang:
                if ruang.nama == "Lab 216":
                    return ruang

        ruang_valid = [ruang for ruang in self.daftar_ruang if not matkul.butuh_tipe or any(tipe in ruang.tipe_ruang for tipe in matkul.butuh_tipe)]
        
        return random.choice(ruang_valid) if ruang_valid else random.choice(self.daftar_ruang)

    def anneal(self):
        current_solution = self.solusi_awal()
        current_score = self.evaluate_solution(current_solution)
        best_solution = current_solution
        best_score = current_score
        temperature = self.initial_temperature

        for i in range(self.max_iterations):
            neighbor_solution = self.get_neighbor(current_solution)
            neighbor_score = self.evaluate_solution(neighbor_solution)

            delta_score = neighbor_score - current_score
            acceptance_probability = math.exp(-delta_score / temperature) if delta_score > 0 else 1

            if random.random() < acceptance_probability:
                current_solution, current_score = neighbor_solution, neighbor_score
                if current_score < best_score:
                    best_solution, best_score = current_solution, current_score

            temperature *= self.cooling_rate
            if i % 10000 == 0:
                print(f"Iterasi {i} | Skor saat ini: {current_score} | Skor terbaik: {best_score} | Temperatur: {temperature:.4f}")

        self.apply_solution(best_solution)
        self.best_solution = best_solution 


    def solusi_awal(self):
        solusi = []
        for matkul in self.daftar_matkul:
            ruang = self.get_ruang_valid(matkul)
            hari = random.choice(self.daftar_hari)
            durasi = self.jam_sks(matkul.sks, matkul.kategori)
            max_jam_mulai = len(self.daftar_slot) - durasi

            if max_jam_mulai <= 0:
                print(f"Matkul {matkul.matkul} ({durasi} slot) tidak muat dalam hari (slot tersedia: {len(self.daftar_slot)})")
                continue  # Skip matkul yang tidak muat

            jam_mulai = random.randint(0, max_jam_mulai)
            solusi.append((matkul, ruang, hari, jam_mulai))
        return solusi
    
    def get_neighbor(self, solusi):
        neighbor = solusi.copy()
        index = random.randint(0, len(neighbor) - 1)
        matkul, _, _, _ = neighbor[index]
        ruang = self.get_ruang_valid(matkul)
        hari = random.choice(self.daftar_hari)
        jam_mulai = random.randint(0, len(self.daftar_slot) - self.jam_sks(matkul.sks,matkul.kategori))
        neighbor[index] = (matkul, ruang, hari, jam_mulai)
        return neighbor
    
    def evaluate_solution(self, solusi):
        score = 0
        for i, (mk1, r1, h1, j1) in enumerate(solusi):
            durasi1 = self.jam_sks(mk1.sks,mk1.kategori)
            if mk1.butuh_tipe and not any(tipe in r1.tipe_ruang for tipe in mk1.butuh_tipe):
                print(f"[!] MK {mk1.matkul} butuh {mk1.butuh_tipe}, tapi ditempatkan di {r1.nama} ({r1.tipe_ruang})")
                score += 10  
            for mk2, r2, h2, j2 in solusi[i+1:]:
                durasi2 = self.jam_sks(mk2.sks,mk2.kategori)
                if h1 == h2:
                    if r1 == r2 and max(j1, j2) < min(j1 + durasi1, j2 + durasi2):
                        score += 1
                    if mk1.dosen == mk2.dosen and max(j1, j2) < min(j1 + durasi1, j2 + durasi2):
                        score += 1
                    if mk1.prodi == mk2.prodi and mk1.semester == mk2.semester and max(j1, j2) < min(j1 + durasi1, j2 + durasi2):
                        score += 1
        return score
    
    def apply_solution(self, solusi):
        self.reset_jadwal()
        for matkul, ruang, hari, jam_mulai in solusi:
            durasi = self.jam_sks(matkul.sks,matkul.kategori)
            for i in range(durasi):
                if jam_mulai + i < len(self.daftar_slot):  # pastikan jam_list
                    ruang.jadwal[hari][jam_mulai + i] = matkul
                    matkul.dosen.jadwal[hari][jam_mulai + i] = matkul
                    self.prodi_jadwal[matkul.prodi][matkul.semester][hari][jam_mulai + i] = matkul

    def reset_jadwal(self):
        for ruang in self.daftar_ruang:
            ruang.jadwal = defaultdict(lambda: defaultdict(lambda: None))
        for dosen in self.daftar_dosen:
            dosen.jadwal = defaultdict(lambda: defaultdict(lambda: None))
        self.prodi_jadwal = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None))))
    
    def generate_jadwal(self):
        self.anneal()
        return self.best_solution
    
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
            
    def df_hasiljadwal(self, solusi):
        data=[]
        for matkul, ruang, hari, jam_mulai in solusi:
            durasi = self.jam_sks(matkul.sks, matkul.kategori)

            waktu_mulai = self.daftar_slot[jam_mulai][0]
            waktu_selesai = self.daftar_slot[jam_mulai + durasi - 1][1]         

            data.append({
                'id_perkuliahan': matkul.id_perkuliahan,
                'hari': hari,
                'jam_mulai': waktu_mulai,
                'jam_selesai': waktu_selesai,
                'kelas': matkul.kelas,
                'mata_kuliah': matkul.matkul,
                'nama_dosen': matkul.dosen.nama,
                'ruang': ruang.nama if hasattr(ruang, 'nama') else ruang,
                'semester': matkul.semester
            })
        df = pd.DataFrame(data)
        return df
