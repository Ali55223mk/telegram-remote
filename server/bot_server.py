"""
Telegram Remote Control - Server (Railway)
Runs 24/7, handles Telegram commands, forwards to PC agent
"""
import os
import json
import time
import threading
from datetime import datetime

from flask import Flask, request, jsonify
import requests

TOKEN = os.environ.get("BOT_TOKEN", "8999468767:AAGvs27z1D3FUwPMCjmPdYZiQfMAR6vkss8")
AUTHORIZED_USERS = {int(x) for x in os.environ.get("AUTHORIZED_USERS", "6337140367").split(",")}
PC_MAC = os.environ.get("PC_MAC", "").upper()
PC_BROADCAST_IP = os.environ.get("PC_BROADCAST_IP", "255.255.255.255")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# In-memory state
pc_status = {"online": False, "ip": None, "last_seen": None, "mac": PC_MAC}
pending_tasks = []
task_results = {}

def send_telegram(chat_id, text, parse_mode=None):
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json=data, timeout=10)
    except Exception as e:
        print(f"Telegram send error: {e}")

def send_photo(chat_id, photo_path, caption=""):
    try:
        with open(photo_path, "rb") as f:
            requests.post(f"{TELEGRAM_API}/sendPhoto", data={"chat_id": chat_id, "caption": caption}, files={"photo": f}, timeout=30)
    except Exception as e:
        print(f"Send photo error: {e}")

def send_wol(mac):
    mac_clean = mac.replace(":", "").replace("-", "")
    if len(mac_clean) != 12:
        return False
    magic = bytes.fromhex("FF" * 6 + mac_clean * 16)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic, (PC_BROADCAST_IP, 9))
        s.sendto(magic, ("255.255.255.255", 9))
        s.close()
        return True
    except:
        return False

