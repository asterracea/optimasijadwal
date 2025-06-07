import pandas as pd
import requests
from sqlalchemy import create_engine,text
from config import db_url

def sendApi(id_generate,token,uri):
    query = """SELECT h.hari, h.waktu_mulai, h.waktu_selesai,h.kelas, h.mata_kuliah, h.nama_dosen, h.ruang, h.semester, p.temp_perkuliahan FROM tb_hasil h JOIN tb_perkuliahan p ON h.id_perkuliahan = p.id_perkuliahan WHERE p.id_generate = :id_generate""" #ubah berdasarkan id generate lalu kirim hasil
    df_jadwal = pd.read_sql(text(query), db_url, params={"id_generate": id_generate})
    
    payload =  df_jadwal.to_dict(orient="records")
    print(payload)

    # json_payload = json.dumps(payload, ensure_ascii=False)

    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
    }


    try:
        response = requests.post(uri, json=payload, headers=headers)
        print("Status code:", response.status_code)
        print("Content-Type:", response.headers.get('Content-Type'))
        print("payload")
        
        try:
            data = response.json()
            print("Respon dari server:",data.get("message", "Tidak ada pesan"))
        except ValueError:
            print("Respons bukan JSON. Isi respons:", response.text)
    except Exception as e:
        print("Gagal mengirim:", e)


