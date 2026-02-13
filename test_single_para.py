#!/usr/bin/env python3
"""Test single paragraph generation."""
import sys
sys.path.insert(0, '.')

from core.llamacpp_client import LlamaCppClient
from core.question_generator import QuestionGenerator
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor

# Config
config = {
    'endpoint': 'http://127.0.0.1:8080',
    'temperature': 0.3,
    'max_tokens': 800,
    'timeout': 300,
    'use_system_prompt': True,
    'system_prompt': 'Sen bir Türkçe eğitim dataset uzmanısın. Verilen talimatlara göre JSON formatında soru-cevap çiftleri oluşturursun.'
}

# Parse PDF
text = DocumentParser.parse('BS EN ISO 14122-1-2016.pdf')
paragraphs = TextProcessor.split_into_paragraphs(text, 150)

print(f"Toplam paragraf: {len(paragraphs)}\n")

# Test paragraph 2 (0-indexed = 1)
para_idx = 1
para = paragraphs[para_idx]

print(f"Paragraf {para_idx + 1} ({len(para)} karakter):")
print("=" * 60)
print(para)
print("=" * 60)

# Create client and generator
client = LlamaCppClient(config)
generator = QuestionGenerator(client, min_questions=2, max_questions=5)

print("\n🔄 Soru üretiliyor...\n")

try:
    questions = generator.generate_questions(para)
    print(f"✅ {len(questions)} soru üretildi:\n")
    import json
    print(json.dumps(questions, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
