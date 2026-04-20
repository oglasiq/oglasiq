from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

ISKANJA_FILE = "iskanja.json"

def nalozi_iskanja():
    if os.path.exists(ISKANJA_FILE):
        with open(ISKANJA_FILE, "r") as f:
            return json.load(f)
    return []

def shrani_iskanja(iskanja):
    with open(ISKANJA_FILE, "w") as f:
        json.dump(iskanja, f, ensure_ascii=False, indent=2)

# Vrni vsa iskanja
@app.route("/iskanja", methods=["GET"])
def get_iskanja():
    return jsonify(nalozi_iskanja())

# Shrani iskanje
@app.route("/iskanja", methods=["POST"])
def post_iskanje():
    data = request.json
    iskanja = nalozi_iskanja()

    obstaja = False
    for i, isk in enumerate(iskanja):
        if isk.get("id") == data.get("id"):
            iskanja[i] = data
            obstaja = True
            break

    if not obstaja:
        data["id"] = len(iskanja) + 1
        iskanja.append(data)

    shrani_iskanja(iskanja)
    return jsonify({"status": "ok", "iskanje": data})

# Izbrisi iskanje
@app.route("/iskanja/<int:iid>", methods=["DELETE"])
def delete_iskanje(iid):
    iskanja = nalozi_iskanja()
    iskanja = [i for i in iskanja if i.get("id") != iid]
    shrani_iskanja(iskanja)
    return jsonify({"status": "ok"})

# Ustavi ali aktiviraj iskanje
@app.route("/iskanja/<int:iid>/toggle", methods=["POST"])
def toggle_iskanje(iid):
    iskanja = nalozi_iskanja()
    for isk in iskanja:
        if isk.get("id") == iid:
            isk["aktiven"] = not isk.get("aktiven", True)
            break
    shrani_iskanja(iskanja)
    return jsonify({"status": "ok"})

# Health check za Railway
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "OglasIQ API"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 OglasIQ strežnik se zaganja na portu {port}...")
    app.run(debug=False, host="0.0.0.0", port=port)