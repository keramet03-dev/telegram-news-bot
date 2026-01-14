#!/bin/bash

#############################################
#  XƏBƏR DÜNYASI BOT - UBUNTU SETUP SCRİPT  #
#  Avtomatik quraşdırma və işlətmə          #
#############################################

set -e  # Xəta olduqda dayandır

# Rənglər
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        🤖 XƏBƏR DÜNYASI BOT - UBUNTU SETUP                ║"
echo "║              Avtomatik Quraşdırma Skripti                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ═══════════════════════════════════════════════════════════════
# KONFİQURASİYA - SİZİN CREDENTİALLARINIZ
# ═══════════════════════════════════════════════════════════════
BOT_TOKEN="8531294221:AAEiIfFs0Kf9fizcSjJfMcyoXvongxGaqko"
API_ID="39717958"
API_HASH="e8e1f10ee0080cc64f3d8027a1de2088"
KANAL="@xeberdunyasiaz"

# Quraşdırma parametrləri
BOT_DIR="/opt/xeber-bot"
SERVICE_NAME="xeber-bot"
PYTHON_VERSION="python3"

# ═══════════════════════════════════════════════════════════════
# FUNKSIYALAR
# ═══════════════════════════════════════════════════════════════

print_step() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✖ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✔ $1${NC}"
}

# ═══════════════════════════════════════════════════════════════
# ROOT YOXLAMASI
# ═══════════════════════════════════════════════════════════════
if [[ $EUID -ne 0 ]]; then
   print_error "Bu skript root icazəsi ilə işlədilməlidir!"
   echo "İşlətmək üçün: sudo bash setup.sh"
   exit 1
fi

# ═══════════════════════════════════════════════════════════════
# ADDIM 1: SİSTEM YENİLƏMƏSİ VƏ PAKETLƏR
# ═══════════════════════════════════════════════════════════════
print_step "Addım 1/7: Sistem yenilənir və paketlər quraşdırılır..."

apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl > /dev/null 2>&1

# Git konfiqurasiyası
git config --global user.name "keramet03-dev"
git config --global user.email "keramet03@gmail.com"

print_success "Sistem paketləri quraşdırıldı"
print_success "Git konfiqurasiya edildi: keramet03-dev <keramet03@gmail.com>"

# ═══════════════════════════════════════════════════════════════
# ADDIM 2: BOT DİREKTORİYASI
# ═══════════════════════════════════════════════════════════════
print_step "Addım 2/7: Bot direktoriyası yaradılır..."

# Əgər köhnə quraşdırma varsa, dayandır
if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    systemctl stop $SERVICE_NAME
fi

# Direktoriya yaratma
mkdir -p $BOT_DIR
cd $BOT_DIR

print_success "Direktoriya yaradıldı: $BOT_DIR"

# ═══════════════════════════════════════════════════════════════
# ADDIM 3: VIRTUAL ENVIRONMENT
# ═══════════════════════════════════════════════════════════════
print_step "Addım 3/7: Python virtual environment yaradılır..."

# Köhnə venv varsa sil
if [ -d "venv" ]; then
    rm -rf venv
fi

$PYTHON_VERSION -m venv venv
source venv/bin/activate

print_success "Virtual environment yaradıldı"

# ═══════════════════════════════════════════════════════════════
# ADDIM 4: REQUIREMENTS.TXT VƏ BOT KODU
# ═══════════════════════════════════════════════════════════════
print_step "Addım 4/7: Bot faylları yaradılır..."

# requirements.txt
cat > requirements.txt << 'EOF'
telethon
feedparser
deep-translator
EOF

# news_bot.py
cat > news_bot.py << 'PYTHONEOF'
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

# Environment variables
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
KANAL = os.getenv('KANAL')
SESSION_STRING = os.getenv('SESSION_STRING', '')

# Konfiqurasiya yoxlaması
def check_config():
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
        sys.exit(1)
    
    try:
        int(API_ID)
    except ValueError:
        logger.error("❌ API_ID rəqəm olmalıdır!")
        sys.exit(1)

# 18 keyfiyyətli mənbə
NEWS = {
    'APA': 'https://apa.az/rss/az/news',
    'Trend': 'https://az.trend.az/rss/',
    'Report': 'https://report.az/rss/',
    'Oxu.az': 'https://oxu.az/rss/news',
    'Anadolu Dünya': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
    'TRT Dünya': 'https://www.trthaber.com/dunya.rss',
    'Hürriyet Dünya': 'https://www.hurriyet.com.tr/rss/dunya',
    'NTV Dünya': 'https://www.ntv.com.tr/dunya.rss',
    'Reuters': 'http://feeds.reuters.com/reuters/topNews',
    'BBC': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'DW': 'https://rss.dw.com/rdf/rss-en-all',
    'CNN': 'http://rss.cnn.com/rss/edition_world.rss',
    'Evrim Ağacı': 'https://evrimagaci.org/rss',
    'Nat Geo': 'https://www.nationalgeographic.com/pages/topic/latest-stories/_jcr_content.feed',
    'ScienceDaily': 'https://www.sciencedaily.com/rss/top.xml',
    'BBC Science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    'PopSci': 'https://www.popsci.com/feed/',
}

shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    logger.info("⚠️ Bağlanma siqnalı alındı...")
    shutdown_event.set()

def get_news(url, source_name):
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
    except Exception as e:
        logger.error(f"❌ {source_name} xətası: {type(e).__name__}: {e}")
    return None

def translate_text(text):
    if not text or len(text.strip()) == 0:
        return text
    try:
        truncated = text[:400] if len(text) > 400 else text
        result = GoogleTranslator(source='auto', target='az').translate(truncated)
        return result if result else text
    except Exception as e:
        logger.warning(f"⚠️ Tərcümə xətası: {e}")
        return text

