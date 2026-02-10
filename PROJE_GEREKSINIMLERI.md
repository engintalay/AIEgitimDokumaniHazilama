# AI Eğitim Dokümanı Hazırlama - Proje Gereksinimleri

## Genel Bakış
Ham bilgi kaynaklarından (PDF, DOC, TXT vb.) yapay zeka modeli eğitimi için kullanılabilecek JSONL formatında dataset üreten bir araç.

---

## 1. Girdi Formatları
- PDF
- DOC/DOCX
- TXT
- Benzeri metin tabanlı formatlar

---

## 2. Çıktı Formatı
**Format:** JSONL (her satırda bir JSON objesi)

**Yapı:**
```json
{
  "instruction": "Kullanıcının sorusu",
  "input": "Özelleşmiş sorular için ek bilgi (çoğunlukla boş)",
  "output": "Modelin vermesi gereken net, kısa ve doğru cevap",
  "confidence": "high"
}
```

**Not:** `input` alanı çoğunlukla boş olacak, sadece özelleşmiş sorularda dolu olacak.

---

## 3. Soru-Cevap Üretimi
- AI tarafından otomatik oluşturulacak
- Her paragraf için minimum 3-4 soru
- Soru sayısı AI tarafından dinamik belirlenecek
- Halüsinasyon yaratmayacak şekilde
- Ezberlemeyi önleyecek kadar çeşitli sorular

---

## 4. AI Model Desteği

### Desteklenen Modeller:
1. **Ollama** (local)
2. **LM Studio** (local)
3. **Genişletilebilir altyapı** (OpenAI, Claude vb. için hazır olacak)

### Donanım Bilgisi:
- Ana makine: AMD Ryzen 7840HS (CPU ağırlıklı)
- Yedek: Nvidia GTX 1650 4GB (mobil)
- Opsiyonel: Nvidia A5000 (kiralama ile)

---

## 5. Confidence (Güven) Kuralları

### `confidence: "high"` - Şu durumlardan EN AZ BİRİ sağlanıyorsa:

✅ **1. Kılavuzda açıkça yazıyorsa**
```json
{
  "instruction": "ADF aynı anda kaç sayfa alır?",
  "output": "ADF en fazla 20 sayfa alabilir.",
  "confidence": "high"
}
```

✅ **2. Net "YAPILMAZ / YAPILIR" kuralı varsa**
```json
{
  "instruction": "Inkjet kağıt kullanabilir miyim?",
  "output": "Hayır. Inkjet kağıt kullanılması önerilmez.",
  "confidence": "high"
}
```

✅ **3. Menü yolu kılavuzda veriliyorsa**
- Örnek: Menü 1-3-1 → Toner tasarrufu

### `confidence: "low"` - Şu durumlardan BİRİ bile varsa:

❌ **1. Kılavuzda hiç geçmiyorsa**
```json
{
  "instruction": "Bu cihaz Wi-Fi destekler mi?",
  "output": "Kullanım kılavuzunda Wi-Fi desteği belirtilmemektedir.",
  "confidence": "low"
}
```

❌ **2. Kullanıcı modern özellik varsayıyorsa**
```json
{
  "instruction": "Telefonumdan yazdırabilir miyim?",
  "output": "Kullanım kılavuzunda mobil yazdırma desteği bilgisi bulunmamaktadır.",
  "confidence": "low"
}
```

❌ **3. Teknik ama dış kaynak gerektiren soruysa**
- Güncel driver linki
- Firmware versiyonu
- Güncel OS uyumu

**ÖNEMLİ:** Sadece `high` ve `low` değerleri kullanılacak, `medium` YOK!

---

## 6. Metin Parçalama
- **Yöntem:** Paragraf bazında
- Her paragraf ayrı ayrı işlenecek
- Her paragraftan minimum 3-4 soru üretilecek

---

## 7. Konfigürasyon Dosyası

**Özellik:** Zengin ve kapsamlı config dosyası

**İçerik (önerilen):**
- Model tipi (ollama, lmstudio, openai vb.)
- Endpoint URL
- Model adı
- Temperature
- Max tokens
- Min/max soru sayısı
- Timeout ayarları
- Retry ayarları
- API key (opsiyonel modeller için)
- Parçalama ayarları
- Çıktı dizini
- Log seviyesi

---

## 8. Kullanıcı Arayüzü

### Başlangıç:
- **CLI (Command Line Interface)**

