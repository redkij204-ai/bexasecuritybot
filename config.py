# --- SOZLAMALAR ---
BOT_TOKEN = "8980343439:AAGfJoL2gOBhxzQJxhtP6Ui_kfzdRDzTtaw"
CHANNEL_ID = "@zakaz_bexa"                    # Buyurtmalar tushadigan kanal
SUPER_ADMIN_ID = 7637455479                   # Bosh admin (bazadan o'chirib bo'lmaydi)
DEFAULT_REQUIRED_CHANNEL = "@bexa_security"   # Boshlang'ich majburiy obuna kanali
DB_PATH = "orders.db"

# Mini-ilovangiz joylashgan HTTPS manzil (Railway/Render/VPS domeningiz).
# Buni deploy qilgach albatta o'zgartiring - "https://" bilan boshlanishi shart!
WEBAPP_URL = "https://telegram-bot-production-f8d2.up.railway.app"

# --- NARXLAR (so'mda) - o'zingizga moslab o'zgartiring ---
UNIT_PRICES = {
    "Telegram nakrutka": 5000,
    "Instagram": 35000,
    "TikTok": 35000,
    "YouTube": 88000,
}
PREMIUM_PRICES = {
    "1 oylik": 45000,
    "3 oylik": 120000,
    "6 oylik": 220000,
    "1 yillik": 400000,
}
STARS_UNIT_PRICE = 250
META_VERIFY_PRICE = 15000
