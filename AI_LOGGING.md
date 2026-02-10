# AI İstek/Cevap Loglama

## Kullanım

### 1. Config Dosyası ile

`config/config.yaml` dosyasını düzenle:

```yaml
logging:
  level: "DEBUG"
  show_ai_requests: true  # Bunu true yap
```

Sonra çalıştır:
```bash
./run.sh --input dokuman.pdf
```

### 2. Verbose Modu ile (Hızlı)

```bash
# --verbose ile otomatik aktif olur
./run.sh --input dokuman.pdf --verbose
```

### 3. Manuel Aktifleştirme

```bash
source venv/bin/activate
python cli/main.py --input dokuman.pdf --verbose
```

## Log Çıktısı

Log dosyası: `data/logs/app.log`

```
=== OLLAMA REQUEST ===
URL: http://localhost:11434/api/generate
Model: qwen2.5:14b
Temperature: 0.3
Prompt:
Sen bir Türkçe eğitim dataset uzmanısın...

=== OLLAMA RESPONSE ===
Response:
[
  {
    "instruction": "...",
    "output": "...",
    "confidence": "high"
  }
]
======================
```

## Log Dosyasını İzle

```bash
# Canlı izle
tail -f data/logs/app.log

# Son 50 satır
tail -n 50 data/logs/app.log

# Sadece Ollama isteklerini göster
grep -A 10 "OLLAMA REQUEST" data/logs/app.log
```

## Sorun Giderme

### Prompt'u görmek için:
```bash
grep -A 20 "Prompt:" data/logs/app.log
```

### Cevapları görmek için:
```bash
grep -A 20 "Response:" data/logs/app.log
```

### Hataları görmek için:
```bash
grep "ERROR" data/logs/app.log
```
