#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, asyncio, re, sqlite3, random
from datetime import datetime
import feedparser
from telethon import TelegramClient
from telethon.sessions import MemorySession
from deep_translator import GoogleTranslator

# ========== ENVIRONMENT ==========
API_ID = int(os.getenv('API_ID', '39717958'))
API_HASH = os.getenv('API_HASH', 'e8e1f10ee0080cc64f3d8027a1de2088')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
KANAL = os.getenv('KANAL', '@xeberdunyasiaz')

# ========== DATABASE ==========
DB_FILE = 'news.db'

def init_db():
    """Database başlat"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posted_links
                 (link TEXT PRIMARY KEY, posted_at TIMESTAMP, type TEXT)''')
    conn.commit()
    conn.close()

def is_posted(link):
    """Əvvəl paylaşılıbmı?"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT link FROM posted_links WHERE link=?', (link,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_posted(link, content_type='news'):
    """Paylaşılıb qeyd et"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO posted_links VALUES (?, ?, ?)', 
                  (link, datetime.now(), content_type))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

# ========== XƏBƏR MƏNBƏLƏR ==========
NEWS = {
    # Azərbaycan (6)
    'APA': 'https://apa.az/rss/az/news',
    'Trend': 'https://az.trend.az/rss/',
    'Report': 'https://report.az/rss/',
    'Oxu.az': 'https://oxu.az/rss/news',
    'Azadliq': 'https://www.azadliq.org/api/zorrepgviq',
    'Milli.az': 'https://milli.az/rss',
    
    # Türkiyə Dünya (8)
    'Anadolu': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
    'TRT Dünya': 'https://www.trthaber.com/dunya.rss',
    'Hürriyet': 'https://www.hurriyet.com.tr/rss/dunya',
    'NTV': 'https://www.ntv.com.tr/dunya.rss',
    'Sabah': 'https://www.sabah.com.tr/rss/dunya.xml',
    'Sözcü': 'https://www.sozcu.com.tr/kategori/dunya/feed/',
    'Habertürk': 'https://www.haberturk.com/rss/kategori/dunya.xml',
    'CNN Türk': 'https://www.cnnturk.com/feed/rss/dunya/news',
    
    # Beynəlxalq (10)
    'Reuters': 'http://feeds.reuters.com/reuters/topNews',
    'BBC': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'DW': 'https://rss.dw.com/rdf/rss-en-all',
    'CNN': 'http://rss.cnn.com/rss/edition_world.rss',
    'AP News': 'https://rsshub.app/apnews/topics/apf-topnews',
    'The Guardian': 'https://www.theguardian.com/world/rss',
    'France24': 'https://www.france24.com/en/rss',
    'Euro News': 'https://www.euronews.com/rss',
    'Sky News': 'https://feeds.skynews.com/feeds/rss/world.xml',
    
    # Elm & Tech (7)
    'ScienceDaily': 'https://www.sciencedaily.com/rss/top.xml',
    'BBC Science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    'PopSci': 'https://www.popsci.com/feed/',
    'TechCrunch': 'https://techcrunch.com/feed/',
    'Wired': 'https://www.wired.com/feed/rss',
    'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    
    # İqtisad (4)
    'Bloomberg': 'https://www.bloomberg.com/feed/podcast/etf-iq.xml',
    'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    'MarketWatch': 'https://www.marketwatch.com/rss/topstories',
    'Financial Post': 'https://financialpost.com/feed/',
}

# ========== ƏYLƏNCƏ MƏNBƏLƏR (Reddit) ==========
FUN = {
    'r/funny': 'https://www.reddit.com/r/funny/.rss',
    'r/memes': 'https://www.reddit.com/r/memes/.rss',
    'r/wholesomememes': 'https://www.reddit.com/r/wholesomememes/.rss',
    'r/Unexpected': 'https://www.reddit.com/r/Unexpected/.rss',
    'r/AnimalsBeingDerps': 'https://www.reddit.com/r/AnimalsBeingDerps/.rss',
    'r/aww': 'https://www.reddit.com/r/aww/.rss',
    'r/ContagiousLaughter': 'https://www.reddit.com/r/ContagiousLaughter/.rss',
}

AZ_SOURCES = ['APA', 'Trend', 'Report', 'Oxu.az', 'Azadliq', 'Milli.az']

# ========== FUNKSIYALAR ==========
def clean_html(text):
    """HTML təmizlə"""
    if not text: return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_numbers(text):
    """Rəqəmləri vurğula"""
    if not text: return text
    text = re.sub(r'(\d+[\d\.,]*\s*%)', r'📊 \1', text)
    text = re.sub(r'([$€£¥₺]\s*[\d\.,]+[BMK]?)', r'💰 \1', text)
    return text

def generate_tags(title, content, source):
    """Avtomatik teqlər"""
    text = f"{title} {content}".lower()
    tags = set()
    
    countries = {
        'azərbaycan': '#Azərbaycan', 'türkiyə': '#Türkiyə', 'rusiya': '#Rusiya',
        'amerika': '#ABŞ', 'çin': '#Çin', 'almaniya': '#Almaniya',
        'fransa': '#Fransa', 'ingiltərə': '#İngiltərə', 'iran': '#İran',
        'russia': '#Rusiya', 'turkey': '#Türkiyə', 'usa': '#ABŞ', 'china': '#Çin',
    }
    
    topics = {
        'iqtisad': '#İqtisadiyyat', 'siyasət': '#Siyasət', 'texnologiya': '#Texnologiya',
        'elm': '#Elm', 'səhiyyə': '#Səhiyyə', 'enerji': '#Enerji', 'neft': '#Neft',
        'economy': '#İqtisadiyyat', 'politics': '#Siyasət', 'technology': '#Texnologiya',
        'science': '#Elm', 'health': '#Səhiyyə', 'energy': '#Enerji', 'oil': '#Neft',
    }
    
    all_kw = {**countries, **topics}
    
    for word, tag in all_kw.items():
        if word in text:
            tags.add(tag)
    
    tags.add('#xəbər')
    tags = list(tags)[:12]
    return ' '.join(sorted(tags))

def make_title(title):
    """Başlığı aktiv et"""
    if not title: return "🔴 XƏBƏR"
    
    keywords = ['son dəqiqə', 'təcili', 'breaking', 'urgent']
    title_lower = title.lower()
    
    for kw in keywords:
        if kw in title_lower:
            return f"🔴 SON DƏQİQƏ: {title}"
    
    return f"🔴 SON DƏQİQƏ: {title}"

def get_news(url, source):
    """RSS-dən xəbər götür"""
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return None
        
        entry = feed.entries[0]
        title = clean_html(entry.get('title', ''))
        link = entry.get('link', '')
        
        if not title or not link:
            return None
        
        content = ''
        if 'summary' in entry:
            content = clean_html(entry.summary)
        elif 'description' in entry:
            content = clean_html(entry.description)
        
        if len(content) > 400:
            content = content[:397] + '...'
        
        media_url = None
        media_type = None
        
        if 'media_content' in entry:
            media = entry.media_content[0]
            media_url = media.get('url')
            media_type = 'video' if 'video' in media.get('type', '') else 'image'
        elif 'enclosures' in entry and entry.enclosures:
            enc = entry.enclosures[0]
            media_url = enc.get('href')
            media_type = 'video' if 'video' in enc.get('type', '') else 'image'
        elif 'media_thumbnail' in entry:
            media_url = entry.media_thumbnail[0].get('url')
            media_type = 'image'
        
        return {
            'title': title,
            'content': content,
            'link': link,
            'source': source,
            'media_url': media_url,
            'media_type': media_type
        }
    except Exception as e:
        print(f"❌ {source}: {str(e)}")
        return None

def extract_reddit_media(content_html):
    """Reddit post-dan media URL çıxar (təkmilləşdirilmiş)"""
    if not content_html:
        return None, None
    
    # 1) Preview image (ən çox rast gəlinən)
    match = re.search(r'https://preview\.redd\.it/[^\s"<>]+\.(?:jpg|png|gif|jpeg)', content_html)
    if match:
        return match.group(0), 'image'
    
    # 2) i.redd.it (direct image)
    match = re.search(r'https://i\.redd\.it/[^\s"<>]+\.(?:jpg|png|gif|jpeg)', content_html)
    if match:
        return match.group(0), 'image'
    
    # 3) v.redd.it (video) - Telethon bunu dəstəkləmir, amma link qalsın
    match = re.search(r'https://v\.redd\.it/[^\s"<>]+', content_html)
    if match:
        return match.group(0), 'video'
    
    # 4) External image (imgur.com və s.)
    match = re.search(r'https://i\.imgur\.com/[^\s"<>]+\.(?:jpg|png|gif|jpeg)', content_html)
    if match:
        return match.group(0), 'image'
    
    # 5) Thumbnail (son çarə)
    match = re.search(r'<img[^>]+src="([^"]+)"', content_html)
    if match:
        url = match.group(1)
        # HTML entities decode
        url = url.replace('&amp;', '&')
        if url.startswith('http'):
            return url, 'image'
    
    return None, None

def get_fun_content(url, source):
    """Reddit-dən əyləncəli məzmun götür (təkmilləşdirilmiş)"""
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return None
        
        # İlk 20 post-dan media olan birini tap
        attempts = 0
        max_attempts = 20
        
        while attempts < max_attempts:
            # Random post seç
            entry = random.choice(feed.entries[:20])
            
            title = clean_html(entry.get('title', ''))
            link = entry.get('link', '')
            
            if not title or not link:
                attempts += 1
                continue
            
            # Artıq göndərilmişmi?
            if is_posted(link):
                attempts += 1
                continue
            
            # Media tap
            content_html = entry.get('content', [{}])[0].get('value', '')
            media_url, media_type = extract_reddit_media(content_html)
            
            # Media varsa qaytar
            if media_url:
                return {
                    'title': title,
                    'link': link,
                    'source': source,
                    'media_url': media_url,
                    'media_type': media_type
                }
            
            attempts += 1
        
        # 20 cəhddən sonra heç nə tapılmadı
        return None
        
    except Exception as e:
        print(f"❌ {source}: {str(e)}")
        return None

def tr(text):
    """Azərbaycanca tərcümə"""
    try:
        return GoogleTranslator(source='auto', target='az').translate(text)
    except:
        return text

def generate_funny_caption(title):
    """Gülməli açıqlama yarat"""
    captions = [
        f"😂 GÜLMƏYƏ HAZIRSAN?\n\n{title}\n\nBunu görəndə gülməyə bilməzsən! 🤣",
        f"🤣 BU NƏDİR YA?\n\n{title}\n\nGünün ən gülməli anı! 😄",
        f"😄 ÇOX MARAQLI!\n\n{title}\n\nDostlarına göndər, onlar da gülsün! 🎉",
        f"🎭 ƏYLƏNCƏLİ!\n\n{title}\n\nBir az gülmək heç kəsə zərər verməz! 😊",
        f"🌟 GÖRMƏLİSƏN!\n\n{title}\n\nBu həqiqətən gülməlidir! 🤪",
        f"💯 ƏFSANƏ!\n\n{title}\n\nİnternetin ən gülməli məzmunu! 😹",
        f"🔥 TOP!\n\n{title}\n\nBunu qaçırma, çox gülməlidir! 😂",
    ]
    return random.choice(captions)

async def post_news(client):
    """30 xəbər paylaş"""
    posted = 0
    
    for source, url in NEWS.items():
        if posted >= 30:
            break
        
        try:
            news = get_news(url, source)
            
            if not news or is_posted(news['link']):
                continue
            
            # Tərcümə
            if source not in AZ_SOURCES:
                news['title'] = tr(news['title'])
                if news['content']:
                    news['content'] = tr(news['content'])
            
            title = make_title(news['title'])
            content = extract_numbers(news['content']) if news['content'] else ''
            tags = generate_tags(news['title'], content, source)
            
            msg = f"{title}\n\n"
            if content:
                msg += f"{content}\n\n"
            msg += f"📰 {source} | Oxu: {news['link']}\n\n{tags}"
            
            try:
                if news['media_url']:
                    await client.send_file(KANAL, news['media_url'], caption=msg)
                else:
                    await client.send_message(KANAL, msg)
                
                mark_posted(news['link'], 'news')
                posted += 1
                print(f"✅ [{posted}/30] {source}: Göndərildi")
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"❌ {source} göndərmə xəta: {str(e)}")
        
        except Exception as e:
            print(f"❌ {source}: {str(e)}")
    
    return posted

async def post_fun(client):
    """1 əyləncəli məzmun paylaş (media olan)"""
    
    # Bütün mənbələri qarışdır
    sources = list(FUN.items())
    random.shuffle(sources)
    
    for source, url in sources:
        try:
            fun = get_fun_content(url, source)
            
            # Media yoxdursa növbəti mənbəyə keç
            if not fun or not fun['media_url']:
                print(f"⚠️  {source}: Media tapılmadı, skip")
                continue
            
            # Tərcümə
            title_az = tr(fun['title'])
            
            # Gülməli açıqlama
            caption = generate_funny_caption(title_az)
            caption += f"\n\n📱 Mənbə: {source}\n\n#əyləncə #gülməli #meme"
            
            try:
                # v.redd.it video işləməyə bilər, amma cəhd edək
                await client.send_file(KANAL, fun['media_url'], caption=caption)
                
                mark_posted(fun['link'], 'fun')
                print(f"😂 Əyləncə göndərildi: {source}")
                return True
                
            except Exception as e:
                print(f"❌ {source} göndərmə xəta: {str(e)}")
                # Media göndərilməsə növbəti mənbəyə keç
                continue
        
        except Exception as e:
            print(f"❌ {source}: {str(e)}")
    
    print("⚠️  Heç bir əyləncəli məzmun göndərilə bilmədi")
    return False

async def main():
    """Əsas funksiya"""
    print("\n" + "="*60)
    print("🤖 XƏBƏR DÜNYASI BOT - VERSİYA 4.1 ULTRA")
    print("="*60)
    print("✅ Xəbər + Əyləncə hibrid kanal!")
    print(f"📢 Kanal: {KANAL}")
    print(f"📰 Xəbər mənbə: {len(NEWS)} keyfiyyətli")
    print(f"😂 Əyləncə mənbə: {len(FUN)} subreddit")
    print("🔄 Format: 30 xəbər → 1 əyləncə → 6 dəqiqə")
    print("🎯 Əyləncə: Yalnız media olan (şəkil/video)")
    print("🔒 Təkrar yoxlama: aktiv")
    print("="*60 + "\n")
    
    init_db()
    
    async with TelegramClient(MemorySession(), API_ID, API_HASH) as c:
        await c.start(bot_token=BOT_TOKEN)
        
        while True:
            print(f"\n{'='*60}")
            print(f"🔄 YENİ DÖVR: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            
            # 30 xəbər
            posted = await post_news(c)
            print(f"\n📊 {posted} xəbər göndərildi\n")
            
            # 1 əyləncə (media olan)
            await post_fun(c)
            
            print(f"\n{'='*60}")
            print("⏸ 6 dəqiqə fasilə...")
            print(f"{'='*60}\n")
            
            await asyncio.sleep(360)

if __name__ == '__main__':
    asyncio.run(main())
