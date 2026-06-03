# Telegram Remote Control 🎛

تحكم بجهاز الكمبيوتر عن بعد عبر تليجرام — مجاني 24/7.

## المكونات

```
📱 تلفونك → Telegram → 🌐 Railway (server) → 💻 جهازك (agent)
```

- **Server** (`server/`) — بوت تليجرام على Railway، شغال 24 ساعة مجاناً
- **Agent** (`agent.py`) — سكربت على جهازك، يربط البوت بالويندوز

## الأوامر

| الأمر | الوظيفة |
|---|---|
| `/start` | قائمة الأوامر |
| `/status` | حالة الجهاز (CPU, RAM, uptime) |
| `/shutdown` | إطفاء الكمبيوتر |
| `/restart` | إعادة تشغيل |
| `/lock` | قفل الشاشة |
| `/password 123456` | تغيير كلمة سر المستخدم |
| `/cmd ipconfig` | تشغيل أمر CMD |
| `/screenshot` | تصوير الشاشة |
| `/wol AA:BB:CC:DD:EE:FF` | تشغيل الجهاز عن بعد (Wake-on-LAN) |
| `/setmac AA:BB:CC:DD:EE:FF` | حفظ MAC address |

## النشر (مرة واحدة)

### 1. إنشاء حساب Railway
- افتح [railway.app](https://railway.app)
- سجل دخول بـ GitHub (نفس الحساب اللي رفعت عليه)

### 2. ربط المستودع
- Dashboard → New Project → Deploy from GitHub repo
- اختار `Ali55223mk/telegram-remote`
- Settings → Health Check Path: `/`

### 3. ضبط المتغيرات
- Project → Variables → New Variable:

| المتغير | القيمة |
|---|---|
| `BOT_TOKEN` | `8999468767:AAGvs27z1D3FUwPMCjmPdYZiQfMAR6vkss8` |
| `AUTHORIZED_USERS` | `6337140367` |
| `PC_MAC` | (MAC address حق كرت الشبكة عندك) |

### 4. ضبط Webhook (مهم)
- من Railway خذ الـ URL: `https://your-project.up.railway.app`
- افتح في المتصفح:
  `https://api.telegram.org/bot8999468767:AAGvs27z1D3FUwPMCjmPdYZiQfMAR6vkss8/setWebhook?url=https://your-project.up.railway.app/webhook`
- إذا ظهر `ok: true` تم الضبط ✅

## تشغيل الـ Agent على جهازك

1. شغّل `install_deps.bat` لتثبيت المكتبات
2. افتح `agent.py` وغير `SERVER_URL` إلى رابط Railway حقك
3. شغّل `agent_startup.bat` (يشتغل في الخلفية)
4. (اختياري) اضغط `Win+R` → اكتب `shell:startup` → ضع اختصار لـ `agent_startup.bat`

## Wake-on-LAN (تشغيل الجهاز وهو طافي)

1. ادخل BIOS (F2/Del عند البدأ)
2. فعّل **Wake-on-LAN** / **Power On By PCI-E**
3. شغل كمد كأدمن:
   ```
   powercfg /h off
   ```
4. من Device Manager → Network Adapter → حق كرت الشبكة → Advanced → Wake on Magic Packet → Enabled
5. استخدم `/wol` في البوت لتشغيل الجهاز عن بعد
