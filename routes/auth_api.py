from flask import Blueprint, jsonify, request,flash,render_template,make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required,get_jwt, get_jwt_identity,  decode_token
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from config import db_url
from sqlalchemy import create_engine, text
from insertDB import simpanData
import requests


bcrypt = Bcrypt()
def create_auth_api(socketio):  # socketio sebagai parameter
    api = Blueprint('auth_api', __name__)
    
    @api.route('/api/auth-login',methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify(msg="Email dan password harus diisi"), 400
        try:
            with db_url.connect() as conn:
                query = text("SELECT * FROM tb_user WHERE email = :email")
                result = conn.execute(query, {"email": email})
                user = result.mappings().fetchone()

            if user and bcrypt.check_password_hash(user["password"], password):
                token = create_access_token(identity=str(user["id_user"]))
                return jsonify({
                    "access_token": token,
                    "status": "success",
                    "message": "Login berhasil",
                    }), 200
            else:
                return jsonify(msg="Email atau password salah"), 401
        except Exception as e:
            return jsonify(msg=f"Terjadi kesalahan server: {str(e)}"), 500


    @api.route('/api/receive-data',methods=['POST'])
    @jwt_required()
    def receive_data():
        try:
            auth_header = request.headers.get('Authorization')
            print("Authorization Header:", auth_header)
            
            identity = get_jwt_identity()
            id_user = int(identity)
            print("User ID dari JWT:", id_user)

            data = request.get_json()
            simpanData(data, id_user)
            socketio.emit('notifikasi_baru', {'pesan': f'Data baru berhasil diterima dari user {id_user}'})
            return jsonify({"status": "success",
                            "user_id": id_user,
                            "message": "Data berhasil disimpan"}), 200
        except Exception as e:
            print("Error parsing JSON:", e)
            return jsonify({"status": "failed", "error": str(e)}), 400
    return api


 