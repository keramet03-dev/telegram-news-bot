import asyncio
import feedparser
from telethon import TelegramClient
from deep_translator import GoogleTranslator
from datetime import datetime
import os

# Environment variables
API_ID = int(os.getenv('API_ID', '39717958'))
API_HASH = os.getenv('API_HASH', 'e8e1f10ee0080cc64f3d8027a1de2088')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8074459853:AAEUYnKc_9IuKZsD3tuLEu9mj-vTYIrXIwA')
KANAL = os.getenv('KANAL', '@xeberdunyasiaz')

# 18 keyfiyyətli mənbə
NEWS = {
    # Azərbaycan (4)
    'APA': 'https://apa.az/rss/az/news',
    'Trend': 'https://az.trend.az/rss/',
    'Report': 'https://report.az/rss/',
    'Oxu.az': 'https://oxu.az/rss/news',
    
    # Türkiyə - Dünya xəbərləri (4)
    'Anadolu Dünya': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
    'TRT Dünya': 'https://www.trthaber.com/dunya.rss',
    'Hürriyet Dünya': 'https://www.hurriyet.com.tr/rss/dunya',
    'NTV Dünya': 'https://www.ntv.com.tr/dunya.rss',
    
    # Beynəlxalq (5)
    'Reuters': 'http://feeds.reuters.com/reuters/topNews',
    'BBC': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'DW': 'https://rss.dw.com/rdf/rss-en-all',
    'CNN': 'http://rss.cnn.com/rss/edition_world.rss',
    
    # Elmi/Maraqlı (5)
    'Evrim Ağacı': 'https://evrimagaci.org/rss',
    'Nat Geo': 'https://www.nationalgeographic.com/pages/topic/latest-stories/_jcr_content.feed',
    'ScienceDaily': 'https://www.sciencedaily.com/rss/top.xml',
    'BBC Science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    'PopSci': 'https://www.popsci.com/feed/',
}

def get_news(url):
    try:
        f = feedparser.parse(url)
        if f.entries:
            e = f.entries[0]
            return {
                'title': e.title,
                'link': e.link,
                'source': f.feed.get('title', 'Unknown')
            }
    except:
        pass
    return None

def tr(text):
    try:
        return GoogleTranslator(source='auto', target='az').translate(text[:400])
    except:
        return text

def improve_title(title):
    """Sadə başlıq təkmilləşdirmə - emoji əlavə et"""
    if any(word in title.lower() for word in ['təcili', 'son dəqiqə', 'breaking', 'urgent']):
        return f"⚡ {title}"
    elif any(word in title.lower() for word in ['prezident', 'president', 'hökumət', 'government']):
        return f"🏛 {title}"
    elif any(word in title.lower() for word in ['iqtisad', 'economy', 'maliyyə', 'finance', 'dollar']):
        return f"💰 {title}"
    elif any(word in title.lower() for word in ['elm', 'science', 'texnologiya', 'technology']):
        return f"🔬 {title}"
    elif any(word in title.lower() for word in ['idman', 'sport', 'futbol']):
        return f"⚽ {title}"
    else:
        return f"📰 {title}"

async def post(c):
    print(f"\n🔄 [{datetime.now().strftime('%H:%M')}] Xəbərlər toplanır...")
    
    all_news = []
    for name, url in NEWS.items():
        x = get_news(url)
        if x:
            need_tr = name not in ['APA', 'Trend', 'Report', 'Oxu.az']
            t = tr(x['title']) if need_tr else x['title']
            t = improve_title(t)
            
            m = f"{t}\n\n📰 {name}\n🔗 [Oxu]({x['link']})\n\n#xəbər"
            
            all_news.append({'name': name, 'msg': m})
    
    # Smart paylaşım: 3-1-3-1 pattern
    count = 0
    for i, news in enumerate(all_news):
        try:
            await c.send_message(KANAL, news['msg'])
            print(f"✅ [{i+1}/{len(all_news)}] {news['name']}")
            count += 1
            
            if (i + 1) % 3 == 0:
                print("⏸ 2.5 dəqiqə ara...")
                await asyncio.sleep(150)
            else:
                await asyncio.sleep(10)
                
        except Exception as e:
            print(f"❌ {news['name']}: {e}")
    
    print(f"\n✅ Cəmi {count} xəbər paylaşıldı!\n")

async def main():
    print("🤖 XƏBƏR DÜNYASI BOT - VERSİYA 2.0")
    print("=" * 50)
    c = TelegramClient('bot', API_ID, API_HASH)
    await c.start(bot_token=BOT_TOKEN)
    print(f"✅ Bot işə düşdü!")
    print(f"📢 Kanal: {KANAL}")
    print(f"🌍 Mənbə: {len(NEWS)} keyfiyyətli")
    print(f"⏰ Smart paylaşım aktiv")
    print(f"🔄 Hər 3 saatda yenilənir\n")
    
    while True:
        await post(c)
        print("⏰ 3 saat gözləyir...\n")
        await asyncio.sleep(10800)

if __name__ == '__main__':
    asyncio.run(main())
