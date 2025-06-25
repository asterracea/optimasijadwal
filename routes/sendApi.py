import pandas as pd
import requests
from sqlalchemy import create_engine,text
from config import db_url

def sendApi(id_generate,token,uri):
    try:
        query = """SELECT h.hari, h.jam_mulai, h.jam_selesai,h.kelas, h.mata_kuliah, h.nama_dosen, h.ruang, h.semester, p.temp_perkuliahan FROM tb_hasil h JOIN tb_perkuliahan p ON h.id_perkuliahan = p.id_perkuliahan WHERE p.id_generate = :id_generate""" #ubah berdasarkan id generate lalu kirim hasil
        with db_url.connect() as conn:
            df_jadwal = pd.read_sql(text(query), conn, params={"id_generate": id_generate})
        
        payload =  df_jadwal.to_dict(orient="records")

        # json_payload = json.dumps(payload, ensure_ascii=False)

        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json',
        }
        response = requests.post(uri, json=payload, headers=headers)
        print("Status code:", response.status_code)

        if response.headers.get('Content-Type', '').startswith('application/json'):
            data = response.json()
            print("Respon dari server:", data.get("message", "Tidak ada pesan"))
        else:
            print("Isi respons (bukan JSON):", response.text)

    except Exception as e:
        print(f"Gagal mengirim data: {str(e)}")