@app.route("/")
def health():
    return jsonify({"status": "ok", "pc": pc_status})

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "ok", 200
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text", "")

    if user_id not in AUTHORIZED_USERS:
        send_telegram(chat_id, "⛔ غير مصرح لك.")
        return "ok", 200

    parts = text.split()
    cmd = parts[0].lower() if parts else ""

    if cmd == "/start":
        send_telegram(chat_id,
            "🎛 **Telegram Remote Control**\n\n"
            "**الأوامر:**\n"
            "/status - حالة الجهاز\n"
            "/shutdown - إطفاء الكمبيوتر\n"
            "/restart - إعادة تشغيل\n"
            "/lock - قفل الشاشة\n"
            "/password <رمز> - تغيير كلمة السر\n"
            "/cmd <أمر> - تشغيل أمر CMD\n"
            "/screenshot - تصوير الشاشة\n"
            "/wol - تشغيل الكمبيوتر عن بعد\n"
            "/setmac AA:BB:CC:DD:EE:FF - تعيين MAC address",
            parse_mode="Markdown"
        )

    elif cmd == "/status":
        if pc_status["online"]:
            last = pc_status["last_seen"] or "?"
            uptime_sec = 0
            pending_tasks.append({"cmd": "status", "chat_id": chat_id, "ts": time.time()})
        else:
            send_telegram(chat_id, f"💻 **الجهاز: OFFLINE**\n📡 MAC: `{pc_status['mac'] or 'غير معروف'}`\n📅 آخر ظهور: {pc_status['last_seen'] or 'أبداً'}", parse_mode="Markdown")

    elif cmd == "/shutdown":
        if pc_status["online"]:
            pending_tasks.append({"cmd": "shutdown", "chat_id": chat_id, "ts": time.time()})
            send_telegram(chat_id, "🔄 جاري إيقاف التشغيل...")
        else:
            send_telegram(chat_id, "❌ الجهاز طافي.")

    elif cmd == "/restart":
        if pc_status["online"]:
            pending_tasks.append({"cmd": "restart", "chat_id": chat_id, "ts": time.time()})
            send_telegram(chat_id, "🔄 جاري إعادة التشغيل...")
        else:
            send_telegram(chat_id, "❌ الجهاز طافي.")

    elif cmd == "/lock":
        if pc_status["online"]:
            pending_tasks.append({"cmd": "lock", "chat_id": chat_id, "ts": time.time()})
            send_telegram(chat_id, "🔒 جاري قفل الشاشة...")
        else:
            send_telegram(chat_id, "❌ الجهاز طافي.")

    elif cmd == "/password":
        if len(parts) < 2:
            send_telegram(chat_id, "⚠️ استخدم: /password <كلمة_السر>")
        elif pc_status["online"]:
            pending_tasks.append({"cmd": "password", "args": parts[1], "chat_id": chat_id, "ts": time.time()})
            send_telegram(chat_id, "🔑 جاري تغيير كلمة السر...")
        else:
            send_telegram(chat_id, "❌ الجهاز طافي.")

    elif cmd == "/cmd":
        if len(parts) < 2:
            send_telegram(chat_id, "⚠️ استخدم: /cmd <أمر>")
        elif pc_status["online"]:
            pending_tasks.append({"cmd": "cmd", "args": " ".join(parts[1:]), "chat_id": chat_id, "ts": time.time()})
            send_telegram(chat_id, "⌛ جاري تشغيل الأمر...")
        else:
            send_telegram(chat_id, "❌ الجهاز طافي.")

    elif cmd == "/screenshot":
        if pc_status["online"]:
            pending_tasks.append({"cmd": "screenshot", "chat_id": chat_id, "ts": time.time()})
            send_telegram(chat_id, "📸 جاري التصوير...")
        else:
            send_telegram(chat_id, "❌ الجهاز طافي.")

    elif cmd == "/wol":
        mac = parts[1] if len(parts) > 1 else pc_status.get("mac", "")
        if not mac:
            send_telegram(chat_id, "⚠️ ما في MAC مسجل. استخدم /setmac AA:BB:CC:DD:EE:FF")
            return "ok", 200
        pc_status["mac"] = mac
        ok = send_wol(mac)
        if ok:
            send_telegram(chat_id, f"📡 تم إرسال WOL إلى `{mac}`\nتأكد إن Wake-on-LAN مفعل في BIOS", parse_mode="Markdown")
        else:
            send_telegram(chat_id, "❌ فشل إرسال WOL")

    elif cmd == "/setmac":
        if len(parts) < 2:
            send_telegram(chat_id, "⚠️ استخدم: /setmac AA:BB:CC:DD:EE:FF")
        else:
            mac = parts[1].upper()
            pc_status["mac"] = mac
            send_telegram(chat_id, f"✅ تم حفظ MAC: `{mac}`", parse_mode="Markdown")

    return "ok", 200

@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    pc_status["online"] = True
    pc_status["ip"] = data.get("ip", request.remote_addr)
    pc_status["last_seen"] = datetime.now().isoformat()
    return jsonify({"tasks": pending_tasks})

@app.route("/api/result", methods=["POST"])
def task_result():
    data = request.get_json()
    task_cmd = data.get("cmd", "")
    chat_id = data.get("chat_id")
    output = data.get("output", "")
    error = data.get("error")
    photo_path = data.get("photo_path")

    if chat_id:
        if photo_path:
            send_photo(chat_id, photo_path, caption="📸 Screenshot")
        elif error:
            send_telegram(chat_id, f"❌ {error}")
        else:
            send_telegram(chat_id, output, parse_mode="Markdown")

    # Remove completed task
    global pending_tasks
    pending_tasks = [t for t in pending_tasks if t.get("chat_id") != chat_id or t.get("cmd") != task_cmd]
    return "ok", 200

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify(pending_tasks)

# Periodic cleanup of stale tasks
def cleanup_loop():
    while True:
        time.sleep(60)
        now = time.time()
        global pending_tasks
        pending_tasks = [t for t in pending_tasks if now - t.get("ts", 0) < 120]
        # Mark PC offline if no heartbeat in 90s
        if pc_status["online"] and pc_status["last_seen"]:
            try:
                last = datetime.fromisoformat(pc_status["last_seen"])
                if (datetime.now() - last).total_seconds() > 90:
                    pc_status["online"] = False
            except:
                pass

if __name__ == "__main__":
    threading.Thread(target=cleanup_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
