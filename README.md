[README.md](https://github.com/user-attachments/files/30383306/README.md)
# Bexa SMM — Bot + Mini-ilova

## Tuzilishi
```
bexa/
├── config.py           # Token, narxlar, admin ID — SHU YERDA SOZLANG
├── db.py                # Umumiy SQLite baza (bot va backend ikkalasi ishlatadi)
├── utils.py              # Narx hisoblash, initData tekshirish
├── bot.py                 # Telegram bot: Stars/Premium bot ichida, admin buyurtma boshqaruvi
├── webapp_backend.py      # Mini-ilova uchun FastAPI backend (API + frontend serve qiladi)
├── static/index.html      # Mini-ilova frontend (bitta fayl)
├── requirements.txt
└── orders.db               # Avtomatik yaratiladi (bot yoki backend birinchi ishga tushganda)
```

## Nima botda, nima mini-ilovada?
- **Botda qoldi:** ⭐ Telegram Stars, 💎 Telegram Premium (oddiy matnli suhbat orqali)
- **Mini-ilovada:** Telegram nakrutka, Instagram, TikTok, YouTube, Meta Verify, Bot yaratish
- **Ikkalasi ham** bitta `orders.db` bazasini ishlatadi — buyurtmalar qayerdan kelishidan qat'iy nazar, xuddi shu `@zakaz_bexa` kanaliga, xuddi shu ✅/❌ tugmalar bilan tushadi.

## 1-qadam: sozlash
`config.py` faylini oching va o'zgartiring:
- `BOT_TOKEN` — bot tokeningiz
- `CHANNEL_ID` — buyurtmalar tushadigan kanal
- `SUPER_ADMIN_ID` — sizning Telegram ID'ingiz (bazadan o'chirib bo'lmaydigan bosh admin)
- `WEBAPP_URL` — **hosting qilingandan keyin** shu yerga HTTPS manzilni yozasiz

## 2-qadam: lokal test (ixtiyoriy)
```bash
pip install -r requirements.txt
python bot.py                 # 1-terminalda
uvicorn webapp_backend:app --host 0.0.0.0 --port 8000   # 2-terminalda
```
Eslatma: Telegram Mini App faqat **HTTPS** manzilda ishlaydi, shuning uchun lokal `localhost` bilan botdagi "Mini-ilova" tugmasini sinab bo'lmaydi — buni chin serverda yoki `ngrok` kabi tunnel orqali sinab ko'rish mumkin.

## 3-qadam: serverga joylash (masalan Railway/Render/VPS)
1. Butun `bexa/` papkani serverga yuklang
2. `pip install -r requirements.txt`
3. Ikkita alohida process ishga tushirish kerak:
   - **Bot**: `python bot.py` (doim fon rejimida, masalan `systemd` yoki `pm2` orqali)
   - **Backend**: `uvicorn webapp_backend:app --host 0.0.0.0 --port 8000` (bu ham doim ishlab turishi kerak, oldida Nginx/hosting platformasi HTTPS domen beradi)
4. Backend uchun olingan HTTPS domenni `config.py` dagi `WEBAPP_URL` ga yozing va botni qayta ishga tushiring
5. [@BotFather](https://t.me/BotFather) → botingiz → **Bot Settings → Menu Button** orqali ham xohlasangiz shu domenni asosiy menyu tugmasi qilib qo'yishingiz mumkin (ixtiyoriy, chunki botda allaqachon "🌐 Mini-ilova" tugmasi bor)

## Muhim eslatmalar
- `orders.db` — bitta fayl, ham bot, ham backend shu fayldan foydalanadi. Ikkalasi ham **bir xil papkada** ishga tushirilishi kerak (yoki `config.py`dagi `DB_PATH`ni to'liq yo'l qilib bering).
- Bosh admin (`SUPER_ADMIN_ID`) mini-ilova admin panelidan o'chirib bo'lmaydi — bu qulflanib qolmaslik uchun himoya.
- `BOT_TOKEN` kodda ochiq turibdi — production'da muhit o'zgaruvchisi (`.env`) orqali yuklashni tavsiya qilamiz.
