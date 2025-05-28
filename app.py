from flask import Flask, render_template, request,redirect,jsonify,url_for,flash,make_response,session,logging
from flask_jwt_extended import JWTManager, create_access_token, jwt_required,get_jwt, get_jwt_identity,  decode_token
from routes.auth_api import api
from config import db_url
from flask_bcrypt import Bcrypt
import pandas as pd
from sqlalchemy import create_engine, text
from algoritma.optimasiSA import PenjadwalanSA


app = Flask(__name__)
app.register_blueprint(api)

app.secret_key = "kyutpipel"
app.config["JWT_SECRET_KEY"] = "semhaslancar"
app.config["JWT_TOKEN_LOCATION"] = ["cookies","headers"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False #sementara
app.config["JWT_HEADER_TYPE"] = "Bearer"
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
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
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"msg": "Missing or invalid JWT"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    print("Invalid token error:", callback)
    return jsonify(msg='Invalid token'), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"msg": "Token has expired"}), 401


@app.route("/",methods=["GET", "POST"])

@app.route("/login", methods=["GET","POST"])
def login():
    token = request.cookies.get("access_token")
    if token:
        try:
            decoded = decode_token(token)
            if decoded.get("sub"):  # sub adalah id_user yang diset di identity
                return redirect(url_for("dashboard"))
        except Exception:
            pass  # Token tidak valid, lanjut ke halaman login
            
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
                        "role": role,
                        "nama": nama,
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
    return render_template('page/login.html')

@app.route("/dashboard")
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT id_generate FROM tb_generate where status='belum'"))
        id_generates = result.mappings().all()
    return render_template("page/dashboard.html", generates=id_generates, active_page='dashboard', user=current_user, nama_user=nama_user,role_user=role_user)

@app.route('/generate-jadwal', methods=['GET','POST'])
@jwt_required()
def generate_jadwal():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role") 
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
        return render_template('page/dashboard.html', data=jadwal_list, nama_user=nama_user,role_user=role_user)
    return redirect(url_for('dashboard'))

   
@app.route('/callback', methods=['POST'])
def optimasi_callback():
    data = request.get_json()
    return jsonify({"status": "received", "data": data})
    

@app.route("/data/dosen")
@jwt_required()
def data_dosen():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_dosen"))
        dosen_data = result.mappings().all()
    return render_template("page/data_dosen.html", dosens=dosen_data, active_page='data_dosen', nama_user=nama_user,role_user=role_user)

    
@app.route("/data/matakuliah")
@jwt_required()
def data_matakuliah():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_matakuliah"))
        matkul_data = result.mappings().all()
    return render_template("page/data_matakuliah.html", matkuls=matkul_data, active_page='data_matakuliah', nama_user=nama_user,role_user=role_user)
@app.route("/data/perkuliahan")
@jwt_required()
def data_perkuliahan():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_perkuliahan"))
        perkuliahan_data = result.mappings().all()
    return render_template("page/data_perkuliahan.html",perkuliahans=perkuliahan_data, active_page='data_perkuliahan', nama_user=nama_user,role_user=role_user)
@app.route("/data/generate")
@jwt_required()
def data_generate():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_generate"))
        generate_data = result.mappings().all()
    return render_template("page/data_generate.html",generates=generate_data, active_page='data_generate', nama_user=nama_user,role_user=role_user)

@app.route("/data/generate/delete/<string:id_generate>", methods=["POST"])
@jwt_required()
def delete_generate(id_generate):
    try:
        with db_url.connect() as connection:
            trans = connection.begin()
            try:
                delete_query = text("DELETE FROM tb_generate WHERE id_generate = :id")
                connection.execute(delete_query, {"id": id_generate})
                trans.commit()
                flash("Data generate berhasil dihapus.", "success")
            except Exception as e:
                trans.rollback()
                flash(f"Gagal menghapus data generate: {e}", "error")
    except Exception as e:
        flash(f"Terjadi kesalahan koneksi: {e}", "error")
    return redirect(url_for("data_generate"))
