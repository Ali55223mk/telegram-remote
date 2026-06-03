# Telegram Remote Control

تحكم بجهاز الكمبيوتر عن بعد عبر تليجرام.

## المكونات

- **Server** — بوت تليجرام على Railway (شغال 24/7)
- **Agent** — سكربت صغير على جهازك يربط البوت بالكمبيوتر

## النشر

1. ارفع مجلد `server/` إلى GitHub
2. Connect Railway → GitHub repo
3. ضع المتغيرات في Railway Dashboard → Variables:
   - `BOT_TOKEN` = توكين البوت
   - `AUTHORIZED_USERS` = 6337140367
   - `PC_MAC` = عنوان MAC حق كرت الشبكة

## التشغيل المحلي

1. شغّل `agent.py` على جهازك (يشتغل في الخلفية)
2. استخدم `agent_startup.bat` لإضافته للتشغيل التلقائي
