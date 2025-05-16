from flask import Flask, render_template, request,redirect,jsonify,url_for,flash,make_response,session,logging
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import db_url  # Import Blueprint
from flask_bcrypt import Bcrypt
import pandas as pd
from insertDB import simpanData
from sqlalchemy import create_engine, text
from algoritma.optimasiSA import PenjadwalanSA


app = Flask(__name__)
app.secret_key = 'alieffiea' 
bcrypt = Bcrypt(app)



@app.route("/",methods=["GET", "POST"])
@app.route("/login", methods=["POST"])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password_input = request.form['password'].strip()
        print(f"[DEBUG] Email: {email}, Password: {password_input}")

        with db_url.connect() as connection:
            query = text("SELECT id_user, email, password, nama, role, status FROM tb_user WHERE email = :email")
            result = connection.execute(query, {"email": email}).fetchone()
            
            if result:
                id_user, email, password_hash, nama,role, status = result
                if status != 'aktif':
                    print(f"[DEBUG] User found: {email}, status: {status}")
                    flash("Akun Anda tidak aktif. Silakan hubungi admin.", "warning")
                    return redirect(url_for('login'))
                if bcrypt.check_password_hash(password_hash, password_input):
                    print("[DEBUG] Password cocok.")
                    session['id_user'] = id_user
                    session['email'] = email
                    session['nama'] = nama
                    session['role'] = role
                    flash("Login berhasil!", "success")
                    return redirect(url_for('index'))
                else:
                    print("[DEBUG] Password salah.")
                    flash("Password salah.", "danger")
            else:
                flash("Username tidak ditemukan.", "danger")
    return render_template('login.html')

@app.route("/dashboard")
def index():
    if 'id_user' not in session:
        flash("Silakan login terlebih dahulu.", "warning")
        return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT id_generate FROM tb_generate where status='belum'"))
        id_generates = result.mappings().all()
    return render_template("dashboard.html", generates=id_generates, active_page='dashboard')

@app.route('/generate-jadwal', methods=['GET','POST'])
def generate_jadwal():
    if request.method == 'POST':
        id_generate = request.form.get('id_generate')
        alpha = float(request.form.get('alpha'))
        suhuawal = float(request.form.get('suhuawal'))
        maxt = int(request.form.get('maxt'))

        # Jalankan Simulated Annealing
        sa = PenjadwalanSA(
                initial_temperature=suhuawal,
                cooling_rate=alpha,
                max_iterations=maxt,
                id_generate=id_generate
            )
        
        best_solution, best_score = sa.anneal()
        df_jadwal = sa.df_jadwaloptimasi(best_solution)
        jadwal_list = df_jadwal.to_dict(orient='records')
        sa.simpan_optimasi(df_jadwal)

        
        # flash('Jadwal berhasil digenerate!', 'success')
        return render_template('dashboard.html', data=jadwal_list)
    return redirect(url_for('index'))

@app.route('/receive-json', methods=['POST'])
def receive_json():
    try: 
        data = request.get_json()
        simpanData(data)
        return jsonify({"status": "successss"}), 200
    except Exception as e:
        print("Error parsing JSON:", e)
        return jsonify({"status": "failed", "error": str(e)}), 400
    
@app.route('/callback', methods=['POST'])
def optimasi_callback():
    data = request.get_json()
    return jsonify({"status": "received", "data": data})
    

@app.route("/data/dosen")
def data_dosen():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_dosen"))
        dosen_data = result.mappings().all()
    return render_template("data_dosen.html", dosens=dosen_data, active_page='data_dosen')

    
@app.route("/data/matakuliah")
def data_matakuliah():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_matakuliah"))
        matkul_data = result.mappings().all()
    return render_template("data_matakuliah.html", matkuls=matkul_data, active_page='data_matakuliah')
@app.route("/data/perkuliahan")
def data_perkuliahan():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_perkuliahan"))
        perkuliahan_data = result.mappings().all()
    return render_template("data_perkuliahan.html",perkuliahans=perkuliahan_data, active_page='data_perkuliahan')
@app.route("/data/generate")
def data_generate():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_generate"))
        generate_data = result.mappings().all()
    return render_template("data_generate.html",generates=generate_data, active_page='data_generate')
@app.route("/data/ruang")
def data_ruang():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_ruang"))
        ruang_data = result.mappings().all()
    return render_template("data_ruang.html",ruangs=ruang_data, active_page='data_ruang')
@app.route("/data/rombel")
def data_rombel():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_rombel"))
        rombel_data = result.mappings().all()
    return render_template("data_rombel.html",rombels=rombel_data, active_page='data_rombel')
@app.route("/jadwal")
def data_hasil():
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_hasil"))
        jadwal_data = result.mappings().all()
    return render_template("data_hasiljadwal.html",jadwals=jadwal_data, active_page='hasil_jadwal')


@app.route("/logout")
def logout():
    session.clear()

    flash("Anda telah logout.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
