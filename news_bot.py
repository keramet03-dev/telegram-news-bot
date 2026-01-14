import asyncio
import feedparser
from telethon import TelegramClient
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator
from datetime import datetime
import os
import sys
import signal
import logging

# Logging konfiqurasiyası
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Environment variables (HEÇ BİR default dəyər - güvənlik üçün)
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
KANAL = os.getenv('KANAL')
SESSION_STRING = os.getenv('SESSION_STRING', '')  # Serverlər üçün optional

# Konfiqurasiya yoxlaması
def check_config():
    """Environment variables mövcudluğunu yoxlayır"""
    missing = []
    if not API_ID:
        missing.append('API_ID')
    if not API_HASH:
        missing.append('API_HASH')
    if not BOT_TOKEN:
        missing.append('BOT_TOKEN')
    if not KANAL:
        missing.append('KANAL')
    
    if missing:
        logger.error(f"❌ Aşağıdakı environment variables təyin edilməyib: {', '.join(missing)}")
        logger.error("💡 Bu dəyişənləri .env faylında və ya sistemdə təyin edin.")
        sys.exit(1)
    
    # API_ID integer olmalıdır
    try:
        int(API_ID)
    except ValueError:
        logger.error("❌ API_ID rəqəm olmalıdır!")
        sys.exit(1)

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

# Graceful shutdown üçün qlobal dəyişən
shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    """Signal handler - təmiz bağlanma"""
    logger.info("⚠️ Bağlanma siqnalı alındı. Bot təmiz şəkildə bağlanır...")
    shutdown_event.set()

def get_news(url, source_name):
    """RSS feed-dən son xəbəri alır"""
    try:
        f = feedparser.parse(url)
        if f.bozo and f.bozo_exception:
            logger.warning(f"⚠️ {source_name} RSS xətası: {f.bozo_exception}")
            return None
        if f.entries:
            e = f.entries[0]
            return {
                'title': e.get('title', 'Başlıq yoxdur'),
                'link': e.get('link', ''),
                'source': f.feed.get('title', source_name)
            }
        else:
            logger.debug(f"ℹ️ {source_name} - xəbər tapılmadı")
    except Exception as e:
        logger.error(f"❌ {source_name} xətası: {type(e).__name__}: {e}")
    return None

def translate_text(text):
    """Mətni Azərbaycan dilinə tərcümə edir"""
    if not text or len(text.strip()) == 0:
        return text
    try:
        # Maksimum 400 simvol
        truncated = text[:400] if len(text) > 400 else text
        result = GoogleTranslator(source='auto', target='az').translate(truncated)
        return result if result else text
    except Exception as e:
        logger.warning(f"⚠️ Tərcümə xətası: {e}")
        return text

def improve_title(title):
    """Başlığa uyğun emoji əlavə edir"""
    if not title:
        return "📰 Xəbər"
    
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['təcili', 'son dəqiqə', 'breaking', 'urgent', 'flash']):
        return f"⚡ {title}"
    elif any(word in title_lower for word in ['prezident', 'president', 'hökumət', 'government', 'nazir', 'minister']):
        return f"🏛 {title}"
    elif any(word in title_lower for word in ['iqtisad', 'economy', 'maliyyə', 'finance', 'dollar', 'manat', 'neft', 'oil']):
        return f"💰 {title}"
    elif any(word in title_lower for word in ['elm', 'science', 'texnologiya', 'technology', 'süni intellekt', 'ai']):
        return f"🔬 {title}"
    elif any(word in title_lower for word in ['idman', 'sport', 'futbol', 'football', 'olimpiya']):
        return f"⚽ {title}"
    elif any(word in title_lower for word in ['müharibə', 'war', 'hücum', 'attack', 'ordu', 'army']):
        return f"⚔️ {title}"
    elif any(word in title_lower for word in ['hava', 'weather', 'yağış', 'rain', 'fəlakət', 'disaster']):
        return f"🌦️ {title}"
    else:
        return f"📰 {title}"