def improve_title(title):
    if not title:
        return "📰 Xəbər"
    
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['təcili', 'son dəqiqə', 'breaking', 'urgent']):
        return f"⚡ {title}"
    elif any(word in title_lower for word in ['prezident', 'president', 'hökumət', 'government']):
        return f"🏛 {title}"
    elif any(word in title_lower for word in ['iqtisad', 'economy', 'maliyyə', 'finance', 'dollar']):
        return f"💰 {title}"
    elif any(word in title_lower for word in ['elm', 'science', 'texnologiya', 'technology']):
        return f"🔬 {title}"
    elif any(word in title_lower for word in ['idman', 'sport', 'futbol']):
        return f"⚽ {title}"
    else:
        return f"📰 {title}"

async def post(client):
    logger.info(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Xəbərlər toplanır...")
    
    all_news = []
    
    for name, url in NEWS.items():
        if shutdown_event.is_set():
            return
            
        news_item = get_news(url, name)
        if news_item:
            need_translation = name not in ['APA', 'Trend', 'Report', 'Oxu.az']
            title = translate_text(news_item['title']) if need_translation else news_item['title']
            title = improve_title(title)
            
            message = f"{title}\n\n📰 {name}\n🔗 [Oxu]({news_item['link']})\n\n#xəbər"
            all_news.append({'name': name, 'msg': message})
    
    if not all_news:
        logger.error("❌ Heç bir xəbər tapılmadı!")
        return
    
    count = 0
    for i, news in enumerate(all_news):
        if shutdown_event.is_set():
            break
            
        try:
            await client.send_message(KANAL, news['msg'], link_preview=False)
            logger.info(f"✅ [{i+1}/{len(all_news)}] {news['name']}")
            count += 1
            
            if (i + 1) % 3 == 0 and (i + 1) < len(all_news):
                logger.info("⏸ 2.5 dəqiqə ara...")
                await asyncio.sleep(150)
            else:
                await asyncio.sleep(10)
                
        except Exception as e:
            error_msg = str(e)
            if 'FloodWait' in error_msg:
                wait_time = int(''.join(filter(str.isdigit, error_msg)) or '60')
                logger.warning(f"⏳ FloodWait - {wait_time} saniyə gözlənilir...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ {news['name']}: {e}")
    
    logger.info(f"✅ Cəmi {count}/{len(all_news)} xəbər paylaşıldı!")

async def main():
    check_config()
    
    logger.info("🤖 XƏBƏR DÜNYASI BOT - VERSİYA 2.1")
    logger.info("=" * 50)
    
    try:
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
    except Exception:
        pass
    
    if SESSION_STRING:
        client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
    else:
        client = TelegramClient('bot', int(API_ID), API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        logger.info(f"✅ Bot işə düşdü!")
        logger.info(f"📢 Kanal: {KANAL}")
        logger.info(f"🌍 Mənbə: {len(NEWS)} keyfiyyətli")
        logger.info(f"🔄 Hər 3 saatda yenilənir")
        
        while not shutdown_event.is_set():
            await post(client)
            
            if shutdown_event.is_set():
                break
                
            logger.info("⏰ 3 saat gözləyir...")
            
            for _ in range(1080):
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
PYTHONEOF

print_success "Bot faylları yaradıldı"

# ═══════════════════════════════════════════════════════════════
# ADDIM 5: PİP INSTALL
# ═══════════════════════════════════════════════════════════════
print_step "Addım 5/7: Python paketləri quraşdırılır..."

pip install --upgrade pip -q
pip install -r requirements.txt -q

print_success "Python paketləri quraşdırıldı"

# ═══════════════════════════════════════════════════════════════
# ADDIM 6: .ENV FAYLI
# ═══════════════════════════════════════════════════════════════
print_step "Addım 6/7: Environment konfiqurasiyası yaradılır..."

cat > .env << EOF
API_ID=$API_ID
API_HASH=$API_HASH
BOT_TOKEN=$BOT_TOKEN
KANAL=$KANAL
EOF

chmod 600 .env
print_success ".env faylı yaradıldı"

# ═══════════════════════════════════════════════════════════════
# ADDIM 7: SYSTEMD SERVICE
# ═══════════════════════════════════════════════════════════════
print_step "Addım 7/7: SystemD service quraşdırılır..."

cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Xeber Dunyasi Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
EnvironmentFile=$BOT_DIR/.env
ExecStart=$BOT_DIR/venv/bin/python news_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# SystemD yenilə və aktivləşdir
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

print_success "SystemD service quruldu və aktivləşdirildi"

# ═══════════════════════════════════════════════════════════════
# TAMAMLANDI
# ═══════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           ✅ QURAŞDIRMA TAMAMLANDI!                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}📍 Bot yeri:${NC} $BOT_DIR"
echo -e "${BLUE}📍 Service adı:${NC} $SERVICE_NAME"
echo ""
echo -e "${YELLOW}🔧 Faydalı əmrlər:${NC}"
echo "   ├─ Status: sudo systemctl status $SERVICE_NAME"
echo "   ├─ Loglar: sudo journalctl -u $SERVICE_NAME -f"
echo "   ├─ Dayandır: sudo systemctl stop $SERVICE_NAME"
echo "   ├─ Başlat: sudo systemctl start $SERVICE_NAME"
echo "   └─ Yenidən başlat: sudo systemctl restart $SERVICE_NAME"
echo ""

# Status göstər
echo -e "${BLUE}📊 Cari status:${NC}"
systemctl status $SERVICE_NAME --no-pager -l | head -15

echo ""
echo -e "${GREEN}🎉 Bot artıq işləyir! Logları izləmək üçün:${NC}"
echo -e "   ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
