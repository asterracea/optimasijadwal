from flask import Flask, render_template, request,redirect,jsonify,url_for,flash,make_response,session,logging
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import db_url  # Import Blueprint
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pandas as pd
from insertDB import simpanData
from sqlalchemy import create_engine, text
from algoritma.optimasiSA import PenjadwalanSA


app = Flask(__name__)
app.secret_key = "kyutpipel"
app.config["JWT_SECRET_KEY"] = "semhaslancar"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False #sementara
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

@jwt.unauthorized_loader
def unauthorized_callback(callback):
    flash("Silakan login terlebih dahulu.", "warning")
    return redirect(url_for('login'))

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    flash("Token tidak valid. Silakan login ulang.", "danger")
    return redirect(url_for('login'))

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    flash("Sesi Anda telah habis. Silakan login ulang.", "warning")
    return redirect(url_for('login'))


@app.route("/",methods=["GET", "POST"])

@app.route("/login", methods=["GET","POST"])
def login():
    # if 'id_user' in session:
    #     return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email'].strip()
        password_input = request.form['password'].strip()
        # print(f"[DEBUG] Email: {email}, Password: {password_input}")

        with db_url.connect() as connection:
            query = text("SELECT id_user, email, password, nama, role, status FROM tb_user WHERE email = :email")
            result = connection.execute(query, {"email": email}).fetchone()
            
            if result:
                id_user, email, password_hash, nama,role, status = result
                if status != 'aktif':
                    # print(f"[DEBUG] User found: {email}, status: {status}")
                    flash("Akun Anda tidak aktif. Silakan hubungi admin.", "warning")
                    return redirect(url_for('login'))
                if bcrypt.check_password_hash(password_hash, password_input):
                    # Buat JWT token
                    additional_claims = {
                        "email": email,
                        "role": role
                    }
                    access_token = create_access_token(
                        identity=str(id_user),  # JWT identity HARUS string
                        additional_claims=additional_claims
                    )

                    response = make_response(redirect(url_for("dashboard")))
                    response.set_cookie("access_token", access_token, httponly=True)

                    flash("Login berhasil!", "success")
                    return response
                else:
                    flash("Password salah.", "danger")
            else:
                flash("Email tidak ditemukan.", "danger")
    return render_template('login.html')

@app.route("/dashboard")
@jwt_required()
def dashboard():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    current_user = get_jwt_identity()
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT id_generate FROM tb_generate where status='belum'"))
        id_generates = result.mappings().all()
    return render_template("dashboard.html", generates=id_generates, active_page='dashboard',user=current_user)

@app.route('/generate-jadwal', methods=['GET','POST'])
@jwt_required()
def generate_jadwal():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
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
    return redirect(url_for('dashboard'))

@app.route('/receive-json', methods=['POST'])
@jwt_required()
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
@jwt_required()
def data_dosen():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_dosen"))
        dosen_data = result.mappings().all()
    return render_template("data_dosen.html", dosens=dosen_data, active_page='data_dosen')

    
@app.route("/data/matakuliah")
@jwt_required()
def data_matakuliah():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_matakuliah"))
        matkul_data = result.mappings().all()
    return render_template("data_matakuliah.html", matkuls=matkul_data, active_page='data_matakuliah')
@app.route("/data/perkuliahan")
@jwt_required()
def data_perkuliahan():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_perkuliahan"))
        perkuliahan_data = result.mappings().all()
    return render_template("data_perkuliahan.html",perkuliahans=perkuliahan_data, active_page='data_perkuliahan')
@app.route("/data/generate")
@jwt_required()
def data_generate():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_generate"))
        generate_data = result.mappings().all()
    return render_template("data_generate.html",generates=generate_data, active_page='data_generate')
@app.route("/data/ruang")
@jwt_required()
def data_ruang():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_ruang"))
        ruang_data = result.mappings().all()
    return render_template("data_ruang.html",ruangs=ruang_data, active_page='data_ruang')
@app.route("/data/rombel")
@jwt_required()
def data_rombel():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_rombel"))
        rombel_data = result.mappings().all()
    return render_template("data_rombel.html",rombels=rombel_data, active_page='data_rombel')
@app.route("/jadwal")
@jwt_required()
def data_hasil():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_hasil"))
        jadwal_data = result.mappings().all()
    return render_template("data_hasiljadwal.html",jadwals=jadwal_data, active_page='hasil_jadwal')


@app.route("/logout")
def logout():
    # if 'id_user' not in session:
    #     flash("Silakan login terlebih dahulu.", "warning")
    #     return redirect(url_for("login"))
    # session.clear()

    # flash("Anda telah logout.", "info")
    # return redirect(url_for("login"))
    response = redirect(url_for("login"))
    response.delete_cookie("access_token")  # hapus token JWT dari cookie
    session.clear()
    flash("Anda telah logout.", "info")
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
