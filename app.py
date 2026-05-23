from flask import Flask, request, render_template, redirect
import sqlite3
import requests
from datetime import datetime
from config import VERIFY_TOKEN, PAGE_ACCESS_TOKEN

app = Flask(__name__)


# =========================
# CRM DASHBOARD
# =========================
@app.route("/")
def dashboard():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users ORDER BY last_seen DESC")
    users = cur.fetchall()

    conn.close()

    return render_template("index.html", users=users)


# =========================
# FACEBOOK WEBHOOK (ROBUST)
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json(force=True)

    print("RAW:", data)

    for entry in data.get("entry", []):

        for event in entry.get("messaging", []):

            sender_id = event.get("sender", {}).get("id")

            if not sender_id:
                continue

            print("SENDER:", sender_id)

            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute("""
                INSERT OR IGNORE INTO users (psid, first_seen, last_seen, messages_count)
                VALUES (?, ?, ?, 1)
            """, (sender_id, datetime.now().isoformat(), datetime.now().isoformat()))

            cur.execute("""
                UPDATE users
                SET last_seen = ?, messages_count = messages_count + 1
                WHERE psid = ?
            """, (datetime.now().isoformat(), sender_id))

            conn.commit()
            conn.close()

            print("SAVED USER:", sender_id)

    return "ok", 200


# =========================
# SEND MESSAGE FUNCTION
# =========================
def send_message(psid, text):

    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": psid},
        "message": {"text": text}
    }

    r = requests.post(url, json=payload)

    print("FB RESPONSE:", r.status_code, r.text)


# =========================
# CRM BROADCAST BUTTON
# =========================
@app.route("/broadcast", methods=["POST"])
def broadcast():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT psid FROM users")
    users = cur.fetchall()

    print("TOTAL USERS:", len(users))

    for (psid,) in users:

        send_message(psid, "👋 Hey! Just checking in — let me know if you still need help.")

    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(port=5000, debug=True)