"""
Telegram Remote Control for Windows
Commands: shutdown, restart, lock, password, cmd, screenshot, status
"""

import asyncio
import os
import sys
import subprocess
import platform
import tempfile
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== CONFIG =====
TOKEN = "8999468767:AAGvs27z1D3FUwPMCjmPdYZiQfMAR6vkss8"
AUTHORIZED_USERS = {6337140367}
PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "pass.txt")
# ==================

def load_password():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            return f.read().strip()
    return None

def save_password(pwd):
    with open(PASSWORD_FILE, "w") as f:
        f.write(pwd)

def is_authorized(update: Update) -> bool:
    return update.effective_user.id in AUTHORIZED_USERS

async def auth_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_authorized(update):
        await update.message.reply_text("⛔ غير مصرح لك باستخدام هذا البوت.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    await update.message.reply_text(
        "مرحباً، أنا بوت التحكم عن بُعد.\n\n"
        "الأوامر:\n"
        "/shutdown - إيقاف التشغيل\n"
        "/restart - إعادة تشغيل\n"
        "/lock - قفل الشاشة\n"
        "/password <كلمة_السر> - تغيير كلمة سر المستخدم\n"
        "/cmd <أمر> - تشغيل أمر في CMD\n"
        "/screenshot - تصوير الشاشة\n"
        "/status - حالة الجهاز"
    )

async def shutdown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    await update.message.reply_text("🔄 يتم إيقاف التشغيل...")
    os.system("shutdown /s /t 5")

async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    await update.message.reply_text("🔄 يتم إعادة التشغيل...")
    os.system("shutdown /r /t 5")

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    await update.message.reply_text("🔒 يتم قفل الشاشة...")
    os.system("rundll32.exe user32.dll,LockWorkStation")

async def password_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /password <كلمة_السر>")
        return
    new_pass = " ".join(context.args)

    try:
        username = os.getenv("USERNAME")
        result = subprocess.run(
            ["net", "user", username, new_pass],
            capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            save_password(new_pass)
            await update.message.reply_text(f"✅ تم تغيير كلمة سر المستخدم `{username}` بنجاح.")
        else:
            await update.message.reply_text(f"❌ فشل التغيير:\n{result.stderr}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def cmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /cmd <أمر>")
        return
    command = " ".join(context.args)
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=30)
        output = result.stdout or result.stderr or "(لا يوجد مخرجات)"
        if len(output) > 4000:
            output = output[:4000] + "\n\n...(مبتور)"
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ انتهت المهلة (30 ثانية)")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def screenshot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    if ImageGrab is None:
        await update.message.reply_text("❌ Pillow غير مثبت. شغل: pip install Pillow")
        return
    try:
        img = ImageGrab.grab()
        path = os.path.join(tempfile.gettempdir(), "screenshot.png")
        img.save(path)
        with open(path, "rb") as f:
            await update.message.reply_photo(f, caption="📸 Screenshot")
        os.remove(path)
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في التصوير: {e}")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update, context): return
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time()) if psutil else None
        uptime = datetime.now() - boot_time if boot_time else None
        cpu = psutil.cpu_percent(interval=1) if psutil else "?"
        mem = psutil.virtual_memory() if psutil else None
        disk = psutil.disk_usage("/") if psutil else None
        hostname = platform.node()
        username = os.getenv("USERNAME")

        msg = (
            f"💻 **{hostname}**\n"
            f"👤 المستخدم: {username}\n"
            f"🕒 الجهاز شغال منذ: {uptime if uptime else 'N/A'}\n"
            f"⚙️ CPU: {cpu}%\n"
        )
        if mem:
            msg += f"🧠 RAM: {mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB ({mem.percent}%)\n"
        if disk:
            msg += f"💾 C: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shutdown", shutdown_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("password", password_cmd))
    app.add_handler(CommandHandler("cmd", cmd_cmd))
    app.add_handler(CommandHandler("screenshot", screenshot_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
