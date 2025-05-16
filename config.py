from sqlalchemy import create_engine
DB_AUTH = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "db_optimasi1"
}
db_url = create_engine(f"mysql+pymysql://{DB_AUTH['user']}:{DB_AUTH['password']}@{DB_AUTH['host']}/{DB_AUTH['database']}"
)