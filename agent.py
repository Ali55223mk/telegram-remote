"""
Agent script - runs on Windows PC
Sends heartbeat to server bot, executes commands
"""
import os
import sys
import time
import json
import subprocess
import socket
import platform
import tempfile
import threading
from datetime import datetime

try:
    import requests
except ImportError:
    os.system("pip install requests")
    import requests

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    import psutil
except ImportError:
    psutil = None

# ===== CONFIG =====
SERVER_URL = "https://bot-production-8cf4.up.railway.app"
POLL_INTERVAL = 3  # seconds
HEARTBEAT_INTERVAL = 30  # seconds
# =================

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "unknown"

def run_cmd(command, timeout=30):
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=timeout)
        out = result.stdout or result.stderr or "(no output)"
        if len(out) > 3000:
            out = out[:3000] + "\n\n...(truncated)"
        return out, None
    except subprocess.TimeoutExpired:
        return None, "⏰ Timeout (30s)"
    except Exception as e:
        return None, str(e)

def take_screenshot():
    if ImageGrab is None:
        return None, "Pillow not installed"
    try:
        img = ImageGrab.grab()
        path = os.path.join(tempfile.gettempdir(), "screenshot.png")
        img.save(path)
        return path, None
    except Exception as e:
        return None, str(e)

def get_status():
    boot = datetime.fromtimestamp(psutil.boot_time()) if psutil else None
    uptime = str(datetime.now() - boot).split(".")[0] if boot else "?"
    cpu = psutil.cpu_percent(interval=0.5) if psutil else "?"
    mem = psutil.virtual_memory() if psutil else None
    disk = psutil.disk_usage("/") if psutil else None
    hostname = platform.node()
    username = os.getenv("USERNAME")

    msg = f"💻 **{hostname}**\n👤 {username}\n🕒 Uptime: {uptime}\n⚙️ CPU: {cpu}%"
    if mem:
        msg += f"\n🧠 RAM: {mem.used//(1024**3)}GB/{mem.total//(1024**3)}GB ({mem.percent}%)"
    if disk:
        msg += f"\n💾 C: {disk.used//(1024**3)}GB/{disk.total//(1024**3)}GB ({disk.percent}%)"
    return msg, None

def change_password(new_pass):
    try:
        username = os.getenv("USERNAME")
        result = subprocess.run(["net", "user", username, new_pass], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return None, None
        else:
            return None, result.stderr
    except Exception as e:
        return None, str(e)

def execute_task(task):
    cmd = task.get("cmd", "")
    chat_id = task.get("chat_id")
    args = task.get("args", "")

    output = None
    error = None
    photo_path = None

    if cmd == "status":
        output, error = get_status()
    elif cmd == "shutdown":
        output = "🛑 Shutting down..."
        threading.Thread(target=lambda: os.system("shutdown /s /t 3"), daemon=True).start()
    elif cmd == "restart":
        output = "🔄 Restarting..."
        threading.Thread(target=lambda: os.system("shutdown /r /t 3"), daemon=True).start()
    elif cmd == "lock":
        os.system("rundll32.exe user32.dll,LockWorkStation")
        output = "🔒 Locked"
    elif cmd == "password":
        error = change_password(args)
        if not error:
            output = "✅ Password changed"
    elif cmd == "cmd":
        output, error = run_cmd(args)
    elif cmd == "screenshot":
        photo_path, error = take_screenshot()
        if photo_path:
            output = "📸 Screenshot taken"
    else:
        error = f"Unknown command: {cmd}"

    # Send result back to server
    result_data = {"cmd": cmd, "chat_id": chat_id, "output": output, "error": error}
    if photo_path:
        result_data["photo_path"] = photo_path

    try:
        requests.post(f"{SERVER_URL}/api/result", json=result_data, timeout=15)
    except Exception as e:
        print(f"Failed to send result: {e}")

def main():
    print("=" * 40)
    print("Telegram Remote Agent - Starting")
    print(f"Server: {SERVER_URL}")
    print(f"IP: {get_local_ip()}")
    print("=" * 40)

    last_heartbeat = 0

    while True:
        now = time.time()

        # Heartbeat
        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            last_heartbeat = now
            try:
                resp = requests.post(f"{SERVER_URL}/api/heartbeat",
                    json={"ip": get_local_ip()}, timeout=10)
                if resp.ok:
                    data = resp.json()
                    tasks = data.get("tasks", [])
                    for t in tasks:
                        execute_task(t)
            except requests.exceptions.ConnectionError:
                print(f"Connection error to {SERVER_URL}")
            except Exception as e:
                print(f"Heartbeat error: {e}")

        # Poll for new tasks
        try:
            resp = requests.get(f"{SERVER_URL}/api/tasks", timeout=10)
            if resp.ok:
                tasks = resp.json()
                for t in tasks:
                    execute_task(t)
        except:
            pass

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
