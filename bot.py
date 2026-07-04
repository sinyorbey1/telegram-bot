#!/usr/bin/env python3
"""
Telegram Kod Forward Bot
Prime Duyuru -> SİNYOR | Kodsepeti
"""

import logging
import os
import re
import json
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Sabitler - Environment variables
API_ID = int(os.environ.get("API_ID", "39978792"))
API_HASH = os.environ.get("API_HASH", "4e1fdbca6802ec308cddff07ed8a7c14")
SOURCE_CHAT_ID = int(os.environ.get("SOURCE_CHAT_ID", "-1002214186195"))
DEST_CHAT_ID = int(os.environ.get("DEST_CHAT_ID", "-1003729562192"))
SESSION_STRING = os.environ.get("SESSION_STRING", "")

STATE_FILE = "forwarded_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except:
        pass

# Ana uygulama
app = None
forwarded_state = load_state()
forwarded_count = 0

async def handle_new_message(message: Message):
    """Yeni mesajı işle ve ilet. TÜM mesajları ilet."""
    global forwarded_count, forwarded_state

    text = message.text or message.caption or ""
    msg_id = message.id

    # Duplicate kontrolü
    state_key = f"{msg_id}"
    if state_key in forwarded_state:
        return

    # Boş mesaj kontrolü
    if not text and not message.media:
        return

    logger.info(f"[YENİ] ID:{msg_id} | {text[:80]}")

    try:
        # SADE FORMAT: Orijinal mesajı aynen gönder
        if message.photo:
            await app.send_photo(
                chat_id=DEST_CHAT_ID,
                photo=message.photo.file_id,
                caption=text if text else None,
            )
        elif message.document:
            await app.send_document(
                chat_id=DEST_CHAT_ID,
                document=message.document.file_id,
                caption=text if text else None,
            )
        elif message.video:
            await app.send_video(
                chat_id=DEST_CHAT_ID,
                video=message.video.file_id,
                caption=text if text else None,
            )
        elif message.animation:
            await app.send_animation(
                chat_id=DEST_CHAT_ID,
                animation=message.animation.file_id,
                caption=text if text else None,
            )
        elif text:
            await app.send_message(
                chat_id=DEST_CHAT_ID,
                text=text,
            )
        else:
            return

        forwarded_state[state_key] = True
        save_state(forwarded_state)
        forwarded_count += 1
        logger.info(f"[OK] #{forwarded_count}")

    except FloodWait as e:
        logger.warning(f"FloodWait: {e.value}s bekleniyor...")
        await asyncio.sleep(e.value)
        if state_key in forwarded_state:
            del forwarded_state[state_key]
        await handle_new_message(message)
    except Exception as e:
        logger.error(f"Hata: {e}", exc_info=True)

async def main():
    global app

    logger.info("Bot başlatılıyor...")

    if SESSION_STRING:
        app = Client(
            "bot",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING,
        )
    else:
        app = Client(
            "telegram_forward_bot",
            api_id=API_ID,
            api_hash=API_HASH,
        )

    await app.start()
    me = await app.get_me()
    logger.info(f"Giriş: {me.first_name} (@{me.username})")

    # Grupları kontrol et
    try:
        source = await app.get_chat(SOURCE_CHAT_ID)
        logger.info(f"Kaynak: {source.title}")
    except Exception as e:
        logger.error(f"Kaynak grup bulunamadı: {e}")
        await app.stop()
        return

    try:
        dest = await app.get_chat(DEST_CHAT_ID)
        logger.info(f"Hedef: {dest.title}")
    except Exception as e:
        logger.error(f"Hedef grup bulunamadı: {e}")
        await app.stop()
        return

    # Yeni mesajları dinle
    @app.on_message(filters.chat(SOURCE_CHAT_ID))
    async def new_message_handler(client: Client, message: Message):
        await handle_new_message(message)

    logger.info("=" * 50)
    logger.info("BOT AKTİF - Yeni mesajları dinliyor...")
    logger.info("=" * 50)

    # Sonsuz döngü
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot durduruldu.")
    except Exception as e:
        logger.error(f"Bot hatası: {e}", exc_info=True)
