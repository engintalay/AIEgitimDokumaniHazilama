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

### 1. Geliştirme/Yerel Kurulum
Geliştirme ortamı için otomatik kurulum scriptlerini kullanabilirsiniz:

**Linux/Mac:**
```bash
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### 2. Canlı (Production) Kurulum
Uygulamayı sunucuda (Docker olmadan) güvenli ve performanslı çalıştırmak için:
```bash
chmod +x setup_prod.sh
./setup_prod.sh
```
Bu script **Gunicorn**, **Systemd** ve **Nginx** yapılandırmasını otomatik olarak yapar.

## Kullanım

### Hızlı Başlama (Yerel)
```bash
# Web arayüzünü (Development) başlat
./run.sh --web
```
Tarayıcıda: `http://localhost:5000`

### Production Kullanımı
Production kurulumu yapıldıktan sonra uygulama **Nginx** üzerinden **81 portunda** yayında olacaktır.
Tarayıcıda: `http://localhost:81`

---

## Vektörel Arama (RAG) ve Web Arayüzü

### 1. Web Arayüzünü Başlatma
Yerel geliştirme sunucusunu manuel başlatmak için:
```bash
python3 app.py
```

### 2. Doküman İndeksleme (Ingestion)
```bash
python3 ingest.py --input dokuman.pdf
```

### 3. CLI Üzerinden Soru Sorma (RAG)
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
