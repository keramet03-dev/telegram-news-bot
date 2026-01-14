"""
Session String Generator

Bu skript Telegram Session String yaradır.
Serverlərə deploy edərkən bu string-i SESSION_STRING environment variable olaraq istifadə edin.

İstifadə:
    python generate_session.py

Nəticə SESSION_STRING environment variable-a kopyalanmalıdır.
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

print("=" * 60)
print("🔐 TELEGRAM SESSION STRING GENERATOR")
print("=" * 60)
print()
print("Bu skript bot üçün session string yaradır.")
print("Session string serverdə fayl əvəzinə istifadə olunur.")
print()

# API məlumatlarını al
api_id = input("API ID daxil edin: ").strip()
api_hash = input("API Hash daxil edin: ").strip()
bot_token = input("Bot Token daxil edin: ").strip()

async def generate():
    print("\n⏳ Session yaradılır...")
    
    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.start(bot_token=bot_token)
    
    session_string = client.session.save()
    
    await client.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ SESSION STRING YARADILDI!")
    print("=" * 60)
    print("\nBu dəyəri SESSION_STRING environment variable olaraq istifadə edin:\n")
    print("-" * 60)
    print(session_string)
    print("-" * 60)
    print("\n⚠️ DİQQƏT: Bu string-i heç kimlə paylaşmayın!")
    print("⚠️ Bu string bot-a tam giriş imkanı verir!")
    print()

if __name__ == '__main__':
    asyncio.run(generate())
