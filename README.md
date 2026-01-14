# 🌍 Xəbər Dünyası Bot

Azərbaycan və dünya xəbərlərini avtomatik toplayan və Telegram kanalına paylaşan güclü bot.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 İçindəkilər

- [Xüsusiyyətlər](#-xüsusiyyətlər)
- [Arxitektura](#-arxitektura)
- [Quraşdırma](#-quraşdırma)
- [Konfiqurasiya](#-konfiqurasiya)
- [İstifadə](#-istifadə)
- [Deployment](#-deployment)
- [Xəbər Mənbələri](#-xəbər-mənbələri)
- [Texniki Detallar](#-texniki-detallar)
- [Problemlərin Həlli](#-problemlərin-həlli)

---

## ✨ Xüsusiyyətlər

### 🔄 Avtomatik Xəbər Toplayıcı
- **18 premium mənbədən** xəbər toplayır
- Hər **3 saatda** yeni xəbərləri yoxlayır
- RSS/Atom feed-ləri parsing edir

### 🌐 Çoxdilli Dəstək
- Azərbaycan, Türk, İngilis mənbələri
- **Avtomatik tərcümə** - xarici xəbərlər Azərbaycan dilinə çevrilir
- Google Translate API istifadə edir

### 📱 Smart Paylaşım
- **3-1-3-1 pattern** - spam filtrindən qorunmaq üçün
- Hər 3 xəbərdən sonra 2.5 dəqiqə fasilə
- Xəbərlər arasında 10 saniyə gözləmə

### 🏷️ Kateqoriya Emociyaları
| Kateqoriya | Emoji | Açar sözlər |
|------------|-------|-------------|
| Təcili | ⚡ | təcili, son dəqiqə, breaking |
| Siyasət | 🏛 | prezident, hökumət, government |
| İqtisadiyyat | 💰 | iqtisad, maliyyə, dollar |
| Elm/Texnologiya | 🔬 | elm, science, texnologiya |
| İdman | ⚽ | idman, sport, futbol |
| Digər | 📰 | default |

---

## 🏗️ Arxitektura

```
┌─────────────────────────────────────────────────────────────┐
│                      XƏBƏR DÜNYASI BOT                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────┐    ┌───────────┐    ┌───────────────────┐   │
│  │ RSS Feed  │───▶│ Feedparser│───▶│ Xəbər Obyektləri  │   │
│  │ (18 mənbə)│    │           │    │ {title,link,src}  │   │
│  └───────────┘    └───────────┘    └─────────┬─────────┘   │
│                                              │              │
│                                              ▼              │
│                                    ┌─────────────────┐      │
│                                    │ Google Translate│      │
│                                    │ (auto → az)     │      │
│                                    └────────┬────────┘      │
│                                             │               │
│                                             ▼               │
│                                    ┌─────────────────┐      │
│                                    │ Emoji Generator │      │
│                                    │ (kategori+emoji)│      │
│                                    └────────┬────────┘      │
│                                             │               │
│                                             ▼               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                    Telethon Client                     │ │
│  │              (Telegram MTProto Protocol)               │ │
│  └───────────────────────────────────────────────────────┘ │
│                            │                                │
│                            ▼                                │
│                 ┌─────────────────────┐                     │
│                 │ Telegram Kanalı     │                     │
│                 │ @xeberdunyasiaz     │                     │
│                 └─────────────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Quraşdırma

### Tələblər
- Python 3.8+
- Telegram Bot Token
- Telegram API ID və Hash

### Addımlar

```bash
# 1. Reponu klonlayın
git clone https://github.com/username/telegram-news-bot.git
cd telegram-news-bot

# 2. Virtual environment yaradın (tövsiyə olunur)
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 3. Asılılıqları quraşdırın
pip install -r requirements.txt
```

### Asılılıqlar

| Paket | Versiya | Məqsəd |
|-------|---------|--------|
| `telethon` | latest | Telegram MTProto client |
| `feedparser` | latest | RSS/Atom feed parsing |
| `deep-translator` | latest | Çoxdilli tərcümə |

---

## ⚙️ Konfiqurasiya

### Environment Variables

Bot aşağıdakı environment variable-ları istifadə edir:

| Dəyişən | Tələb | Default | Təsvir |
|---------|-------|---------|--------|
| `API_ID` | ✅ | - | Telegram API ID ([my.telegram.org](https://my.telegram.org)) |
| `API_HASH` | ✅ | - | Telegram API Hash |
| `BOT_TOKEN` | ✅ | - | [@BotFather](https://t.me/BotFather)-dən alınan token |
| `KANAL` | ✅ | - | Hədəf kanal (məs: @kanaliniz) |

### Environment Variables Quraşdırması

#### Lokal (Windows PowerShell)
```powershell
$env:API_ID = "your_api_id"
$env:API_HASH = "your_api_hash"
$env:BOT_TOKEN = "your_bot_token"
$env:KANAL = "@your_channel"
python news_bot.py
```

#### Lokal (Linux/Mac)
```bash
export API_ID="your_api_id"
export API_HASH="your_api_hash"
export BOT_TOKEN="your_bot_token"
export KANAL="@your_channel"
python news_bot.py
```

#### `.env` fayl istifadəsi (tövsiyə olunur)
```bash
# .env faylı yaradın
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
KANAL=@your_channel
```

---

## 🚀 İstifadə

### Lokal İşlətmə
```bash
python news_bot.py
```

### Bot Çıxışı
```
🤖 XƏBƏR DÜNYASI BOT - VERSİYA 2.0
==================================================
✅ Bot işə düşdü!
📢 Kanal: @xeberdunyasiaz
🌍 Mənbə: 18 keyfiyyətli
⏰ Smart paylaşım aktiv
🔄 Hər 3 saatda yenilənir

🔄 [14:30] Xəbərlər toplanır...
✅ [1/18] APA
✅ [2/18] Trend
✅ [3/18] Report
⏸ 2.5 dəqiqə ara...
...
✅ Cəmi 18 xəbər paylaşıldı!
⏰ 3 saat gözləyir...
```

---

## ☁️ Deployment

### Render.com (Tövsiyə Olunur)

1. GitHub-a repo əlavə edin
2. [Render.com](https://render.com)-da hesab yaradın
3. **New → Background Worker** seçin
4. GitHub repo-nu bağlayın
5. Environment variables əlavə edin:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - `KANAL`

**render.yaml artıq konfiqurasiya olunub:**
```yaml
services:
  - type: worker
    name: xeber-dunyasi-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python news_bot.py
```

### Railway.app

```bash
# Railway CLI quraşdırın
npm install -g @railway/cli

# Login olun
railway login

# Layihə yaradın
railway init

# Environment variables əlavə edin
railway variables set API_ID=xxx API_HASH=xxx BOT_TOKEN=xxx KANAL=@xxx

# Deploy edin
railway up
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "news_bot.py"]
```

```bash
docker build -t xeber-bot .
docker run -d \
  -e API_ID=xxx \
  -e API_HASH=xxx \
  -e BOT_TOKEN=xxx \
  -e KANAL=@xxx \
  xeber-bot
```

### VPS/Linux Server

```bash
# Screen istifadəsi
screen -S xeber-bot
python news_bot.py
# Ctrl+A, D - detach

# SystemD service
sudo nano /etc/systemd/system/xeber-bot.service
```

```ini
[Unit]
Description=Xeber Dunyasi Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-news-bot
Environment=API_ID=xxx
Environment=API_HASH=xxx
Environment=BOT_TOKEN=xxx
Environment=KANAL=@xxx
ExecStart=/usr/bin/python3 news_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable xeber-bot
sudo systemctl start xeber-bot
sudo systemctl status xeber-bot
```

---

## 📰 Xəbər Mənbələri

### 🇦🇿 Azərbaycan (4)
| Mənbə | Növ | Tərcümə |
|-------|-----|---------|
| APA | Xəbər agentliyi | ❌ |
| Trend | Xəbər agentliyi | ❌ |
| Report | Xəbər portalı | ❌ |
| Oxu.az | Xəbər portalı | ❌ |

### 🇹🇷 Türkiyə - Dünya Xəbərləri (4)
| Mənbə | Növ | Tərcümə |
|-------|-----|---------|
| Anadolu Dünya | Xəbər agentliyi | ✅ |
| TRT Dünya | Dövlət mediya | ✅ |
| Hürriyet Dünya | Qəzet | ✅ |
| NTV Dünya | TV kanalı | ✅ |

### 🌍 Beynəlxalq (5)
| Mənbə | Növ | Tərcümə |
|-------|-----|---------|
| Reuters | Xəbər agentliyi | ✅ |
| BBC World | Beynəlxalq media | ✅ |
| Al Jazeera | Xəbər şəbəkəsi | ✅ |
| DW | Alman mediya | ✅ |
| CNN | ABŞ mediya | ✅ |

### 🔬 Elmi/Maraqlı (5)
| Mənbə | Növ | Tərcümə |
|-------|-----|---------|
| Evrim Ağacı | Elm portalı | ✅ |
| Nat Geo | Coğrafiya/Təbiət | ✅ |
| ScienceDaily | Elm xəbərləri | ✅ |
| BBC Science | Elm bölümü | ✅ |
| PopSci | Populyar elm | ✅ |

---

## 🔧 Texniki Detallar

### Fayl Strukturu
```
telegram-news-bot/
├── news_bot.py        # Əsas bot kodu
├── requirements.txt   # Python asılılıqları
├── render.yaml        # Render.com konfiqurasiyası
├── README.md          # Sənədləşdirmə
├── .env.example       # Environment nümunəsi
└── bot.session        # Telegram session (auto-generated)
```

### Əsas Funksiyalar

| Funksiya | Təsvir |
|----------|--------|
| `get_news(url)` | RSS feed-dən son xəbəri alır |
| `tr(text)` | Mətni Azərbaycan dilinə tərcümə edir |
| `improve_title(title)` | Başlığa uyğun emoji əlavə edir |
| `post(client)` | Bütün xəbərləri toplayıb paylaşır |
| `main()` | Bot-un əsas döngüsü |

### Vaxt Cədvəli
- **Paylaşım intervalı**: Hər 3 saatda bir
- **Xəbərlər arası**: 10 saniyə
- **3 xəbərdən sonra fasilə**: 2.5 dəqiqə

---

## ❗ Problemlərin Həlli

### Bot işə düşmür

```bash
# Python versiyasını yoxlayın
python --version  # 3.8+ lazımdır

# Asılılıqları yenidən quraşdırın
pip install -r requirements.txt --force-reinstall
```

### Telegram xətası: "FloodWait"
Bot çox sürətli mesaj göndərir. Kodu dəyişməyə ehtiyac yoxdur - bot avtomatik gözləyir.

### Session faylı problemi
```bash
# Session faylını silin
rm bot.session bot.session-journal

# Botu yenidən başladın
python news_bot.py
```

### RSS feed işləmir
Bəzi xəbər mənbələri RSS feed-lərini dəyişə bilər. Log mesajlarına baxın və işləməyən mənbələri `NEWS` dict-indən silin.

### Tərcümə xətası
Google Translate limiti aşıla bilər. Tərcümə olmadan başlıq göstəriləcək.

---

## 📄 Lisenziya

MIT License - Sərbəst istifadə, dəyişdirmə və paylaşma icazəsi.

---

## 👨‍💻 Müəllif

**Xəbər Dünyası Bot** - Azərbaycan üçün avtomatik xəbər botu

📧 Əlaqə: [@xeberdunyasiaz](https://t.me/xeberdunyasiaz)

---

⭐ Bu layihə sizə kömək etdisə, ulduz unutmayın!