@app.route("/data/ruang")
@jwt_required()
def data_ruang():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_ruang"))
        ruang_data = result.mappings().all()
    return render_template("page/data_ruang.html",ruangs=ruang_data, active_page='data_ruang', nama_user=nama_user,role_user=role_user)
@app.route("/data/rombel")
@jwt_required()
def data_rombel():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        result = connection.execute(text("SELECT * FROM tb_rombel"))
        rombel_data = result.mappings().all()
    return render_template("page/data_rombel.html",rombels=rombel_data, active_page='data_rombel', nama_user=nama_user,role_user=role_user)

@app.route("/user/datauser", methods=["GET", "POST"])
@jwt_required()
def data_user():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    if request.method == "POST":
        # Ambil data dari form
        nama = request.form.get("addnama")
        email = request.form.get("addemail")
        role = request.form.get("addrole")
        status = request.form.get("addstatus")
        password = request.form.get("addpassword")
        conpassword = request.form.get("addconpassword")

        # Validasi sederhana password
        if password != conpassword:
            flash("Password dan Konfirmasi Password tidak cocok.", "error")
            return redirect(url_for("data_user"))
        if not (nama and email and role and status and password):
            flash("Semua field wajib diisi.", "warning")
            return redirect(url_for("data_user"))
    
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        try:
            with db_url.connect() as connection:
                insert_query = text("""
                    INSERT INTO tb_user (nama, email, role, status, password)
                    VALUES (:nama, :email, :role, :status, :password)
                """)
                connection.execute(insert_query, {
                    "nama": nama,
                    "email": email,
                    "role": role,
                    "status": status,
                    "password": hashed_password
                })
                connection.commit()

            flash("User admin berhasil ditambahkan.", "success")
            return redirect(url_for("data_user"))
        except Exception as e:
            flash(f"Gagal menambah user: {e}", "danger")
            return redirect(url_for("data_user"))

    with db_url.connect() as connection:
        query = text("SELECT * FROM tb_user")
        result = connection.execute(query)
        admin_data = result.mappings().all()
        column_names = result.keys()
    return render_template("page/user.html", users=admin_data, columns=column_names,active_page='data_user', nama_user=nama_user,role_user=role_user)

@app.route("/user/datauser/edit/<int:user_id>", methods=["POST"])
@jwt_required()
def edit_user(user_id):
    # Ambil data dari form
    nama = request.form.get("nama")
    role = request.form.get("role")
    status = request.form.get("status")

    # Validasi
    if not (nama and role and status):
        flash("Semua field wajib diisi.", "warning")
        return redirect(url_for("data_user"))

    try:
        # Eksekusi query update
        with db_url.connect() as connection:
            with connection.begin():
                update_query = text("""
                    UPDATE tb_user
                    SET nama = :nama, role = :role, status = :status
                    WHERE id_user = :id
                """)
                connection.execute(update_query, {
                    "nama": nama,
                    "role": role,
                    "status": status,
                    "id": user_id
                })

        flash("User berhasil diperbarui.", "success")
    except Exception as e:
        flash(f"Gagal memperbarui user: {e}", "error")

    return redirect(url_for("data_user"))

@app.route("/user/datauser/delete/<int:user_id>", methods=["POST"])
@jwt_required()
def delete_user(user_id):
    try:
        with db_url.connect() as connection:
            trans = connection.begin()  # Mulai transaksi
            try:
                delete_query = text("DELETE FROM tb_user WHERE id_user = :id")
                connection.execute(delete_query, {"id": user_id})
                trans.commit()  # Simpan perubahan
                flash("User berhasil dihapus.", "success")
            except Exception as e:
                trans.rollback()  # Batalkan perubahan jika gagal
                flash(f"Gagal menghapus user: {e}", "error")
    except Exception as e:
        flash(f"Terjadi kesalahan koneksi: {e}", "error")
    
    return redirect(url_for("data_user"))

