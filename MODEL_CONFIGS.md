# Model Konfigürasyon Örnekleri

## LM Studio (Qwen2.5)

```yaml
model:
  type: "lmstudio"
  name: "qwen2.5-14b-instruct"
  endpoint: "http://localhost:1234"
  temperature: 0.3
  max_tokens: 2000
  
  use_system_prompt: true
  system_prompt: "Sen bir Türkçe eğitim dataset uzmanısın. Verilen talimatlara göre JSON formatında soru-cevap çiftleri oluşturursun."
  json_mode: true
  json_wrapper: "questions"  # {"questions": [...]}
```

## Ollama (Qwen2.5)

```yaml
model:
  type: "ollama"
  name: "qwen2.5:14b"
  endpoint: "http://localhost:11434"
  temperature: 0.3
  max_tokens: 2000
  
  use_system_prompt: false  # Ollama için genelde false
  system_prompt: ""
  json_mode: false
  json_wrapper: ""  # Direkt array: [...]
```

## Ollama (Llama 3.1)

```yaml
model:
  type: "ollama"
  name: "llama3.1:8b"
  endpoint: "http://localhost:11434"
  temperature: 0.3
  max_tokens: 2000
  
  use_system_prompt: false
  system_prompt: ""
  json_mode: false
  json_wrapper: ""
```

## OpenAI (GPT-4)

```yaml
model:
  type: "openai"
  name: "gpt-4"
  endpoint: "https://api.openai.com"
  api_key: "sk-..."
  temperature: 0.3
  max_tokens: 2000
  
  use_system_prompt: true
  system_prompt: "Sen bir Türkçe eğitim dataset uzmanısın."
  json_mode: true
  json_wrapper: "questions"
```

## Ayar Açıklamaları

### `use_system_prompt`
- `true`: System message kullan (LM Studio, OpenAI için önerilen)
- `false`: Sadece user message (Ollama için önerilen)

### `system_prompt`
- Model'e verilen sistem talimatı
- JSON formatı, dil, görev tanımı içerir

### `json_mode`
- `true`: API'ye JSON mode parametresi gönder (LM Studio, OpenAI)
- `false`: Normal mode (Ollama)

### `json_wrapper`
- `"questions"`: Çıktı `{"questions": [...]}` formatında
- `""` (boş): Çıktı direkt `[...]` array formatında
- Model'in tercihine göre ayarla

## Test Etme

```bash
# Config'i düzenle
nano config/config.yaml

# Test et
./run.sh --input test.pdf --verbose

# Log'ları kontrol et
tail -f data/logs/app.log
```
