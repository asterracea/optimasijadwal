from flask import Flask, request, jsonify

rec = Flask(__name__)

@rec.route('/receive-json', methods=['POST'])
def receive_json():
    data = request.get_json()
    headers = request.headers

    print("Received JSON:", data),
    print("Received Headers:", headers)
    

    return jsonify({"status": "success", "received": data}), 200

if __name__ == '__main__':
    rec.run(host='0.0.0.0', port=5000) 
