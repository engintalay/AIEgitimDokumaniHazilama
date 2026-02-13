#!/usr/bin/env python3
"""Test llama.cpp client."""
import sys
from core.llamacpp_client import LlamaCppClient

# Test config
config = {
    'endpoint': 'http://127.0.0.1:8080',
    'temperature': 0.3,
    'max_tokens': 500,
    'timeout': 60,
    'use_system_prompt': True,
    'system_prompt': 'Sen bir Türkçe eğitim dataset uzmanısın.'
}

print("🔍 llama.cpp Client Test\n")
print(f"Endpoint: {config['endpoint']}")

# Create client
client = LlamaCppClient(config)

# Check availability
print("\n1️⃣ Servis kontrolü...")
if client.is_available():
    print("✅ llama.cpp server çalışıyor")
else:
    print("❌ llama.cpp server erişilemiyor")
    print("\nllama.cpp'yi şu şekilde başlatın:")
    print("  llama-server -m model.gguf --port 8080")
    sys.exit(1)

# Test generation
print("\n2️⃣ Metin üretimi testi...")
test_prompt = """Aşağıdaki metinden 2 soru-cevap çifti oluştur:

METIN:
Python programlama dili 1991 yılında Guido van Rossum tarafından geliştirilmiştir.
Basit sözdizimi ve okunabilir kod yapısı ile bilinir.

JSON formatında cevap ver:
[
  {
    "instruction": "soru",
    "input": "",
    "output": "cevap",
    "confidence": "high"
  }
]"""

try:
    print("\n📤 İstek gönderiliyor...")
    response = client.generate(test_prompt)
    print("\n📥 Cevap alındı:")
    print("=" * 60)
    print(response)
    print("=" * 60)
    print("\n✅ Test başarılı!")
except Exception as e:
    print(f"\n❌ Hata: {e}")
    sys.exit(1)
