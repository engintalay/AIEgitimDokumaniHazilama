#!/bin/bash

# AI Eğitim Dokümanı Hazırlama - Uygulama Kaldırma Betiği
PROJECT_DIR="/home/engin/projects/AIEgitimDokumaniHazilama"

echo "🗑️ Uygulama kaldırılıyor..."

# 1. Systemd servisini durdur ve kaldır
if [ -f "/etc/systemd/system/ai_app.service" ]; then
    echo "⚙️ Systemd servisi durduruluyor ve kaldırılıyor..."
    sudo systemctl stop ai_app 2>/dev/null
    sudo systemctl disable ai_app 2>/dev/null
    sudo rm -f /etc/systemd/system/ai_app.service
    sudo systemctl daemon-reload
else
    echo "⚠️ Systemd servisi bulunamadı, atlanıyor."
fi

# 2. Nginx yapılandırmasını kaldır
echo "🌐 Nginx yapılandırması temizleniyor..."
sudo rm -f /etc/nginx/sites-enabled/ai_app
sudo rm -f /etc/nginx/sites-available/ai_app
sudo systemctl restart nginx

# 3. Virtual Environment ve geçici dosyaları sil
echo "🐍 Python ortamı ve geçici dosyalar siliniyor..."
if [ -d "$PROJECT_DIR/venv" ]; then
    rm -rf "$PROJECT_DIR/venv"
fi

if [ -f "$PROJECT_DIR/ai_app.sock" ]; then
    rm -f "$PROJECT_DIR/ai_app.sock"
fi

echo "✅ Uygulama başarıyla kaldırıldı!"
echo "💡 Not: Veritabanı ve yüklenen dosyalar ($PROJECT_DIR/data/) korunmuştur."
