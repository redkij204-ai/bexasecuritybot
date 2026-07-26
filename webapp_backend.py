import html
import json
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from config import BOT_TOKEN, CHANNEL_ID, META_VERIFY_PRICE
from utils import format_price, calc_unit_price, get_tg_user_from_init_data

app = FastAPI(title="Bexa SMM Mini App")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

db.init_db()

# Mini-ilovada ko'rsatiladigan xizmatlar katalogi
# (Telegram Stars va Telegram Premium bilan bu yerda ishlanmaydi - ular botda qoladi)
SERVICE_CATALOG = {
    "telegram": {
        "title": "Telegram nakrutka",
        "icon": "✈️",
        "price_key": "Telegram nakrutka",
        "sub_services": ["Bot uchun", "Kanal yoki guruh", "Reaksiya", "Prasmotr",
                          "So'rovnoma uchun", "Premium nakrutka", "Boost"],
        "has_quality": True,
    },
    "instagram": {
        "title": "Instagram",
        "icon": "📸",
        "price_key": "Instagram",
        "sub_services": ["Obunachi", "Like", "Comment", "Prasmotr", "Jonli efir kuzatuvchilari"],
        "has_quality": True,
    },
    "tiktok": {
        "title": "TikTok",
        "icon": "🎵",
        "price_key": "TikTok",
        "sub_services": ["Obunachi", "Like", "Comment", "Prasmotr", "Jonli efir kuzatuvchilari"],
        "has_quality": True,
    },
    "youtube": {
        "title": "YouTube",
        "icon": "▶️",
        "price_key": "YouTube",
        "sub_services": ["Obunachi", "Like", "Comment", "Prasmotr", "Jonli efir kuzatuvchilari"],
        "has_quality": True,
    },
    "meta_verify": {
        "title": "Meta Verify (Galochka)",
        "icon": "✅",
        "price": META_VERIFY_PRICE,
        "fixed": True,
    },
    "bot_build": {
        "title": "Bot yaratish",
        "icon": "🤖",
        "price": 0,
        "fixed": True,
        "needs_details": True,
    },
}


# ---------------- AUTH ----------------
def get_tg_user(x_telegram_init_data: Optional[str] = Header(None)):
    if not x_telegram_init_data:
        raise HTTPException(401, "initData yo'q")
    user = get_tg_user_from_init_data(x_telegram_init_data, BOT_TOKEN)
    if not user:
        raise HTTPException(401, "initData yaroqsiz")
    return user


def require_admin(user=Depends(get_tg_user)):
    if not db.is_admin(user["id"]):
        raise HTTPException(403, "Ruxsat yo'q")
    return user


# ---------------- UMUMIY ----------------
@app.get("/api/services")
def api_services():
    return SERVICE_CATALOG


@app.get("/api/me")
def api_me(user=Depends(get_tg_user)):
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    db.save_user(user["id"], user.get("username"), full_name)
    db_user = db.get_user(user["id"])
    return {
        "id": user["id"],
        "username": user.get("username"),
        "full_name": full_name,
        "phone": db_user["phone"] if db_user else None,
        "is_admin": db.is_admin(user["id"]),
    }


# ---------------- BUYURTMA ----------------
class OrderIn(BaseModel):
    category: str
    sub_service: Optional[str] = None
    quality: Optional[str] = None
    amount: Optional[str] = None
    link: Optional[str] = None
    details: Optional[str] = None


@app.post("/api/order")
async def api_create_order(order_in: OrderIn, user=Depends(get_tg_user)):
    cat = SERVICE_CATALOG.get(order_in.category)
    if not cat:
        raise HTTPException(400, "Noto'g'ri xizmat turi")

    db_user = db.get_user(user["id"])
    phone = db_user["phone"] if db_user else None

    if cat.get("fixed"):
        service_name = cat["title"]
        price = cat["price"]
    else:
        if not order_in.sub_service or not order_in.amount:
            raise HTTPException(400, "Xizmat turi va miqdor kiritilishi shart")
        service_name = f"{cat['title']} -> {order_in.sub_service}"
        price = calc_unit_price(cat["price_key"], order_in.amount)

    order_id = db.save_order({
        "user_id": user["id"],
        "service": service_name,
        "quality": order_in.quality,
        "amount": order_in.amount,
        "link": order_in.link,
        "target_user": None,
        "details": order_in.details,
        "price": price,
    })

    await notify_admin_channel(order_id, user, phone, service_name, order_in, price)

    return {"order_id": order_id, "price": price}