async def post(client):
    """Bütün xəbərləri toplayır və paylaşır"""
    logger.info(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Xəbərlər toplanır...")
    
    all_news = []
    failed_sources = []
    
    for name, url in NEWS.items():
        if shutdown_event.is_set():
            logger.info("⚠️ Bağlanma - xəbər toplama dayandırıldı")
            return
            
        news_item = get_news(url, name)
        if news_item:
            # Azərbaycan mənbələri tərcümə olunmur
            need_translation = name not in ['APA', 'Trend', 'Report', 'Oxu.az']
            title = translate_text(news_item['title']) if need_translation else news_item['title']
            title = improve_title(title)
            
            message = f"{title}\n\n📰 {name}\n🔗 [Oxu]({news_item['link']})\n\n#xəbər"
            all_news.append({'name': name, 'msg': message})
        else:
            failed_sources.append(name)
    
    if failed_sources:
        logger.warning(f"⚠️ İşləməyən mənbələr: {', '.join(failed_sources)}")
    
    if not all_news:
        logger.error("❌ Heç bir xəbər tapılmadı!")
        return
    
    # Smart paylaşım: 3-1-3-1 pattern
    count = 0
    for i, news in enumerate(all_news):
        if shutdown_event.is_set():
            logger.info("⚠️ Bağlanma - paylaşım dayandırıldı")
            break
            
        try:
            await client.send_message(KANAL, news['msg'], link_preview=False)
            logger.info(f"✅ [{i+1}/{len(all_news)}] {news['name']}")
            count += 1
            
            # Spam qorunması: hər 3 xəbərdən sonra 2.5 dəqiqə gözlə
            if (i + 1) % 3 == 0 and (i + 1) < len(all_news):
                logger.info("⏸ 2.5 dəqiqə ara...")
                await asyncio.sleep(150)
            else:
                await asyncio.sleep(10)
                
        except Exception as e:
            error_msg = str(e)
            if 'FloodWait' in error_msg:
                # FloodWait xətası - Telegram limiti
                wait_time = int(''.join(filter(str.isdigit, error_msg)) or '60')
                logger.warning(f"⏳ FloodWait - {wait_time} saniyə gözlənilir...")
                await asyncio.sleep(wait_time)
            elif 'ChatWriteForbidden' in error_msg:
                logger.error(f"❌ Bot kanala yaza bilmir! Botu admin edin: {KANAL}")
                break
            else:
                logger.error(f"❌ {news['name']}: {e}")
    
    logger.info(f"✅ Cəmi {count}/{len(all_news)} xəbər paylaşıldı!")

async def main():
    """Əsas bot döngüsü"""
    # Konfiqurasiya yoxlaması
    check_config()
    
    logger.info("🤖 XƏBƏR DÜNYASI BOT - VERSİYA 2.1 (Server Edition)")
    logger.info("=" * 50)
    
    # Signal handlers (graceful shutdown)
    try:
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
    except Exception:
        pass  # Windows-da bəzi siqnallar işləmir
    
    # Client yaratma - SESSION_STRING varsa onu istifadə et (serverlər üçün)
    if SESSION_STRING:
        logger.info("📱 Session string ilə qoşulur...")
        client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
    else:
        logger.info("📱 Fayl session ilə qoşulur...")
        client = TelegramClient('bot', int(API_ID), API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        logger.info(f"✅ Bot işə düşdü!")
        logger.info(f"📢 Kanal: {KANAL}")
        logger.info(f"🌍 Mənbə: {len(NEWS)} keyfiyyətli")
        logger.info(f"⏰ Smart paylaşım aktiv")
        logger.info(f"🔄 Hər 3 saatda yenilənir")
        logger.info("")
        
        # Əsas döngü
        while not shutdown_event.is_set():
            await post(client)
            
            if shutdown_event.is_set():
                break
                
            logger.info("⏰ 3 saat gözləyir...")
            
            # 3 saat gözləmə (shutdown yoxlaması ilə)
            for _ in range(1080):  # 1080 * 10 saniyə = 3 saat
                if shutdown_event.is_set():
                    break
                await asyncio.sleep(10)
                
    except Exception as e:
        logger.error(f"❌ Bot xətası: {e}")
    finally:
        logger.info("🔌 Bot bağlanır...")
        await client.disconnect()
        logger.info("👋 Bot təmiz şəkildə bağlandı!")

if __name__ == '__main__':
    asyncio.run(main())
