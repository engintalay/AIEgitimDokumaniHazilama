#!/usr/bin/env python3
"""Test script to check if model can generate JSON."""
import requests
import json

# Test paragraph
test_paragraph = """
Brother DCP-8070D çok fonksiyonlu bir yazıcıdır. 
Yazıcı, tarayıcı ve fotokopi özelliklerine sahiptir.
Maksimum çözünürlük 2400 x 600 dpi'dir.
"""

# Create prompt
prompt = """Sen bir Türkçe eğitim dataset uzmanısın. Aşağıdaki metinden 3 adet soru-cevap çifti oluştur.

METIN:
Brother DCP-8070D çok fonksiyonlu bir yazıcıdır. 
Yazıcı, tarayıcı ve fotokopi özelliklerine sahiptir.
Maksimum çözünürlük 2400 x 600 dpi'dir.

ÇOK ÖNEMLİ: Sadece ve sadece aşağıdaki JSON formatında cevap ver:

[
  {
    "instruction": "DCP-8070D hangi özelliklere sahiptir?",
    "input": "",
    "output": "Yazıcı, tarayıcı ve fotokopi özelliklerine sahiptir.",
    "confidence": "high"
  }
]"""

# Send to Ollama
url = "http://localhost:11434/api/generate"
payload = {
    "model": "RefinedNeuro/Turkcell-LLM-7b-v1:latest",
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.3
    }
}

print("🔄 Ollama'ya istek gönderiliyor...")
print(f"Model: {payload['model']}\n")

response = requests.post(url, json=payload, timeout=60)
result = response.json().get('response', '')

print("=" * 60)
print("OLLAMA CEVABI:")
print("=" * 60)
print(result)
print("=" * 60)

# Try to parse JSON
import re
json_match = re.search(r'\[.*\]', result, re.DOTALL)
if json_match:
    try:
        data = json.loads(json_match.group(0))
        print("\n✅ JSON başarıyla parse edildi!")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ JSON parse hatası: {e}")
else:
    print("\n❌ JSON array bulunamadı!")
