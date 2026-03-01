from flask import Flask, jsonify, request
import requests
import os
import datetime

app = Flask(__name__)

PLAYFAB_TITLE_ID = os.getenv("PLAYFAB_TITLE_ID")
PLAYFAB_SECRET_KEY = os.getenv("9DOHAJC53EEQIW1EGTHH13YSG8Z68EYU6OW3JHU39HQ4D5JPRU")
DISCORD_WEBHOOK_URL = os.getenv("https://discordapp.com/api/webhooks/1477463119214411868/oTWWsyd9lEe258ATGQ47jgv4wC2Sx6BPSinSBIAk8bAwFAGPYT8NvTzIBp167ajGtS1j")
META_APP_ID = os.getenv("34299400353006765")
META_APP_SECRET = os.getenv("9aaad69574634a447f50d4d5ee91df69")

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

@app.route("/api/OculusLogin", methods=["POST"])
def oculus_login():
    data = request.json
    oculus_id = data.get("OculusId")
    nonce = data.get("Nonce")

    if not oculus_id or not nonce:
        send_webhook("Oculus Login Failed", "Missing ID or Nonce", False)
        return jsonify({"error": "Missing OculusId or Nonce"}), 400

    response = requests.post(
        "https://graph.oculus.com/user_nonce_validate",
        json={
            "access_token": f"OC|{META_APP_ID}|{META_APP_SECRET}",
            "nonce": nonce,
            "user_id": oculus_id
        }
    )

    if response.status_code != 200 or not response.json().get("is_valid"):
        send_webhook("Oculus Login Failed", f"User: {oculus_id}", False)
        return jsonify({"error": "Invalid Oculus login"}), 401

    send_webhook("Oculus Login Success", f"User: {oculus_id}", True)
    return jsonify({"message": "Oculus authenticated"}), 200

@app.route("/api/PlayFabLogin", methods=["POST"])
def playfab_login():
    data = request.json
    custom_id = data.get("CustomId")

    if not custom_id:
        send_webhook("PlayFab Login Failed", "Missing CustomId", False)
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
        send_webhook("PlayFab Login Failed", f"CustomId: {custom_id}", False)
        return jsonify({"error": "PlayFab login failed"}), 401

    pf = login_request.json()["data"]

    send_webhook("PlayFab Login Success", f"PlayFabId: {pf['PlayFabId']}", True)

    return jsonify({
        "SessionTicket": pf["SessionTicket"],
        "PlayFabId": pf["PlayFabId"],
        "EntityToken": pf["EntityToken"]["EntityToken"]
    })

fake_stats = {}

@app.route("/api/AddWin", methods=["POST"])
def add_win():
    data = request.json
    user = data.get("User")

    if not user:
        return jsonify({"error": "Missing user"}), 400

    fake_stats[user] = fake_stats.get(user, 0) + 1

    send_webhook("Win Added", f"{user} now has {fake_stats[user]} wins")

    return jsonify({"wins": fake_stats[user]})


@app.route("/api/Leaderboard", methods=["GET"])
def leaderboard():
    sorted_lb = sorted(fake_stats.items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_lb)

@app.route("/api/PhotonAuth", methods=["POST"])
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
        send_webhook("Photon Auth Failed", "Invalid SessionTicket", False)
        return jsonify({"ResultCode": 3, "Message": "Invalid SessionTicket"})

    send_webhook("Photon Auth Success", "Player connected to multiplayer")

    return jsonify({
        "ResultCode": 1,
        "Message": "Authenticated"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
