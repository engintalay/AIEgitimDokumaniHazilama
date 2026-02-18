# AI Eğitim Dokümanı Hazırlama

Ham bilgi kaynaklarından (PDF, DOC, TXT) yapay zeka modeli eğitimi için JSONL formatında dataset üreten araç.

## Özellikler

- ✅ PDF, DOCX, TXT formatlarını destekler
- ✅ Ollama, LM Studio ve llama.cpp ile çalışır
- ✅ OpenAI desteği için hazır altyapı
- ✅ Paragraf bazında otomatik soru-cevap üretimi
- ✅ Confidence değerlendirmesi (high/low)
- ✅ Detaylı ilerleme takibi (ETA, hız, istatistikler)
- ✅ Checkpoint/Resume özelliği
- ✅ Vektörel Arama (RAG) desteği (ChromaDB)
- ✅ Modern Web Arayüzü (Flask)
- ✅ JSONL formatında çıktı
- ✅ Modüler ve genişletilebilir yapı

## Kurulum

### Otomatik Kurulum (Önerilen)

**Linux/Mac:**
```bash
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### Manuel Kurulum

```bash
# Virtual environment oluştur
python3 -m venv venv

# Aktifleştir (Linux/Mac)
source venv/bin/activate

# Aktifleştir (Windows)
venv\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt
```

## Kullanım

### Hızlı Başlangıç

```bash
# Kurulum scriptini çalıştır (ilk kez)
./setup.sh

# Programı çalıştır
./run.sh --input dokuman.pdf --output dataset.jsonl

# Veya manuel
source venv/bin/activate
python cli/main.py --input dokuman.pdf
```

### Temel Kullanım

```bash
python cli/main.py --input dokuman.pdf --output dataset.jsonl
```

### Config Dosyası ile

```bash
python cli/main.py --input dokuman.pdf --config config/config.yaml
```

### Kaldığı Yerden Devam

```bash
python cli/main.py --input dokuman.pdf --resume
```

### Checkpoint Temizle

```bash
python cli/main.py --input dokuman.pdf --clear-checkpoint
```

### Detaylı Log

```bash
python cli/main.py --input dokuman.pdf --verbose
```

## Vektörel Arama (RAG) ve Web Arayüzü

### 1. Web Arayüzünü Başlatma
Modern ve interaktif arayüz üzerinden soru-cevap yapmak için:
```bash
python3 app.py
```
Ardından tarayıcınızda `http://127.0.0.1:5000` adresine gidin.

### 2. Doküman İndeksleme (Ingestion)
Dokümanları manuel olarak vektör veri tabanına eklemek için:
```bash
python3 ingest.py --input dokuman.pdf
```

### 3. CLI Üzerinden Soru Sorma (RAG)
İndekslenmiş dokümanlar arasında akıllı arama yapıp yanıt almak için:
```bash
python3 ask_rag.py "Sorunuzu buraya yazın"
```

## Konfigürasyon

`config/config.yaml` dosyasını düzenleyerek ayarları özelleştirebilirsiniz:

- Model tipi (ollama, lmstudio, llamacpp, openai)
- Model parametreleri (temperature, max_tokens)
- Soru üretim ayarları
- Checkpoint ayarları
- İlerleme gösterimi
- Log ayarları

## Çıktı Formatı

```json
{
  "instruction": "Kullanıcının sorusu",
  "input": "",
  "output": "Modelin vermesi gereken cevap",
  "confidence": "high"
}
```

## Confidence Değerleri

- **high**: Kılavuzda açıkça yazıyor, net kural var, menü yolu belirtilmiş
- **low**: Kılavuzda geçmiyor, belirsiz, dış kaynak gerektiriyor

## Proje Yapısı

### Ana Dosyalar
- `split_paragraphs.py`: Dokümanları akıllı bir şekilde temizler ve mantıksal birimlere (paragraf veya sayfa) böler. Başlıkları, listeleri ve edebî atıfları korur/birleştirir.
- `app.py`: Modern web arayüzünü başlatan Flask sunucusu.
- `ingest.py`: Dokümanları vektör veri tabanına (ChromaDB) indeksler.
- `ask_rag.py`: Vektör veri tabanı üzerinden arama yaparak soru-cevap (RAG) işlemini gerçekleştirir.
- `setup.sh` / `setup.bat`: Gerekli bağımlılıkları yükleyen kurum scriptleri.
- `run.sh`: Tüm süreci otomatize eden ana çalıştırma scripti.

### Core Modülleri (`core/`)
- `document_parser.py`: PDF, DOCX ve TXT dosyalarından metin, tablo ve görsel ayıklama işlemlerini yapar.
- `text_processor.py`: Ayıklanan metni temizleme, satır birleştirme (unwrapping) ve mantıksal blokları (başlık-paragraf ilişkisi gibi) birleştirme mantığını içerir.
- `ai_client.py`: AI model istemcileri için temel arayüz (interface).
- `ai_client_factory.py`: Konfigürasyona göre doğru AI istemcisini (Ollama, OpenAI vb.) oluşturan fabrika sınıfı.
- `ollama_client.py`, `openai_client.py`, `lmstudio_client.py`, `llamacpp_client.py`: Farklı yapay zeka servisleri için özel implementasyonlar.
- `question_generator.py`: AI modelini kullanarak metin bloklarından soru-cevap çiftleri üretir.
- `dataset_writer.py`: Üretilen verileri JSONL formatında diske yazar.

### CLI Arayüzü (`cli/`)
- `main.py`: Dataset hazırlama sürecini başlatan ana giriş noktası. Parametre yönetimi ve iş akışını kontrol eder.

### Yardımcı Modüller (`utils/`)
- `progress.py`: Konsolda ilerleme çubuğu, hız ve kalan süre bilgilerini gösterir.
- `checkpoint.py`: Yarıda kalan işlemlerin kaydedilmesini ve sonradan devam edilmesini sağlar.
- `logger.py`: Tüm sistemin loglama yapılandırmasını yönetir.

### Test ve Debug
- `debug_pdf.py`: PDF yapısını incelemek ve sorunları tespit etmek için yardımcı araç.
- `test_*.py`: Çeşitli modüllerin doğru çalışıp çalışmadığını kontrol eden test scriptleri.

## Gereksinimler

- Python 3.8+
- Ollama veya LM Studio (local AI için)
- Desteklenen doküman formatları: PDF, DOCX, TXT

## Lisans

MIT
