from flask import Flask, render_template, request,redirect,jsonify,url_for,flash,make_response,session,logging
from flask_jwt_extended import JWTManager, create_access_token, jwt_required,get_jwt, get_jwt_identity,  decode_token
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from routes.auth_api import create_auth_api
from config import db_url
from flask_bcrypt import Bcrypt
import pandas as pd
from sqlalchemy import create_engine, text
from algoritma.optimasiSA import PenjadwalanSA
import requests
from datetime import timedelta
from functools import wraps
from flask import abort


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
app.register_blueprint(create_auth_api(socketio))

app.secret_key = "kyutpipel"
app.config["JWT_SECRET_KEY"] = "semhaslancar"
app.config["JWT_TOKEN_LOCATION"] = ["cookies","headers"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False #sementara
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=6)

jwt = JWTManager(app)
bcrypt = Bcrypt(app)

@jwt.unauthorized_loader
def unauthorized_callback(callback):
    if request.path.startswith("/api/"):
        return jsonify({"status": "unauthorized", "message": "Token tidak ditemukan"}), 401
    else:
        flash("Silakan login terlebih dahulu.", "warning")
        return redirect(url_for('login'))

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    if request.path.startswith("/api/"):
        return jsonify({"status": "invalid token", "message": "Token tidak valid"}), 401
    else:
        flash("Token tidak valid. Silakan login ulang.", "danger")
        return redirect(url_for('login'))

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    if request.path.startswith("/api/"):
        return jsonify({"status": "expired token", "message": "Token telah kadaluwarsa"}), 401
    else:
        flash("Sesi Anda telah habis. Silakan login ulang.", "warning")
        return redirect(url_for('login'))


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.", "danger")
            return redirect(url_for("unauthorized"))  # Atau halaman lain yang sesuai
        return fn(*args, **kwargs)
    return wrapper
@app.route("/error")
def unauthorized():
    return render_template("page/error.html")
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
        username = request.form['username'].strip()
        password_input = request.form['password'].strip()
        # print(f"[DEBUG] username: {username}, Password: {password_input}")

        with db_url.connect() as connection:
            query = text("SELECT id_user, username, password, nama, role, status FROM tb_user WHERE username = :username")
            result = connection.execute(query, {"username": username}).fetchone()
            
            if result:
                id_user, username, password_hash, nama,role, status = result
                if status != 'aktif':
                    # print(f"[DEBUG] User found: {username}, status: {status}")
                    flash("Akun Anda tidak aktif. Silakan hubungi admin.", "warning")
                    return redirect(url_for('login'))
                if bcrypt.check_password_hash(password_hash, password_input):
                    # Buat JWT token
                    additional_claims = {
                        "username": username,
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
                flash("username tidak ditemukan.", "danger")
    return render_template('page/login.html')

@app.route("/dashboard")
@jwt_required()
@admin_required
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
        
        best_solution = sa.generate_jadwal()
        df_jadwal = sa.df_hasiljadwal(best_solution)
        jadwal_list = df_jadwal.to_dict(orient='records')
        sa.simpan_optimasi(df_jadwal)

        # flash('Jadwal berhasil digenerate!', 'success')
        return render_template('page/dashboard.html', data=jadwal_list, nama_user=nama_user,role_user=role_user)
    return redirect(url_for('dashboard'))
   
@app.route("/data/master", methods=['GET', 'POST'])
@jwt_required()
def data_master():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")

    selected_id = None
    if request.method == "POST":
        selected_id = request.form.get("id_generate")

    with db_url.connect() as connection:
        generate_ids = connection.execute(
            text("SELECT id_generate FROM tb_generate")
        ).mappings().all()

    dosen_data, matkul_data, perkuliahan_data, ruang_data, rombel_data, prodi_data, waktu_data = [], [], [], [], [], [], []
    if selected_id:
        with db_url.connect() as connection:
            query = text("""
                        SELECT 
                            p.id_perkuliahan,
                            p.id_generate,
                            mk.nama_matakuliah,
                            mk.sks,
                            d.nama_dosen,
                            k.nama_kelas,
                            s.nama_semester,
                            pr.nama_prodi
                        FROM tb_perkuliahan p
                        JOIN tb_matakuliah mk ON p.kode_matakuliah = mk.kode_matakuliah
                        JOIN tb_dosen d ON p.kode_dosen = d.kode_dosen
                        JOIN tb_rombel k ON p.id_kelasrombel = k.id_kelasrombel
                        JOIN tb_semester s ON p.id_semester = s.id_semester
                        JOIN tb_prodi pr ON p.kode_prodi = pr.kode_prodi
                        WHERE p.id_generate = :id
                    """)

            dosen = connection.execute(text("SELECT * FROM tb_dosen WHERE id_generate = :id"), {"id": selected_id})
            mk = connection.execute(text("SELECT * FROM tb_matakuliah WHERE id_generate = :id"), {"id": selected_id})
            pk = connection.execute(query, {"id": selected_id})
            ruang = connection.execute(text("SELECT * FROM tb_ruang WHERE id_generate = :id"), {"id": selected_id})
            rb = connection.execute(text("SELECT * FROM tb_rombel WHERE id_generate = :id"), {"id": selected_id})
            ps = connection.execute(text("SELECT * FROM tb_prodi WHERE id_generate = :id"), {"id": selected_id})
            time = connection.execute(text("SELECT * FROM tb_waktu WHERE id_generate = :id"), {"id": selected_id})

            dosen_data = dosen.mappings().all()
            matkul_data = mk.mappings().all()
            perkuliahan_data = pk.mappings().all()
            ruang_data = ruang.mappings().all()
            rombel_data = rb.mappings().all()
            prodi_data = ps.mappings().all()
            waktu_data = time.mappings().all()

    return render_template("page/tabdata.html",
                           active_page='data_master',
                           generate_ids=generate_ids,
                           selected_id=selected_id,
                           dosens=dosen_data,
                           matkuls=matkul_data,
                           perkuliahans=perkuliahan_data,
                           ruangs=ruang_data,
                           rombels=rombel_data,
                           prodis=prodi_data,
                           waktu=waktu_data,
                           nama_user=nama_user,
                           role_user=role_user)


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
        username = request.form.get("addusername")
        role = request.form.get("addrole")
        status = request.form.get("addstatus")
        password = request.form.get("addpassword")
        conpassword = request.form.get("addconpassword")

        # Validasi sederhana password
        if password != conpassword:
            flash("Password dan Konfirmasi Password tidak cocok.", "error")
            return redirect(url_for("data_user"))
        if not (nama and username and role and status and password):
            flash("Semua field wajib diisi.", "warning")
            return redirect(url_for("data_user"))
    
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        try:
            with db_url.connect() as connection:
                insert_query = text("""
                    INSERT INTO tb_user (nama, username, role, status, password)
                    VALUES (:nama, :username, :role, :status, :password)
                """)
                connection.execute(insert_query, {
                    "nama": nama,
                    "username": username,
                    "role": role,
                    "status": status,
                    "password": hashed_password
                })
                connection.commit()

            flash("User berhasil ditambahkan.", "success")
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
    role = request.form.get("edit_role")
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
                    text("""
                        SELECT h.*,
                        m.sks,
                        s.nama_semester,
                        p.nama_prodi 
                        FROM tb_hasil h 
                        JOIN tb_perkuliahan k ON h.id_perkuliahan = k.id_perkuliahan
                        JOIN tb_matakuliah m ON k.kode_matakuliah = m.kode_matakuliah
                        JOIN tb_prodi p ON k.kode_prodi = p.kode_prodi
                        JOIN tb_semester s ON k.id_semester = s.id_semester 
                        WHERE p.id_generate = :id_generate"""),
                    {"id_generate": selected_id}
                )
                jadwal_data = result.mappings().all()

        bentrok = connection.execute(
            text("""
                SELECT 
                    a.id_hasil AS id1, b.id_hasil AS id2,
                    a.hari, a.jam_mulai, a.jam_selesai, b.jam_mulai AS b_mulai, b.jam_selesai AS b_selesai,
                    a.nama_dosen, a.ruang
                FROM tb_hasil a
                JOIN tb_hasil b ON a.id_hasil != b.id_hasil
                JOIN tb_perkuliahan pa ON a.id_perkuliahan = pa.id_perkuliahan
                JOIN tb_perkuliahan pb ON b.id_perkuliahan = pb.id_perkuliahan
                WHERE pa.id_generate = :id_generate AND pb.id_generate = :id_generate
                AND a.hari = b.hari
                AND (a.nama_dosen = b.nama_dosen OR a.ruang = b.ruang)
                AND a.jam_mulai < b.jam_selesai
                AND a.jam_selesai > b.jam_mulai
            """), {"id_generate": selected_id}
        ).mappings().all()
    return render_template("page/data_hasiljadwal.html",jadwals=jadwal_data, opsi_ids=opsi_id, selected_id=selected_id, active_page='hasiljadwal', nama_user=nama_user,role_user=role_user,bentrok=bentrok)

