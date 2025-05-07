from flask import Blueprint, request, jsonify
from model.conn import get_db_jadwal

apiconn = Blueprint("data_api", __name__)

# api dosen
@apiconn.route('/get/dosen', methods=['GET'])
def get_dosen():
    try:
        db = get_db_jadwal()
        cur = db.cursor()

        cur.execute("SELECT * FROM tb_datadosen")
        data = cur.fetchall()
        cur.close()

        datadosen = []
        for row in data:
            datadosen.append({
                'nama_dosen': row[2],
            })

        return jsonify({'success': True, 'data dosen': datadosen}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    

# Endpoint untuk mendapatkan data ruang
@apiconn.route('/get/ruang', methods=['GET'])
def get_ruang():
    try:
        db = get_db_jadwal()
        cur = db.cursor()

        cur.execute("SELECT * FROM tb_ruangan")
        data = cur.fetchall()
        cur.close()

        dataruang = []
        for row in data:
            dataruang.append({
                # 'kode_ruangan': row[0],
                'nama_ruangan': row[1],
                'status_ruangan' : row[2]
            })

        return jsonify({'success': True, 'data ruang': dataruang}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@apiconn.route('/get/matkul', methods=['GET'])
def get_matkul():
    try:
        db = get_db_jadwal()
        cur = db.cursor()

        cur.execute("SELECT tb_matakuliah.nama_matakuliah, tb_matakuliah.sks, tb_matakuliah.status, tb_matakuliah.kelas, tb_datadosen.nama_dosen FROM tb_matakuliah JOIN tb_datadosen ON tb_matakuliah.kode_dosen = tb_datadosen.kode_dosen")
        data = cur.fetchall()
        cur.close()

        datamatkul = []
        for row in data:
            datamatkul.append({
                'mata kuliah': row[0],
                'nama dosen': row[4],
                'sks' : row[1],
                'status' :row[2],
                'kelas' :row[3],

            })

        return jsonify({'success': True, 'data matkul': datamatkul}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@apiconn.route('/get/hari', methods=['GET'])
def get_hari():
    try:
        db = get_db_jadwal()
        cur = db.cursor()
        cur.execute("SELECT * FROM tb_hari")
        data = cur.fetchall()
        cur.close()

        hari = []
        for row in data:
            hari.append({
                'hari' : row[1]
            })

        return jsonify({'success': True, 'data hari': hari}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
