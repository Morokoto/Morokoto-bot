# Morokoto Buy Bot (Telegram + Solana)

Publica una tarjeta de compra en tu canal de Telegram con **imagen fija** (ojo Morokoto) y texto dinámico:
- Spent (USD/SOL)
- Got (MORO)
- Market Cap (desde Dexscreener)
- Links (Screener / Buy / Birdeye / TX)
- **Puntos verdes 🟢**: 1 por cada **5,000 MORO**, sin tope (se resume con `(+N)` si excede el límite de Telegram).

## 1) Archivos
- `main.py` — servidor FastAPI que recibe webhooks de Helius/QuickNode y publica en Telegram.
- `requirements.txt` — dependencias.
- `Procfile` — arranque para Railway.
- `.env.example` — variables de entorno (renómbralo a `.env` **solo si corres local**).

## 2) Variables de entorno (Railway / Render)
Configura estas variables en tu panel (no subas `.env` con secretos a GitHub):
- `TELEGRAM_TOKEN` — token del bot de @BotFather
- `TELEGRAM_CHAT_ID` — id de tu canal (empieza con `-100...`)
- `MORO_MINT` — mint del token Morokoto en Solana
- `PAIR_ADDRESS` — id del par en Dexscreener (solo el slug final)
- `CARD_IMAGE_URL` — URL pública de tu imagen del ojo
- `DEX_BUY_URL` — link directo de compra (Jupiter o Raydium)
- `SCREENER_URL` — página de Dexscreener del par

## 3) Instalar local (opcional)
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Prueba en el navegador: `http://localhost:8000/`

## 4) Deploy en Railway
- Sube estos archivos a un repo de GitHub.
- Crea proyecto en Railway → "Deploy from GitHub".
- Añade variables de entorno (arriba).
- Railway arrancará con el `Procfile`.

## 5) Webhook (Helius/QuickNode)
- Crea un **Enhanced/Parsed Transaction Webhook** apuntando a: `https://TU-URL/hook`
- Filtro: **Accounts include** = tu mint `MORO_MINT`.
- Guardar.

## 6) Probar Telegram manualmente
Asegúrate de que el bot es **admin** del canal.
```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendPhoto"   -H "Content-Type: application/json"   -d '{
    "chat_id": "'$TELEGRAM_CHAT_ID'",
    "photo": "'$CARD_IMAGE_URL'",
    "caption": "Morokoto Buy! 🟢🟢",
    "parse_mode": "Markdown"
  }'
```

## 7) Cambiar escala de puntos 🟢
En `main.py`, función `green_dots`: cambia `5_000` al valor que quieras por punto.

---

**Nota:** No expongas tu `TELEGRAM_TOKEN` públicamente. Usa variables de entorno en Railway/Render.
