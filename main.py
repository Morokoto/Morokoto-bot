import os, requests
from fastapi import FastAPI, Request

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MORO_MINT        = os.getenv("MORO_MINT", "6VwVLD5yM7zf7gFozf1hLHg7LJ3zeGwSLLFPTq9Vpump")
PAIR_ADDRESS     = os.getenv("PAIR_ADDRESS", "brbbqxmeauveevcnqsxd2quxvgdqpjwwckyxh5s2qqex")
CARD_IMAGE_URL   = os.getenv("CARD_IMAGE_URL", "https://YOUR-DOMAIN/path/to/morokoto-eye.jpg")
DEX_BUY_URL      = os.getenv("DEX_BUY_URL")
SCREENER_URL     = os.getenv("SCREENER_URL")

SOL_PSEUDO_MINT  = "So11111111111111111111111111111111111111112"  # SOL

app = FastAPI()

def fmt(n, d=4):
    try:
        return f"{float(n):,.{d}f}"
    except:
        return str(n)

def green_dots(qty_moro: float) -> str:
    points = int(qty_moro // 5_000)
    if points <= 0:
        points = 1
    max_visible = 300
    if points <= max_visible:
        return "🟢" * points
    hidden = points - max_visible
    return ("🟢" * max_visible) + f" (+{hidden})"

def sol_price_usd() -> float:
    try:
        r = requests.get("https://price.jup.ag/v6/price?ids=SOL", timeout=6)
        return float(r.json()["data"]["SOL"]["price"])
    except:
        return 0.0

def dexscreener_pair() -> dict:
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{PAIR_ADDRESS}"
        r = requests.get(url, timeout=8)
        pairs = r.json().get("pairs", [])
        return pairs[0] if pairs else {}
    except:
        return {}

def send_photo_with_caption(caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": CARD_IMAGE_URL,
        "caption": caption,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    requests.post(url, json=payload, timeout=10)

def build_caption(qty_moro, spent_sol, buyer, sig):
    # Precio SOL
    try:
        r = requests.get("https://price.jup.ag/v6/price?ids=SOL", timeout=6)
        sol_usd = float(r.json()["data"]["SOL"]["price"])
    except:
        sol_usd = 0.0

    spent_usd = spent_sol * sol_usd if sol_usd and spent_sol else None

    # Market cap Dexscreener
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{PAIR_ADDRESS}"
        pr = requests.get(url, timeout=8)
        pairs = pr.json().get("pairs", [])
        pair = pairs[0] if pairs else {}
        mcap = pair.get("fdv") or pair.get("marketCap")
    except:
        mcap = None

    dots = green_dots(qty_moro)
    solscan_tx = f"https://solscan.io/tx/{sig}" if sig else ""
    birdeye_tx = f"https://birdeye.so/tx/{sig}" if sig else ""

    lines = [
        f"*Morokoto Buy!* {dots}",
        "",
        f"🧾 *Spent:* ${fmt(spent_usd,2)} ({fmt(spent_sol,4)} SOL)" if spent_usd else f"🧾 *Spent:* {fmt(spent_sol,4)} SOL",
        f"📦 *Got:* {fmt(qty_moro,2)} MORO",
        f"👤 [Buyer]({solscan_tx}) / [TX]({solscan_tx})" if sig else "👤 Buyer",
        f"💰 *Market Cap:* ${fmt(mcap,0)}" if mcap else None,
        "",
        f"[Screener]({SCREENER_URL}) | [Buy]({DEX_BUY_URL}) | [Birdeye]({birdeye_tx})"
    ]
    return "\n".join([x for x in lines if x is not None])

@app.get("/")
def root():
    return {"ok": True, "msg": "Morokoto bot up"}

@app.post("/hook")
async def hook(req: Request):
    body = await req.json()
    events = body if isinstance(body, list) else [body]

    for ev in events:
        sig = ev.get("signature") or (ev.get("transaction", {}).get("signatures", [None])[0])
        changes = ev.get("tokenBalanceChanges") or ev.get("tokenTransfers") or []

        received = next((c for c in changes if c.get("mint")==MORO_MINT and (
                        (c.get("delta") and float(c["delta"])>0) or
                        (c.get("tokenAmount",{}).get("amount") and float(c["tokenAmount"]["amount"])>0))), None)
        if not received:
            continue

        pay_mints = {SOL_PSEUDO_MINT, "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
        paid = next((c for c in changes if c.get("mint") in pay_mints and (
                    (c.get("delta") and float(c["delta"])<0) or
                    (c.get("tokenAmount",{}).get("amount") and float(c["tokenAmount"]["amount"])<0))), None)
        if not paid:
            continue

        moro_dec = int(received.get("decimals") or received.get("tokenAmount",{}).get("decimals", 9))
        moro_raw = float(received.get("delta") or received.get("tokenAmount",{}).get("amount", 0))
        qty_moro = abs(moro_raw) / (10 ** moro_dec)

        spent_sol = 0.0
        if paid.get("mint")==SOL_PSEUDO_MINT:
            sol_dec = int(paid.get("decimals") or paid.get("tokenAmount",{}).get("decimals", 9))
            sol_raw = float(paid.get("delta") or paid.get("tokenAmount",{}).get("amount", 0))
            spent_sol = abs(sol_raw) / (10 ** sol_dec)

        buyer = received.get("owner") or received.get("userAccount") or "wallet"
        caption = build_caption(qty_moro, spent_sol, buyer, sig)
        send_photo_with_caption(caption)

    return {"ok": True}
