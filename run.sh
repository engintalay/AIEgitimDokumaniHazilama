#!/bin/bash
# Hızlı başlatma scripti

# Virtual environment'ı aktifleştir
if [ -d "venv" ]; then
    source venv/bin/activate
    python cli/main.py "$@"
else
    echo "❌ Virtual environment bulunamadı!"
    echo "Önce kurulum yapın: ./setup.sh"
    exit 1
fi
