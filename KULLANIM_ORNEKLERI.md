# Örnek Kullanım Senaryoları

## 1. İlk Kurulum

```bash
# Projeyi klonla veya indir
cd AIEgitimDokumaniHazilama

# Gerekli paketleri yükle
pip install -r requirements.txt

# Ollama'yı başlat (başka bir terminalde)
ollama serve

# Model indir (örnek)
ollama pull llama3.2
```

## 2. Temel Kullanım

```bash
# Basit kullanım
python cli/main.py --input dokuman.pdf

# Çıktı dosyası belirt
python cli/main.py --input dokuman.pdf --output my_dataset.jsonl

# Detaylı log
python cli/main.py --input dokuman.pdf --verbose
```

## 3. Config Dosyası Özelleştirme

`config/config.yaml` dosyasını düzenle:

```yaml
model:
  type: "ollama"
  name: "llama3.2"
  endpoint: "http://localhost:11434"
  temperature: 0.7
  max_tokens: 2000

generation:
  min_questions_per_paragraph: 3
  max_questions_per_paragraph: 8
```

## 4. Kaldığı Yerden Devam

```bash
# İşlem yarıda kesilirse
python cli/main.py --input dokuman.pdf --resume

# Checkpoint'i temizle ve baştan başla
python cli/main.py --input dokuman.pdf --clear-checkpoint
```

## 5. LM Studio ile Kullanım

`config/config.yaml` dosyasını düzenle:

```yaml
model:
  type: "lmstudio"
  name: "local-model"
  endpoint: "http://localhost:1234"
```

Sonra çalıştır:

```bash
python cli/main.py --input dokuman.pdf
```

## 6. Farklı Doküman Formatları

```bash
# PDF
python cli/main.py --input manual.pdf

# DOCX
python cli/main.py --input guide.docx

# TXT
python cli/main.py --input notes.txt
```

## 7. Çıktı Kontrolü

```bash
# Dataset'i görüntüle
cat data/output/dataset.jsonl

# İlk 5 satırı göster
head -n 5 data/output/dataset.jsonl

# Satır sayısını say
wc -l data/output/dataset.jsonl

# JSON formatını kontrol et
jq '.' data/output/dataset.jsonl | head -n 20
```

## 8. Sorun Giderme

### Ollama bağlanamıyor

```bash
# Ollama'nın çalıştığını kontrol et
curl http://localhost:11434/api/tags

# Modelleri listele
ollama list
```

### LM Studio bağlanamıyor

```bash
# LM Studio'nun çalıştığını kontrol et
curl http://localhost:1234/v1/models
```

### Checkpoint sıfırlama

```bash
# Checkpoint dosyalarını temizle
rm -rf data/checkpoints/*

# Veya programla temizle
python cli/main.py --input dokuman.pdf --clear-checkpoint
```

## 9. Performans İpuçları

- Küçük modellerle başlayın (daha hızlı)
- `temperature` değerini düşürün (daha tutarlı sonuçlar)
- `max_tokens` değerini artırın (daha uzun cevaplar için)
- Checkpoint özelliğini aktif tutun (kesinti durumunda)

## 10. Batch İşleme (Gelecek Özellik)

```bash
# Şu an için döngü ile
for file in *.pdf; do
    python cli/main.py --input "$file" --output "output_${file%.pdf}.jsonl"
done
```
