#!/usr/bin/env python3
"""Test different PDF libraries."""
import sys

pdf_file = "BS EN ISO 14122-1-2016.pdf"

print("="*60)
print("1️⃣ PyPDF2 ile test")
print("="*60)
try:
    import PyPDF2
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f"✓ Sayfa sayısı: {len(reader.pages)}")
        print(f"✓ Şifreli mi: {reader.is_encrypted}")
        
        if len(reader.pages) > 0:
            page = reader.pages[0]
            text = page.extract_text()
            print(f"✓ İlk sayfa karakter: {len(text)}")
            print(f"✓ İlk 300 karakter:\n{text[:300]}")
except Exception as e:
    print(f"❌ Hata: {e}")

print("\n" + "="*60)
print("2️⃣ pdfplumber ile test")
print("="*60)
try:
    import pdfplumber
    with pdfplumber.open(pdf_file) as pdf:
        print(f"✓ Sayfa sayısı: {len(pdf.pages)}")
        
        if len(pdf.pages) > 0:
            text = pdf.pages[0].extract_text()
            print(f"✓ İlk sayfa karakter: {len(text) if text else 0}")
            if text:
                print(f"✓ İlk 300 karakter:\n{text[:300]}")
except Exception as e:
    print(f"❌ Hata: {e}")

print("\n" + "="*60)
print("3️⃣ pymupdf (fitz) ile test")
print("="*60)
try:
    import fitz
    doc = fitz.open(pdf_file)
    print(f"✓ Sayfa sayısı: {doc.page_count}")
    
    if doc.page_count > 0:
        page = doc[0]
        text = page.get_text()
        print(f"✓ İlk sayfa karakter: {len(text)}")
        print(f"✓ İlk 300 karakter:\n{text[:300]}")
    doc.close()
except ImportError:
    print("⚠️  pymupdf yüklü değil (pip install pymupdf)")
except Exception as e:
    print(f"❌ Hata: {e}")
