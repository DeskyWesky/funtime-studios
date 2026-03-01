from flask import Flask, jsonify, request
import requests
import os
import datetime

app = Flask(__name__)

PLAYFAB_TITLE_ID = os.getenv("6A25D")
PLAYFAB_SECRET_KEY = os.getenv("9DOHAJC53EEQIW1EGTHH13YSG8Z68EYU6OW3JHU39HQ4D5JPRU")
DISCORD_WEBHOOK_URL = os.getenv("https://discordapp.com/api/webhooks/1477463119214411868/oTWWsyd9lEe258ATGQ47jgv4wC2Sx6BPSinSBIAk8bAwFAGPYT8NvTzIBp167ajGtS1j")
META_APP_ID = os.getenv("34299400353006765")
META_APP_SECRET = os.getenv("9aaad69574634a447f50d4d5ee91df69")

fake_stats = {}

def send_webhook(title, description, success=True):
    if not DISCORD_WEBHOOK_URL:
        return

    color = 0x00FF00 if success else 0xFF0000

    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "footer": {
                    "text": f"Backend Log • {datetime.datetime.utcnow()}"
                }
            }
        ]
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except:
        pass


@app.route("/")
def home():
    return "Backend running"


@app.route("/PlayFabLogin", methods=["POST"])
def playfab_login():
    data = request.json
    custom_id = data.get("CustomId")

    if not custom_id:
        return jsonify({"error": "Missing CustomId"}), 400

    login_request = requests.post(
        f"https://{PLAYFAB_TITLE_ID}.playfabapi.com/Server/LoginWithServerCustomId",
        json={
            "ServerCustomId": custom_id,
            "CreateAccount": True
        },
        headers={
            "Content-Type": "application/json",
            "X-SecretKey": PLAYFAB_SECRET_KEY
        }
    )

    if login_request.status_code != 200:
        return jsonify({"error": "PlayFab login failed"}), 401

    pf = login_request.json()["data"]

    return jsonify({
        "SessionTicket": pf["SessionTicket"],
        "PlayFabId": pf["PlayFabId"],
        "EntityToken": pf["EntityToken"]["EntityToken"]
    })


@app.route("/AddWin", methods=["POST"])
def add_win():
    data = request.json
    user = data.get("User")

    if not user:
        return jsonify({"error": "Missing user"}), 400

    fake_stats[user] = fake_stats.get(user, 0) + 1
    return jsonify({"wins": fake_stats[user]})


@app.route("/Leaderboard", methods=["GET"])
def leaderboard():
    sorted_lb = sorted(fake_stats.items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_lb)


@app.route("/PhotonAuth", methods=["POST"])
def photon_auth():
    data = request.json
    session_ticket = data.get("SessionTicket")

    if not session_ticket:
        return jsonify({"ResultCode": 3, "Message": "Missing SessionTicket"})

    validate = requests.post(
        f"https://{PLAYFAB_TITLE_ID}.playfabapi.com/Client/AuthenticateSessionTicket",
        json={"SessionTicket": session_ticket}
    )

    if validate.status_code != 200:
        return jsonify({"ResultCode": 3, "Message": "Invalid SessionTicket"})

    return jsonify({
        "ResultCode": 1,
        "Message": "Authenticated"
    })