### Gelecek:
- Modüler yapı ile GUI desteği için hazır
- Modüler yapı ile Web arayüzü desteği için hazır

---

## 9. İlerleme Takibi (ÇOK ÖNEMLİ!)

### Console Çıktısı:
- Detaylı ilerleme bilgisi
- Hangi paragraf işleniyor
- Kaç tane soru üretildi
- Progress bar / yüzde gösterimi
- Tahmini bitiş süresi
- Geçen süre

### Ara Sonuçlar:
- Her üretilen soru-cevap çifti hemen JSONL dosyasına yazılacak
- Kullanıcı işlem devam ederken sonuçları görebilecek

### Checkpoint/Resume:
- Büyük veri setleri için kaldığı yerden devam özelliği
- İşlem kesintiye uğrarsa devam edebilmeli
- İşlenen paragraflar kaydedilmeli

---

## 10. Programlama Dili
**Python**

**Seçim Nedenleri:**
- Ollama ve LM Studio için hazır kütüphaneler
- PDF/DOC parsing için zengin ekosistem
- Kolay kurulum ve taşınabilirlik
- CPU ve GPU desteği kolay yönetilebilir
- Farklı makinelerde çalıştırması basit

---

## 11. Mimari Yapı

### Modüler Tasarım:
```
├── core/
│   ├── document_parser.py      # PDF, DOC, TXT okuma
│   ├── text_processor.py       # Paragraf parçalama
│   ├── ai_client.py            # AI model interface (abstract)
│   ├── ollama_client.py        # Ollama implementasyonu
│   ├── lmstudio_client.py      # LM Studio implementasyonu
│   ├── openai_client.py        # OpenAI implementasyonu (gelecek)
│   ├── question_generator.py   # Soru-cevap üretimi
│   ├── confidence_evaluator.py # Confidence belirleme
│   └── dataset_writer.py       # JSONL yazma
├── cli/
│   └── main.py                 # CLI arayüzü
├── gui/                        # Gelecek için hazır
├── web/                        # Gelecek için hazır
├── config/
│   └── config.yaml             # Konfigürasyon
├── utils/
│   ├── progress.py             # İlerleme takibi
│   ├── checkpoint.py           # Resume özelliği
│   └── logger.py               # Loglama
└── requirements.txt
```

---

## 12. Temel İş Akışı

1. **Girdi Okuma:** PDF/DOC/TXT dosyası okunur
2. **Parçalama:** Metin paragraflara ayrılır
3. **Checkpoint Kontrolü:** Daha önce işlenmiş paragraflar atlanır
4. **Her Paragraf İçin:**
   - AI modeline gönderilir
   - 3-4+ soru-cevap çifti üretilir
   - Confidence değeri belirlenir
   - JSONL dosyasına yazılır
   - Progress güncellenir
   - Checkpoint kaydedilir
5. **Tamamlanma:** Özet rapor gösterilir

---

## 13. Örnek Kullanım (CLI)

```bash
# Temel kullanım
python main.py --input dokuman.pdf --output dataset.jsonl

# Config dosyası ile
python main.py --input dokuman.pdf --output dataset.jsonl --config config.yaml

# Kaldığı yerden devam
python main.py --input dokuman.pdf --output dataset.jsonl --resume

# Detaylı log
python main.py --input dokuman.pdf --output dataset.jsonl --verbose
```

---

## 14. Başarı Kriterleri

✅ Farklı formatlardaki dokümanları okuyabilmeli
✅ Paragraf bazında doğru parçalama yapabilmeli
✅ Ollama ve LM Studio ile çalışabilmeli
✅ Confidence kurallarını doğru uygulayabilmeli
✅ Detaylı ilerleme gösterebilmeli
✅ Kaldığı yerden devam edebilmeli
✅ Geçerli JSONL formatında çıktı üretebilmeli
✅ Modüler ve genişletilebilir yapıda olmalı

---

## 15. Gelecek Özellikler (Opsiyonel)

- GUI arayüzü
- Web arayüzü
- Batch processing (çoklu dosya)
- Paralel işleme
- Özel prompt şablonları
- Dataset kalite analizi
- Duplicate detection
- Export to different formats (CSV, JSON vb.)

---

**Proje Başlangıç Tarihi:** 10 Şubat 2026
**Durum:** Gereksinimler toplandı, geliştirme başlayacak
