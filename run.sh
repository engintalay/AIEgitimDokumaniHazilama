#!/bin/bash
# Hızlı başlatma scripti

# Virtual environment'ı aktifleştir
if [ -d "venv" ]; then
    source venv/bin/activate
    if [ "$1" == "--web" ]; then
        echo "🌐 Web arayüzü başlatılıyor..."
        python app.py
    else
        python cli/main.py "$@"
    fi
else
    echo "❌ Virtual environment bulunamadı!"
    echo "Önce kurulum yapın: ./setup.sh"
    exit 1
fi
