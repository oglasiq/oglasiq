from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests as req

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SUPABASE_URL = "https://mzcygmkvqqmsoufptinm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16Y3lnbWt2cXFtc291ZnB0aW5tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2OTY2MDMsImV4cCI6MjA5MjI3MjYwM30.u0UWS-URLgUu9zifPR197S-tRCpGJAIf-9XYJlHCLbA"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

@app.route("/iskanja", methods=["GET"])
def get_iskanja():
    r = req.get(f"{SUPABASE_URL}/rest/v1/iskanja?select=*", headers=HEADERS)
    return jsonify(r.json())

@app.route("/iskanja", methods=["POST"])
def post_iskanje():
    data = request.json
    # Preveri ce ze obstaja
    r = req.get(f"{SUPABASE_URL}/rest/v1/iskanja?id=eq.{data.get('id')}", headers=HEADERS)
    obstaja = r.json()

    if obstaja:
        # Update
        r = req.patch(
            f"{SUPABASE_URL}/rest/v1/iskanja?id=eq.{data.get('id')}",
            headers=HEADERS,
            json=data
        )
    else:
        # Insert
        r = req.post(
            f"{SUPABASE_URL}/rest/v1/iskanja",
            headers=HEADERS,
            json=data
        )
    return jsonify({"status": "ok"})

@app.route("/iskanja/<int:iid>", methods=["DELETE"])
def delete_iskanje(iid):
    req.delete(f"{SUPABASE_URL}/rest/v1/iskanja?id=eq.{iid}", headers=HEADERS)
    return jsonify({"status": "ok"})

@app.route("/iskanja/<int:iid>/toggle", methods=["POST"])
def toggle_iskanje(iid):
    r = req.get(f"{SUPABASE_URL}/rest/v1/iskanja?id=eq.{iid}", headers=HEADERS)
    data = r.json()
    if data:
        aktiven = not data[0].get("aktiven", True)
        req.patch(
            f"{SUPABASE_URL}/rest/v1/iskanja?id=eq.{iid}",
            headers=HEADERS,
            json={"aktiven": aktiven}
        )
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "OglasIQ API"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 OglasIQ strežnik se zaganja na portu {port}...")
    app.run(debug=False, host="0.0.0.0", port=port)