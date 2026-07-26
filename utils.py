import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from config import UNIT_PRICES


def format_price(n):
    return f"{int(n):,}".replace(",", " ") + " so'm"


def calc_unit_price(category, amount_text):
    try:
        amount = int(amount_text)
    except (TypeError, ValueError):
        return 0
    return UNIT_PRICES.get(category, 0) * amount


def validate_init_data(init_data: str, bot_token: str):
    """Telegram Mini App initData'sini HMAC orqali tekshiradi.
    Muvaffaqiyatli bo'lsa parsed dict qaytaradi, aks holda None."""
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    return parsed


def get_tg_user_from_init_data(init_data: str, bot_token: str):
    parsed = validate_init_data(init_data, bot_token)
    if not parsed or "user" not in parsed:
        return None
    try:
        return json.loads(parsed["user"])
    except (json.JSONDecodeError, TypeError):
        return None
