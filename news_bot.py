import os
import re
import asyncio
import feedparser
from datetime import datetime
from telethon import TelegramClient
from deep_translator import GoogleTranslator

# Environment variables
API_ID = int(os.getenv('API_ID', '39717958'))
API_HASH = os.getenv('API_HASH', 'e8e1f10ee0080cc64f3d8027a1de2088')
BOT_TOKEN = os.getenv('BOT_TOKEN', 'BURAYA_YENİ_BOT_TOKEN')
KANAL = os.getenv('KANAL', '@xeberdunyasiaz')

# 18 keyfiyyətli mənbə
NEWS = {
    'APA': 'https://apa.az/rss/az/news',
    'Trend': 'https://az.trend.az/rss/',
    'Report': 'https://report.az/rss/',
    'Oxu.az': 'https://oxu.az/rss/news',
    'Anadolu': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
    'TRT Dünya': 'https://www.trthaber.com/dunya.rss',
    'Hürriyet': 'https://www.hurriyet.com.tr/rss/dunya',
    'NTV': 'https://www.ntv.com.tr/dunya.rss',
    'Reuters': 'http://feeds.reuters.com/reuters/topNews',
    'BBC': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'DW': 'https://rss.dw.com/rdf/rss-en-all',
    'CNN': 'http://rss.cnn.com/rss/edition_world.rss',
    'Evrim Ağacı': 'https://evrimagaci.org/rss',
    'Nat Geo': 'https://www.nationalgeographic.com/pages/topic/latest-stories/_jcr_content.feed',
    'ScienceDaily': 'https://www.sciencedaily.com/rss/top.xml',
    'BBC Science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    'PopSci': 'https://www.popsci.com/feed/'
}

AZ_SOURCES = ['APA', 'Trend', 'Report', 'Oxu.az']

# Teq sözləri
TAG_KEYWORDS = {
    'ölkələr': ['ABŞ', 'Rusiya', 'Çin', 'Türkiyə', 'İran', 'Azərbaycan', 'Ukrayna', 'Almaniya', 'Fransa', 'Britaniya'],
    'şəxslər': ['Putin', 'Biden', 'Erdoğan', 'Zelenski', 'Trump', 'Prezident', 'Nazir'],
    'mövzular': ['İqtisadiyyat', 'Siyasət', 'Elm', 'Texnologiya', 'İdman', 'Maliyyə', 'Enerji', 'Neft', 'Qaz'],
    'hadisələr': ['Sanksiya', 'Müharibə', 'Sammit', 'Görüş', 'Danışıq', 'Razılaşma', 'Qərar']
}

def clean_html(text):
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_numbers(text):
    text = re.sub(r'(\$\d+[\d\.,]*\s*(milyard|million|bn|mn)?)', r'💰 \1', text)
    text = re.sub(r'(\d+[\d\.,]*%)', r'📊 \1', text)
    text = re.sub(r'(\d+\+)', r'📈 \1', text)
    return text

def generate_tags(title, content):
    tags = ['xəbər']
    combined = (title + ' ' + content).lower()
    
    for country in TAG_KEYWORDS['ölkələr']:
        if country.lower() in combined:
            tags.append(country)
    
    for person in TAG_KEYWORDS['şəxslər']:
        if person.lower() in combined:
            tags.append(person)
    
    for topic in TAG_KEYWORDS['mövzular']:
        if topic.lower() in combined:
            tags.append(topic)
    
    for event in TAG_KEYWORDS['hadisələr']:
        if event.lower() in combined:
            tags.append(event)
    
    tags = list(set(tags))[:12]
    return ' '.join([f'#{t.replace(" ", "")}' for t in tags])

def make_title(title):
    t = title.lower()
    if any(w in t for w in ['breaking', 'urgent', 'təcili', 'son dəqiqə']):
        return f"🔴 SON DƏQİQƏ: {title}"
    elif any(w in t for w in ['shock', 'şok', 'sensasiya', 'ilk dəfə']):
        return f"⚡ ŞOK: {title}"
    elif any(w in t for w in ['prezident', 'president', 'lider']):
        return f"🏛 TƏCİLİ: {title}"
    elif any(w in t for w in ['rekord', 'record', 'tarixi']):
        return f"📈 REKORD: {title}"
    else:
        return f"📰 {title}"

def add_timestamp():
    now = datetime.now()
    return f"⏱ {now.strftime('%H:%M')} | {now.strftime('%d %B')}"