@app.route("/jadwal", methods=["POST", "GET"])
@jwt_required()
def data_hasil():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    with db_url.connect() as connection:
        # Ambil semua id_generate dari tabel generate
        opsi_id = connection.execute(
            text("SELECT DISTINCT p.id_generate FROM tb_hasil h JOIN tb_perkuliahan p ON h.id_perkuliahan = p.id_perkuliahan JOIN tb_generate g ON p.id_generate = g.id_generate WHERE g.status = 'sudah'")
        ).mappings().all()

        jadwal_data = []
        selected_id = None

        if request.method == "POST":
            selected_id = request.form.get("id_generate")
            if selected_id:
                result = connection.execute(
                    text("SELECT h.* FROM tb_hasil h JOIN tb_perkuliahan p ON h.id_perkuliahan = p.id_perkuliahan WHERE p.id_generate = :id_generate"),
                    {"id_generate": selected_id}
                )
                jadwal_data = result.mappings().all()
    return render_template("page/data_hasiljadwal.html",jadwals=jadwal_data, opsi_ids=opsi_id, selected_id=selected_id, active_page='hasiljadwal', nama_user=nama_user,role_user=role_user)

@app.route("/settings", methods=["GET","POST"])
@jwt_required()
def setting():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")

    with db_url.connect() as connection:
        query = text("SELECT nama, email FROM tb_user WHERE id_user = :id_user")
        result = connection.execute(query, {"id_user": current_user}).fetchone()

    if not result:
        flash("User tidak ditemukan.", "danger")
        return redirect(url_for("dashboard"))

    nama, email = result

    if request.method == "POST":
        if "editNama" in request.form:
            new_nama = request.form.get("editNama").strip()
            if not new_nama:
                flash("Nama tidak boleh kosong.", "warning")
                return redirect(url_for("setting"))
            
            try:
                with db_url.begin() as connection:
                    update_query = text("UPDATE tb_user SET nama = :nama WHERE id_user = :id_user")
                    connection.execute(update_query, {"nama": new_nama, "id_user": current_user})
                
                flash("Nama berhasil diperbarui.", "success")
            except Exception as e:
                flash(f"Gagal update nama: {e}", "danger")

            return redirect(url_for("setting"))

    user_info = {"nama": nama, "email": email}
    return render_template("page/setting.html", user=user_info, active_page='pengaturan', nama_user=nama_user,role_user=role_user)

@app.route("/ubah-password", methods=["POST"])
@jwt_required()
def ubah_password():
    current_user = get_jwt_identity()

    password_lama = request.form.get("passwordlama")
    password_baru = request.form.get("passwordbaru")
    konfirmasi_password = request.form.get("passwordbaruconfirm")

    if not password_lama or not password_baru or not konfirmasi_password:
        flash("Semua field harus diisi.", "warning")
        return redirect(url_for("setting"))

    if password_baru != konfirmasi_password:
        flash("Password baru dan konfirmasi tidak cocok.", "danger")
        return redirect(url_for("setting"))

    with db_url.connect() as connection:
        query = text("SELECT password FROM tb_user WHERE id_user = :id_user")
        result = connection.execute(query, {"id_user": current_user}).fetchone()

        if result and bcrypt.check_password_hash(result[0], password_lama):
            password_hash_baru = bcrypt.generate_password_hash(password_baru).decode("utf-8")
            update_query = text("UPDATE tb_user SET password = :new_password WHERE id_user = :id_user")
            connection.execute(update_query, {"new_password": password_hash_baru, "id_user": current_user})
            connection.commit()
            flash("Password berhasil diubah.", "success")
        else:
            flash("Password lama salah.", "danger")

    return redirect(url_for("setting"))

@app.route("/daftar-endpoint")
@jwt_required()
def daftar_endpoint():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")
    return render_template("page/daftar_endpoint.html", active_page='daftar_endpoint', nama_user=nama_user,role_user=role_user)


@app.route("/logout")
def logout():
    response = redirect(url_for("login"))
    response.delete_cookie("access_token")  # hapus token JWT dari cookie
    session.clear()
    flash("Anda telah logout.", "info")
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
