
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
    def __init__(self, nama, tipe_ruang):
        self.nama = nama
        self.tipe_ruang = tipe_ruang
        self.jadwal = defaultdict(lambda: defaultdict(lambda: None))
    
    def __repr__(self):
        return f"Ruang(nama={self.nama}, tipe_ruang={self.tipe_ruang})"
class Dosen:
    def __init__(self, nama):
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
        self.ruang_needed = self.set_ruang(kategori,status)

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
    def __init__(self, initial_temperature, cooling_rate, max_iterations, id_generate):
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
        SELECT tb_rombel.nama_kelas AS kelas,
            tb_matakuliah.nama_matakuliah AS matakuliah,
            tb_dosen.nama_dosen AS dosen,
            tb_matakuliah.sks AS sks,
            tb_matakuliah.status AS status,
            tb_matakuliah.kategori AS kategori,
            tb_matakuliah.kode_matakuliah AS kode_mk,  
            tb_matakuliah.kode_pasangan AS kode_pasangan,
            id_perkuliahan,
            id_semester,
            tb_matakuliah.nama_semester AS semester,
            tb_prodi.nama_prodi AS prodi
        FROM tb_perkuliahan                    
        JOIN tb_matakuliah ON tb_perkuliahan.kode_matakuliah = tb_matakuliah.kode_matakuliah
        JOIN tb_rombel ON tb_perkuliahan.id_kelasrombel = tb_rombel.id_kelasrombel
        JOIN tb_dosen ON tb_perkuliahan.kode_dosen = tb_dosen.kode_dosen
        JOIN tb_generate ON tb_generate.id_generate = tb_rombel.id_generate
        JOIN tb_prodi ON tb_perkuliahan.kode_prodi = tb_prodi.kode_prodi
        AND tb_generate.id_generate = tb_matakuliah.id_generate 
        AND tb_generate.id_generate = tb_dosen.id_generate
        AND tb_generate.id_generate = tb_prodi.id_generate
        WHERE tb_generate.status = 'belum' 
        AND tb_generate.id_generate = :id_generate
        """)
        with self.engine.connect() as connection:
            df_matkul = pd.read_sql_query(query, connection, params={"id_generate": self.id_generate})

        # Iterasi per baris untuk menambahkan data
        for _, row in df_matkul.iterrows():
            dosen_obj = self.tambah_dosen(row['dosen'])
            self.tambah_matkul(
                row['matakuliah'], dosen_obj, row['sks'], row['kelas'], 
                row['status'], row['id_perkuliahan'], row['id_semester'], 
                row['semester'], row['kategori'], row['prodi'], 
                row['kode_mk'], row['kode_pasangan']
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
        for _, row in df_dosen.iterrows():
            self.tambah_dosen(row['dosen'])

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
    
    def tambah_matkul(self, matkul, dosen, sks, kelas, status, id_perkuliahan, id_semester, semester, kategori, prodi, kode_mk=None, kode_pasangan=None):
        matkul = Matakuliah(matkul, dosen, sks, kelas, id_perkuliahan, id_semester, semester, kategori, prodi, status, kode_mk, kode_pasangan)
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
    
    def get_ruang_valid(self,matkul):
        ruang_valid = [ruang for ruang in self.daftar_ruang if not matkul.ruang_needed or any(t in ruang.tipe_ruang for t in matkul.ruang_needed)]
        return random.choice(ruang_valid) if ruang_valid else random.choice(self.daftar_ruang)

    def find_paired_course(self, matkul):
        if not matkul.kode_pasangan:
            return None
        
        for mk in self.daftar_matkul:
            if mk.kode_mk == matkul.kode_pasangan:
                return mk
        return None
    
    def is_paired_courses(self, mk1, mk2):
        return (mk1.kode_pasangan == mk2.kode_mk or mk2.kode_pasangan == mk1.kode_mk)

    # def is_paired_courses(self, mk1, mk2):
    #     return (mk1.kode_pasangan == mk2.kode_mk and 
    #             mk2.kode_pasangan == mk1.kode_mk)

    def anneal(self):
        current_solution = self.solusi_awal()
        current_energy = self.calculate_energy(current_solution)
        best_solution = current_solution
        best_energy = current_energy
        temperature = self.initial_temperature

        for i in range(self.max_iterations):
            neighbor_solution = self.get_neighbor(current_solution)
            neighbor_energy = self.calculate_energy(neighbor_solution)

            if self.accept_probability(current_energy, neighbor_energy, temperature) > random.random():
                current_solution = neighbor_solution
                current_energy = neighbor_energy

            if current_energy < best_energy:
                best_solution = current_solution
                best_energy = current_energy

            temperature *= self.cooling_rate
            if i % 10000 == 0:
                print(f"Iterasi {i} | Skor saat ini: {current_energy} | Skor terbaik: {best_energy} | Temperatur: {temperature:.4f}")

        self.apply_solution(best_solution)
        self.best_solution = best_solution 


    def solusi_awal(self):
        solution = []
        scheduled_courses = set()  # Track kode_mk mata kuliah yang sudah dijadwalkan
        
        for matkul in self.daftar_matkul:
            if matkul.kode_mk in scheduled_courses:
                continue  # Skip jika sudah dijadwalkan sebagai pasangan
                
            paired_course = self.find_paired_course(matkul)
            
            if paired_course and paired_course.kode_mk not in scheduled_courses:
                # Jadwalkan mata kuliah berpasangan berurutan
                durasi_mk1 = self.jam_sks(matkul.sks, matkul.kategori)
                durasi_mk2 = self.jam_sks(paired_course.sks, paired_course.kategori)
                total_durasi = durasi_mk1 + durasi_mk2
                
                max_jam_mulai = len(self.daftar_slot) - total_durasi
                
                if max_jam_mulai > 0:
                    ruang1 = self.get_ruang_valid(matkul)
                    ruang2 = self.get_ruang_valid(paired_course)
                    hari = random.choice(self.daftar_hari)
                    jam_mulai1 = random.randint(0, max_jam_mulai)
                    jam_mulai2 = jam_mulai1 + durasi_mk1
                    
                    solution.append((matkul, ruang1, hari, jam_mulai1))
                    solution.append((paired_course, ruang2, hari, jam_mulai2))
                    
                    scheduled_courses.add(matkul.kode_mk)
                    scheduled_courses.add(paired_course.kode_mk)
                else:
                    print(f"Mata kuliah berpasangan {matkul.matkul} dan {paired_course.matkul} tidak muat dalam satu hari")
                    # Jadwalkan terpisah jika tidak muat
                    ruang = self.get_ruang_valid(matkul)
                    hari = random.choice(self.daftar_hari)
                    jam_mulai = random.randint(0, len(self.daftar_slot) - durasi_mk1)
                    solution.append((matkul, ruang, hari, jam_mulai))
                    scheduled_courses.add(matkul.kode_mk)
            else:
                # Mata kuliah biasa tanpa pasangan
                ruang = self.get_ruang_valid(matkul)
                hari = random.choice(self.daftar_hari)
                durasi = self.jam_sks(matkul.sks, matkul.kategori)
                max_jam_mulai = len(self.daftar_slot) - durasi
                
                if max_jam_mulai <= 0:
                    print(f"Matkul {matkul.matkul} ({durasi} slot) tidak muat dalam hari (slot tersedia: {len(self.daftar_slot)})")
                    continue
                    
                jam_mulai = random.randint(0, max_jam_mulai)
                solution.append((matkul, ruang, hari, jam_mulai))
                scheduled_courses.add(matkul.kode_mk)
        
        return solution
    
    def get_neighbor(self, solution):
        neighbor = solution.copy()
        index = random.randint(0, len(neighbor) - 1)
        matkul, _, _, _ = neighbor[index]
        
        # Cek apakah mata kuliah ini memiliki pasangan
        paired_course = self.find_paired_course(matkul)
        
        if paired_course:
            # Jika ada pasangan, jadwalkan keduanya berurutan
            durasi_mk1 = self.jam_sks(matkul.sks, matkul.kategori)
            durasi_mk2 = self.jam_sks(paired_course.sks, paired_course.kategori)
            total_durasi = durasi_mk1 + durasi_mk2
            
            # Pastikan ada cukup slot untuk kedua mata kuliah
            max_jam_mulai = len(self.daftar_slot) - total_durasi
            if max_jam_mulai > 0:
                ruang1 = self.get_ruang_valid(matkul)
                ruang2 = self.get_ruang_valid(paired_course)
                hari = random.choice(self.daftar_hari)
                jam_mulai1 = random.randint(0, max_jam_mulai)
                jam_mulai2 = jam_mulai1 + durasi_mk1
                
                # Update kedua mata kuliah
                neighbor[index] = (matkul, ruang1, hari, jam_mulai1)
                
                # Cari dan update mata kuliah pasangan
                for i, (mk, _, _, _) in enumerate(neighbor):
                    if mk == paired_course:
                        neighbor[i] = (paired_course, ruang2, hari, jam_mulai2)
                        break
            else:
                # Jika tidak cukup slot, gunakan cara biasa
                ruang = self.get_ruang_valid(matkul)
                hari = random.choice(self.daftar_hari)
                jam_mulai = random.randint(0, len(self.daftar_slot) - self.jam_sks(matkul.sks, matkul.kategori))
                neighbor[index] = (matkul, ruang, hari, jam_mulai)
        else:
            # Mata kuliah biasa tanpa pasangan
            ruang = self.get_ruang_valid(matkul)
            hari = random.choice(self.daftar_hari)
            jam_mulai = random.randint(0, len(self.daftar_slot) - self.jam_sks(matkul.sks, matkul.kategori))
            neighbor[index] = (matkul, ruang, hari, jam_mulai)
        
        return neighbor
    
    def calculate_energy(self, solution):
        conflicts = 0
        
        # Existing conflict checks
        for i, (mk1, r1, h1, j1) in enumerate(solution):
            slots_needed1 = self.jam_sks(mk1.sks, mk1.kategori)
            
            if mk1.ruang_needed and not any(t in r1.tipe_ruang for t in mk1.ruang_needed):
                conflicts += 10
                
            for mk2, r2, h2, j2 in solution[i+1:]:
                slots_needed2 = self.jam_sks(mk2.sks, mk2.kategori)
                
                if h1 == h2:
                    if r1 == r2 and max(j1, j2) < min(j1 + slots_needed1, j2 + slots_needed2):
                        conflicts += 1
                    if mk1.dosen == mk2.dosen and max(j1, j2) < min(j1 + slots_needed1, j2 + slots_needed2):
                        conflicts += 1
                    if mk1.prodi == mk2.prodi and mk1.semester == mk2.semester and max(j1, j2) < min(j1 + slots_needed1, j2 + slots_needed2):
                        conflicts += 1
        
        # Tambahan: Penalti untuk mata kuliah berpasangan yang tidak berurutan
        for i, (mk1, r1, h1, j1) in enumerate(solution):
            paired_course = self.find_paired_course(mk1)
            if paired_course:
                # Cari jadwal mata kuliah pasangan
                for mk2, r2, h2, j2 in solution:
                    if mk2 == paired_course:
                        slots_needed1 = self.jam_sks(mk1.sks, mk1.kategori)
                        
                        # Penalti jika tidak di hari yang sama
                        if h1 != h2:
                            conflicts += 5
                        # Penalti jika tidak berurutan (mata kuliah kedua tidak langsung setelah yang pertama)
                        elif j1 + slots_needed1 != j2:
                            conflicts += 3
                        break
        
        return conflicts
    
    def accept_probability(self, current_energy, neighbor_energy, temperature):
        if neighbor_energy < current_energy:
            return 1.0
        return math.exp((current_energy - neighbor_energy) / temperature)
    
    def apply_solution(self, solution):
        self.reset_jadwal()
        for matkul, ruang, hari, jam_mulai in solution:
            slots_needed = self.jam_sks(matkul.sks,matkul.kategori)
            for i in range(slots_needed):
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
            
    def df_hasiljadwal(self, solution):
        data=[]
        for matkul, ruang, hari, jam_mulai in solution:
            butuh_slot = self.jam_sks(matkul.sks, matkul.kategori)

            waktu_mulai = self.daftar_slot[jam_mulai][0]
            waktu_selesai = self.daftar_slot[jam_mulai + butuh_slot - 1][1]         

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
