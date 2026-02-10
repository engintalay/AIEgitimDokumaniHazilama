# AI Eğitim Dokümanı Hazırlama

Ham bilgi kaynaklarından (PDF, DOC, TXT) yapay zeka modeli eğitimi için JSONL formatında dataset üreten araç.

## Özellikler

- ✅ PDF, DOCX, TXT formatlarını destekler
- ✅ Ollama ve LM Studio ile çalışır
- ✅ OpenAI desteği için hazır altyapı
- ✅ Paragraf bazında otomatik soru-cevap üretimi
- ✅ Confidence değerlendirmesi (high/low)
- ✅ Detaylı ilerleme takibi (ETA, hız, istatistikler)
- ✅ Checkpoint/Resume özelliği
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

## Konfigürasyon

`config/config.yaml` dosyasını düzenleyerek ayarları özelleştirebilirsiniz:

- Model tipi (ollama, lmstudio, openai)
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

```
├── core/                    # Ana modüller
│   ├── document_parser.py   # Doküman okuma
│   ├── text_processor.py    # Metin işleme
│   ├── ai_client.py         # AI client interface
│   ├── ollama_client.py     # Ollama implementasyonu
│   ├── lmstudio_client.py   # LM Studio implementasyonu
│   ├── openai_client.py     # OpenAI implementasyonu
│   ├── question_generator.py # Soru üretimi
│   └── dataset_writer.py    # JSONL yazma
├── cli/                     # CLI arayüzü
│   └── main.py
├── utils/                   # Yardımcı modüller
│   ├── progress.py          # İlerleme takibi
│   ├── checkpoint.py        # Checkpoint yönetimi
│   └── logger.py            # Loglama
├── config/                  # Konfigürasyon
│   └── config.yaml
└── data/                    # Veri dizini
    ├── output/              # Çıktı dosyaları
    ├── checkpoints/         # Checkpoint dosyaları
    └── logs/                # Log dosyaları
```

## Gereksinimler

- Python 3.8+
- Ollama veya LM Studio (local AI için)
- Desteklenen doküman formatları: PDF, DOCX, TXT

## Lisans

MIT
