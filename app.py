from flask import Flask, render_template,request,jsonify
from routes.api import apiconn  # Import Blueprint
from model.conn import get_db_auth
import pandas as pd
from insertDB import simpanData
# from optimasi

app = Flask(__name__)

# Daftarkan Blueprint
app.register_blueprint(apiconn)

@app.route("/")
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def index():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_generate FROM tb_generate where status='belum'")
    id_generates = cursor.fetchall()
    conn.close()
    return render_template("dashboard.html", generates=id_generates, active_page='dashboard')

@app.route('/receive-json', methods=['POST'])
def receive_json():
    try: 
        data = request.get_json()
        # df_setjadwal = pd.DataFrame(data['setJadwal'])
        # df_setruang = pd.DataFrame(data['setRuang'])
        # df_setwaktu = pd.DataFrame(data['setWaktu'])
        # simpanData(df_setjadwal, df_setruang, df_setwaktu)
        print("Received JSON:", data)
        return jsonify({"status": "successss", "received": data}), 200
    except Exception as e:
        print("Error parsing JSON:", e)
        return jsonify({"status": "failed", "error": str(e)}), 400
    

    
@app.route('/callback', methods=['POST'])
def optimasi_callback():
    data = request.get_json()
    return jsonify({"status": "received", "data": data})
    
@app.route('/generate-jadwal', methods=['POST'])
def generate_jadwal():
    id_generate = request.form.get('id_generate')
    alpha = float(request.form.get('alpha'))
    suhuawal = float(request.form.get('suhuawal'))
    maxt = int(request.form.get('maxt'))

    # Jalankan Simulated Annealing
    sa = PenjadwalanSA(id_generate=id_generate, alpha=alpha, suhu_awal=suhuawal, max_iterasi=maxt)
    best_solution, best_score = sa.anneal()
    df_jadwal = sa.df_jadwaloptimasi(best_solution)

    # Simpan hasil ke database
    engine = create_engine('mysql+pymysql://root:@localhost/db_optimasi1')
    df_jadwal.to_sql('tb_hasil', con=engine, if_exists='append', index=False)

    flash('Jadwal berhasil digenerate!', 'success')
    return redirect(url_for('halaman_generate'))  # ganti dengan nama route tujuan


@app.route("/data/dosen")
def data_dosen():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_dosen")
    dosen_data = cursor.fetchall()
    conn.close()
    return render_template("data_dosen.html", dosens=dosen_data, active_page='data_dosen')

    
@app.route("/data/matakuliah")
def data_matakuliah():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_matakuliah")
    matkul_data = cursor.fetchall()
    conn.close()
    return render_template("data_matakuliah.html", matkuls=matkul_data, active_page='data_matakuliah')
@app.route("/data/perkuliahan")
def data_perkuliahan():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_perkuliahan")
    perkuliahan_data = cursor.fetchall()
    conn.close()
    return render_template("data_perkuliahan.html",perkuliahans=perkuliahan_data, active_page='data_perkuliahan')
@app.route("/data/generate")
def data_generate():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_generate")
    generate_data = cursor.fetchall()
    conn.close()
    return render_template("data_generate.html",generates=generate_data, active_page='data_generate')
@app.route("/data/ruang")
def data_ruang():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_ruang")
    ruang_data = cursor.fetchall()
    conn.close()
    return render_template("data_ruang.html",ruangs=ruang_data, active_page='data_ruang')
@app.route("/data/rombel")
def data_rombel():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_rombel")
    rombel_data = cursor.fetchall()
    conn.close()
    return render_template("data_rombel.html",rombels=rombel_data, active_page='data_rombel')
@app.route("/jadwal")
def data_hasil():
    conn = get_db_auth()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_hasil")
    jadwal_data = cursor.fetchall()
    conn.close()
    return render_template("data_hasiljadwal.html",jadwals=jadwal_data, active_page='hasil_jadwal')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
