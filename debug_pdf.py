#!/usr/bin/env python3
"""Debug PDF parsing."""
import sys
sys.path.insert(0, '.')

import pdfplumber

pdf_file = "BS EN ISO 14122-1-2016.pdf"

print(f"📄 PDF okunuyor: {pdf_file}\n")

try:
    with pdfplumber.open(pdf_file) as pdf:
        print(f"✓ Toplam sayfa: {len(pdf.pages)}")
        print(f"✓ PDF metadata: {pdf.metadata}\n")
        
        print("="*60)
        print("SAYFA ANALİZİ:")
        print("="*60)
        
        total_text = []
        for i, page in enumerate(pdf.pages[:5]):  # İlk 5 sayfa
            text = page.extract_text()
            char_count = len(text) if text else 0
            total_text.append(text or "")
            
            print(f"\nSayfa {i+1}:")
            print(f"  Karakter sayısı: {char_count}")
            
            if text:
                print(f"  İlk 200 karakter:")
                print(f"  {text[:200]}")
            else:
                print(f"  ⚠️  Metin çıkarılamadı!")
                
                # Alternatif yöntem dene
                print(f"  🔍 Alternatif yöntem deneniyor...")
                words = page.extract_words()
                print(f"  Kelime sayısı: {len(words)}")
                if words:
                    sample_words = " ".join([w['text'] for w in words[:20]])
                    print(f"  İlk kelimeler: {sample_words}")
        
        print("\n" + "="*60)
        print(f"TOPLAM METİN: {sum(len(t) for t in total_text)} karakter")
        
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
