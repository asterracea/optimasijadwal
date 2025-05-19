import pandas as pd
import requests
from sqlalchemy import create_engine

def sendApi():
    db = 'mysql+pymysql://root:@localhost/db_optimasi1'
    engine = create_engine(db)

    df_jadwal = pd.read_sql("SELECT h.hari, h.waktu_mulai, h.waktu_selesai,h.kelas, h.mata_kuliah, h.nama_dosen, h.ruang, h.semester, p.temp_perkuliahan FROM tb_hasil h JOIN tb_perkuliahan p ON h.id_perkuliahan = p.id_perkuliahan", engine) #ubah berdasarkan id generate lalu kirim hasil

    payload = {
        "setjadwal": df_jadwal.to_dict(orient="records"),
    }
    print(payload)

    # json_payload = json.dumps(payload, ensure_ascii=False)
    
    uri = 'http://10.252.1.114:8081/optimasi/callback'

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
sendApi()

