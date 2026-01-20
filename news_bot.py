#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, asyncio, re, sqlite3, random
from datetime import datetime
import feedparser
from telethon import TelegramClient
from telethon.sessions import MemorySession
from deep_translator import GoogleTranslator

# ================== ENV ==================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
KANAL = os.getenv("KANAL", "@xeberdunyasiaz")

# ================== DB ==================
DB_FILE = "news.db"

def init_db():
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS posted (
            link TEXT PRIMARY KEY,
            type TEXT,
            time TIMESTAMP
        )
        """)

def is_posted(link):
    with sqlite3.connect(DB_FILE) as db:
        r = db.execute("SELECT 1 FROM posted WHERE link=?", (link,)).fetchone()
        return r is not None

def mark_posted(link, type_):
    with sqlite3.connect(DB_FILE) as db:
        try:
            db.execute("INSERT INTO posted VALUES (?,?,?)",
                       (link, type_, datetime.now()))
        except:
            pass

# ================== SOURCES ==================
NEWS = {
    "APA": "https://apa.az/rss/az/news",
    "Report": "https://report.az/rss/",
    "Trend": "https://az.trend.az/rss/",
    "Oxu.az": "https://oxu.az/rss/news",
    "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "DW": "https://rss.dw.com/rdf/rss-en-all",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "CNN": "http://rss.cnn.com/rss/edition_world.rss",
    "Sky News": "https://feeds.skynews.com/feeds/rss/world.xml",
}

AZ_SOURCES = {"APA", "Report", "Trend", "Oxu.az"}

FUN = {
    "r/memes": "https://www.reddit.com/r/memes/.rss",
    "r/funny": "https://www.reddit.com/r/funny/.rss",
    "r/aww": "https://www.reddit.com/r/aww/.rss",
    "r/wholesomememes": "https://www.reddit.com/r/wholesomememes/.rss",
}

# ================== UTILS ==================
def clean(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()

def translate(text):
    if not text or len(text) > 200:
        return text
    try:
        return GoogleTranslator(source="auto", target="az").translate(text)
    except:
        return text

def make_title(title, source):
    title = title.strip()
    if source in AZ_SOURCES and any(x in title.lower() for x in ["son", "təcili"]):
        return f"🔴 SON DƏQİQƏ: {title}"
    return f"📰 {title}"

def extract_media(entry):
    if "media_content" in entry:
        url = entry.media_content[0].get("url")
        if url and not url.startswith("https://v.redd.it"):
            return url
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0].get("url")
    return None

# ================== NEWS ==================
def get_news(source, url):
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:7]:
            link = e.get("link")
            if not link or is_posted(link):
                continue

            title = clean(e.get("title"))
            content = clean(e.get("summary", ""))[:300]

            if source not in AZ_SOURCES:
                title = translate(title)

            return {
                "title": make_title(title, source),
                "content": content,
                "link": link,
                "source": source,
                "media": extract_media(e)
            }
    except Exception as e:
        print(f"❌ {source}: {e}")
    return None

# ================== FUN ==================
def extract_reddit_media(html):
    for pattern in [
        r"https://i\.redd\.it/[^\s\"<>]+\.(jpg|png|gif)",
        r"https://preview\.redd\.it/[^\s\"<>]+\.(jpg|png|gif)",
        r"https://i\.imgur\.com/[^\s\"<>]+\.(jpg|png|gif)"
    ]:
        m = re.search(pattern, html)
        if m:
            return m.group(0)
    return None

def get_fun(source, url):
    try:
        feed = feedparser.parse(url)
        random.shuffle(feed.entries)
        for e in feed.entries[:20]:
            link = e.get("link")
            if is_posted(link):
                continue

            html = e.get("content", [{}])[0].get("value", "")
            media = extract_reddit_media(html)
            if media:
                return {
                    "title": translate(clean(e.get("title"))),
                    "media": media,
                    "link": link,
                    "source": source
                }
    except Exception as e:
        print(f"❌ {source}: {e}")
    return None

# ================== POST ==================
async def post_news(client):
    posted = 0
    for source, url in NEWS.items():
        if posted >= 8:
            break

        news = get_news(source, url)
        if not news:
            continue

        msg = f"{news['title']}\n\n{news['content']}\n\n📰 {source}\n🔗 {news['link']}"

        try:
            if news["media"]:
                await client.send_file(KANAL, news["media"], caption=msg)
            else:
                await client.send_message(KANAL, msg)

            mark_posted(news["link"], "news")
            posted += 1
            print(f"✅ [{posted}/8] {source}: Göndərildi")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"❌ {source} xəta: {e}")

    return posted

async def post_fun(client):
    for source, url in FUN.items():
        fun = get_fun(source, url)
        if not fun:
            continue

        caption = f"😂 {fun['title']}\n\n📱 {source}\n\n#əyləncə #gülməli #meme"
        try:
            await client.send_file(KANAL, fun["media"], caption=caption)
            mark_posted(fun["link"], "fun")
            print(f"😂 Əyləncə: {source}")
            return
        except Exception as e:
            print(f"❌ {source}: {e}")
            continue

# ================== MAIN ==================
async def main():
    print("\n" + "="*60)
    print("🤖 XƏBƏR DÜNYASI BOT - V5 PRO + MemorySession")
    print("="*60)
    print(f"📢 Kanal: {KANAL}")
    print(f"📰 Xəbər mənbə: {len(NEWS)}")
    print(f"😂 Əyləncə mənbə: {len(FUN)}")
    print("🔄 Format: 8 xəbər → 1 əyləncə → 6 dəq")
    print("🔒 Təkrar yoxlama: aktiv")
    print("="*60 + "\n")
    
    init_db()

    client = TelegramClient(MemorySession(), API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)
    
    print("✅ Bot Telegram-a qoşuldu!\n")

    try:
        while True:
            print(f"{'='*60}")
            print(f"🔄 Yeni dövr: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            
            posted = await post_news(client)
            print(f"\n📊 {posted} xəbər göndərildi\n")
            
            await post_fun(client)
            
            print(f"\n{'='*60}")
            print("⏸ 6 dəqiqə fasilə...")
            print(f"{'='*60}\n")
            await asyncio.sleep(360)
    
    except KeyboardInterrupt:
        print("\n⚠️  Bot dayandırılır...")
    
    finally:
        await client.disconnect()
        print("👋 Bot bağlandı.")

if __name__ == "__main__":
    asyncio.run(main())