async def notify_admin_channel(order_id, user, phone, service_name, order_in, price):
    full_name = html.escape(f"{user.get('first_name', '')} {user.get('last_name', '')}".strip())
    username = html.escape(user.get("username") or "Yo'q")

    text = "📥 <b>Yangi Buyurtma! (Mini-ilova)</b>\n\n"
    text += f"🆔 <b>Buyurtma raqami:</b> #{order_id}\n"
    text += f"👤 <b>Mijoz:</b> {full_name} (@{username})\n"
    text += f"📞 <b>Tel:</b> <code>{html.escape(str(phone or 'Kiritilmagan'))}</code>\n"
    text += f"🛠 <b>Xizmat:</b> {html.escape(service_name)}\n"
    if order_in.quality:
        text += f"✨ <b>Sifat:</b> {html.escape(order_in.quality)}\n"
    if order_in.amount:
        text += f"🔢 <b>Miqdor:</b> {html.escape(order_in.amount)}\n"
    if order_in.link:
        text += f"🔗 <b>Link:</b> {html.escape(order_in.link)}\n"
    if order_in.details:
        text += f"📝 <b>Batafsil:</b> {html.escape(order_in.details)}\n"
    if price:
        text += f"💰 <b>Narx:</b> {format_price(price)}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Bajarildi", "callback_data": f"order_done_{order_id}"},
            {"text": "❌ Rad etildi", "callback_data": f"order_reject_menu_{order_id}"},
        ]]
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
        )
        if resp.status_code != 200:
            # Xatolikni log qilamiz, lekin foydalanuvchiga xato ko'rsatmaymiz -
            # buyurtma bazaga saqlangan, admin uni baribir /api/admin/orders orqali ko'radi
            print(f"Kanalga yuborishda xatolik: {resp.text}")


@app.get("/api/orders/history")
def api_order_history(user=Depends(get_tg_user)):
    return db.get_user_orders(user["id"])


# ---------------- ADMIN ----------------
@app.get("/api/admin/stats")
def api_admin_stats(admin=Depends(require_admin)):
    return db.get_stats()


@app.get("/api/admin/users")
def api_admin_users(admin=Depends(require_admin)):
    return db.get_all_users()


@app.get("/api/admin/orders")
def api_admin_orders(admin=Depends(require_admin)):
    return db.get_recent_orders()


@app.get("/api/admin/admins")
def api_admin_admins(admin=Depends(require_admin)):
    return db.get_admins()


class AdminIn(BaseModel):
    user_id: int
    username: Optional[str] = None


@app.post("/api/admin/admins/add")
def api_admin_add(payload: AdminIn, admin=Depends(require_admin)):
    db.add_admin(payload.user_id, payload.username)
    return {"ok": True}


@app.post("/api/admin/admins/remove")
def api_admin_remove(payload: AdminIn, admin=Depends(require_admin)):
    ok = db.remove_admin(payload.user_id)
    if not ok:
        raise HTTPException(400, "Bosh adminni o'chirib bo'lmaydi")
    return {"ok": True}


@app.get("/api/admin/channels")
def api_admin_channels(admin=Depends(require_admin)):
    return db.get_required_channels()


class ChannelIn(BaseModel):
    channel_username: str


@app.post("/api/admin/channels/add")
def api_channels_add(payload: ChannelIn, admin=Depends(require_admin)):
    db.add_required_channel(payload.channel_username)
    return {"ok": True}


@app.post("/api/admin/channels/remove")
def api_channels_remove(payload: ChannelIn, admin=Depends(require_admin)):
    db.remove_required_channel(payload.channel_username)
    return {"ok": True}


# Frontendni statik fayl sifatida ulash (eng oxirida bo'lishi kerak!)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