def get_news(url):
    try:
        f = feedparser.parse(url)
        if f.entries:
            e = f.entries[0]
            
            title = e.title
            content = ''
            if hasattr(e, 'summary'):
                content = clean_html(e.summary)[:400]
            elif hasattr(e, 'description'):
                content = clean_html(e.description)[:400]
            
            media_url = None
            media_type = None
            
            if hasattr(e, 'enclosures') and e.enclosures:
                enc = e.enclosures[0]
                if hasattr(enc, 'type'):
                    if 'video' in enc.type:
                        media_url = enc.href
                        media_type = 'video'
                    elif 'image' in enc.type:
                        media_url = enc.href
                        media_type = 'image'
            
            if not media_url and hasattr(e, 'media_content'):
                for m in e.media_content:
                    if 'url' in m:
                        media_url = m['url']
                        media_type = 'image'
                        break
            
            if not media_url and hasattr(e, 'media_thumbnail'):
                if e.media_thumbnail and len(e.media_thumbnail) > 0:
                    media_url = e.media_thumbnail[0].get('url')
                    media_type = 'image'
            
            return {
                'title': title,
                'content': content,
                'link': e.link,
                'source': f.feed.title if hasattr(f.feed, 'title') else 'Mənbə',
                'media_url': media_url,
                'media_type': media_type
            }
    except:
        pass
    return None

def tr(text):
    try:
        return GoogleTranslator(source='auto', target='az').translate(text)
    except:
        return text

async def post(c):
    print(f"\n🔄 [{datetime.now().strftime('%H:%M')}] Xəbərlər toplanır...")
    
    all_news = []
    for i, (name, url) in enumerate(NEWS.items(), 1):
        print(f"   [{i}/18] {name}...", end=' ')
        x = get_news(url)
        if x:
            need_tr = name not in AZ_SOURCES
            title = tr(x['title']) if need_tr else x['title']
            content = tr(x['content']) if need_tr and x['content'] else x['content']
            
            content = extract_numbers(content)
            title = make_title(title)
            tags = generate_tags(title, content)
            
            all_news.append({
                'name': name,
                'title': title,
                'content': content,
                'link': x['link'],
                'media_url': x['media_url'],
                'media_type': x['media_type'],
                'tags': tags
            })
            print(f"✅")
        else:
            print(f"❌")
    
    print(f"\n📢 Kanala paylaşılır...")
    for i, news in enumerate(all_news):
        try:
            text = f"{news['title']}\n\n"
            text += f"{add_timestamp()}\n\n"
            
            if news['content']:
                text += f"{news['content']}\n\n"
            
            text += f"📰 {news['name']} | Oxu: {news['link']}\n\n"
            text += news['tags']
            
            if news['media_url'] and news['media_type'] == 'video':
                await c.send_file(KANAL, news['media_url'], caption=text)
            elif news['media_url'] and news['media_type'] == 'image':
                await c.send_file(KANAL, news['media_url'], caption=text)
            else:
                await c.send_message(KANAL, text)
            
            print(f"   ✅ [{i+1}/{len(all_news)}] {news['name']}")
            
            if (i + 1) % 3 == 0 and i + 1 < len(all_news):
                await asyncio.sleep(150)
            else:
                await asyncio.sleep(10)
        except Exception as e:
            print(f"   ❌ [{i+1}/{len(all_news)}] Xəta: {e}")
    
    print(f"✅ Dövrü tamamlandı: {len(all_news)} xəbər\n")

async def main():
    print("=" * 50)
    print("🤖 XƏBƏR DÜNYASI BOT - VERSİYA 4.0 PROFESSIONAL")
    print("=" * 50)
    print(f"✅ Bot işə düşdü!")
    print(f"📢 Kanal: {KANAL}")
    print(f"🌍 Mənbə: 18 keyfiyyətli")
    print(f"⏰ Yenilənmə: Hər 6 dəqiqə")
    print(f"📸 Media: RSS-dən (varsa)")
    print(f"🏷 Teqlər: 8-12 avtomatik")
    print(f"📊 Rəqəmlər: avtomatik vurğu")
    print("=" * 50 + "\n")
    
    c = TelegramClient('bot', API_ID, API_HASH)
    await c.start(bot_token=BOT_TOKEN)
    
    while True:
        await post(c)
        print(f"⏰ 6 dəqiqə gözləyir...")
        await asyncio.sleep(360)

if __name__ == '__main__':
    asyncio.run(main())
