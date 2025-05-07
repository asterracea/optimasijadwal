import pandas as pd
import requests
from sqlalchemy import create_engine
import json

def sendApi():
    db = 'mysql+pymysql://root:@localhost/db_optimasi1'
    engine = create_engine(db)

    df_jadwal = pd.read_sql("SELECT hari, waktu_mulai, waktu_selesai, FROM tb_hasil", engine) #ubah berdasarkan id generate lalu kirim hasil

    # Ubah ke format dict
    payload = {
        "setjadwal": df_jadwal.to_dict(orient="records"),
    }
    
    send = 'http://192.168.21.173:8081/optimasi/callback'

    try:
        response = requests.post(send, json=payload)
        print("Status code:", response.status_code)
        # print("Raw response text:", repr(response.text))
        print("Content-Type:", response.headers.get('Content-Type'))
        
        try:
            data = response.json()
            print("Respon dari server:", data)
        except ValueError:
            print("Respons bukan JSON. Isi respons:", response.text)
    except Exception as e:
        print("Gagal mengirim:", e)
sendApi()

