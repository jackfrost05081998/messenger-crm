from flask import Flask, request, render_template, redirect
import sqlite3
import requests
from datetime import datetime

from config import PAGE_ACCESS_TOKEN, VERIFY_TOKEN
from db import init_db

# AUTO CREATE DATABASE
init_db()

app = Flask(__name__)


# =====================================
# DASHBOARD
# =====================================
@app.route("/")
def dashboard():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users ORDER BY last_seen DESC")

    users = cur.fetchall()

    conn.close()

    return render_template("index.html", users=users)


# =====================================
# FACEBOOK WEBHOOK
# =====================================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # VERIFY WEBHOOK
    if request.method == "GET":

        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge

        return "Invalid token"


    # RECEIVE FACEBOOK EVENTS
    if request.method == "POST":

        data = request.get_json(force=True)

        print("RAW DATA:", data)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        for entry in data.get("entry", []):

            for event in entry.get("messaging", []):

                sender_id = event.get("sender", {}).get("id")

                if not sender_id:
                    continue

                now = datetime.now().isoformat()

                # INSERT USER IF NEW
                cur.execute("""
                INSERT OR IGNORE INTO users
                (psid, first_seen, last_seen, messages_count)
                VALUES (?, ?, ?, 1)
                """, (sender_id, now, now))

                # UPDATE USER
                cur.execute("""
                UPDATE users
                SET last_seen = ?,
                    messages_count = messages_count + 1
                WHERE psid = ?
                """, (now, sender_id))

                conn.commit()

                print("SAVED USER:", sender_id)

        conn.close()

        return "ok", 200


# =====================================
# SEND MESSAGE FUNCTION
# =====================================
def send_message(psid, text):

    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": psid},
        "message": {"text": text}
    }

    r = requests.post(url, json=payload)

    print(r.status_code, r.text)


# =====================================
# BROADCAST TO ALL USERS
# =====================================
@app.route("/broadcast", methods=["POST"])
def broadcast():

    message = request.form.get("message")

    if not message:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT psid FROM users")

    users = cur.fetchall()

    print("TOTAL USERS:", len(users))

    for (psid,) in users:

        send_message(psid, message)

    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run()
