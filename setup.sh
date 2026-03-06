#!/bin/bash
# Kurulum scripti

echo "🚀 AI Eğitim Dokümanı Hazırlama - Kurulum"
echo "=========================================="
echo ""

# Virtual environment oluştur
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment oluşturuluyor..."
    python3 -m venv venv
    echo "✓ Virtual environment oluşturuldu"
else
    echo "✓ Virtual environment zaten mevcut"
fi

# Virtual environment'ı aktifleştir
echo ""
echo "🔧 Paketler yükleniyor..."
source venv/bin/activate

# Paketleri yükle
pip install --upgrade pip
pip install -r requirements.txt

# Gerekli dizinleri oluştur
echo "📂 Dizinler oluşturuluyor..."
mkdir -p data/output data/checkpoints data/logs data/images data/vector_db data/uploads data/database

# .env dosyası kontrolü
if [ ! -f ".env" ]; then
    echo "📄 .env dosyası bulunamadı, .env.template kullanılarak oluşturuluyor..."
    cp .env.template .env
    echo "⚠️ LÜTFEN .env DOSYASINI KENDİ BİLGİLERİNİZLE GÜNCELLEYİN!"
fi

echo ""
echo "✅ Kurulum tamamlandı!"
echo ""
echo "Kullanım için:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "💡 Production kurulumu için setup_prod.sh kullanabilirsiniz."
echo ""
