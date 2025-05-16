from config import db_url
from flask_bcrypt import Bcrypt
from sqlalchemy import text

bcrypt = Bcrypt()

def tambah_user():
    email = "alip@gmail.com"
    nama = "Administrator"
    password = "admin123"
    role = "admin"
    status = "aktif"

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    with db_url.begin() as conn:
        query = text("""
            INSERT INTO tb_user (email, password, nama, role, status)
            VALUES ( :email, :password, :nama, :role, :status)
        """)
        conn.execute(query, {
            "email": email,
            "password": hashed_password,
            "nama": nama,
            "role": role,
            "status": status
        })
        print("✅ User berhasil ditambahkan.")

if __name__ == "__main__":
    tambah_user()