@app.route("/delete-schedule", methods=["POST"])
@jwt_required()
def delete_schedule():
    current_user = get_jwt_identity()

    id_generate = request.form.get('id_generate')
    
    if not id_generate:
        flash("ID Generate tidak ditemukan!", "warning")
        return redirect(url_for('data_hasil'))

    try:
        with db_url.connect() as connection:
            
            # Hapus data tb_hasil sesuai id_generate
            connection.execute(text("""
                DELETE FROM tb_hasil
                WHERE id_perkuliahan IN (
                    SELECT id_perkuliahan FROM tb_perkuliahan WHERE id_generate = :id_generate
                )
            """), {"id_generate": id_generate})

            # Update status di tb_generate jadi 'belum'
            connection.execute(text("""
                UPDATE tb_generate SET status = 'belum' WHERE id_generate = :id_generate
            """), {"id_generate": id_generate})

            # Commit transaksi
            connection.commit()
            
            flash(f"Jadwal dengan ID {id_generate} berhasil dihapus!", "success")

    except Exception as e:
        # Pastikan rollback hanya dipanggil kalau connection masih terbuka
        try:
            connection.rollback()
        except:
            pass
        flash(f"Gagal menghapus jadwal: {str(e)}", "danger")

    return redirect(url_for('data_hasil'))

@app.route("/settings", methods=["GET","POST"])
@jwt_required()
def setting():
    current_user = get_jwt_identity()
    claims = get_jwt()
    nama_user = claims.get("nama")
    role_user = claims.get("role")

    with db_url.connect() as connection:
        query = text("SELECT nama, username FROM tb_user WHERE id_user = :id_user")
        result = connection.execute(query, {"id_user": current_user}).fetchone()

    if not result:
        flash("User tidak ditemukan.", "danger")
        return redirect(url_for("dashboard"))

    nama, username = result

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

    user_info = {"nama": nama, "username": username}
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
    response.delete_cookie("access_token")
    session.clear()
    flash("Anda telah logout.", "info")
    return response

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
