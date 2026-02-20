#!/bin/bash

# AI Eğitim Dokümanı Hazırlama - Prod Deployment Script

echo "🚀 Başlat lıyor: Prod Deployment..."

# 1. Pull latest changes (if in a git repo)
if [ -d .git ]; then
    echo "📥 Güncellemeler çekiliyor..."
    git pull origin main
fi

# 2. Build and restart containers
echo "🏗️ Container'lar derleniyor ve başlatılıyor..."
docker-compose up -d --build

# 3. Clean up old images
echo "🧹 Eski imajlar temizleniyor..."
docker image prune -f

echo "✅ İşlem tamamlandı! Uygulama Nginx üzerinden (Port 80) yayında."
echo "🔍 Durumu kontrol etmek için: docker-compose ps"
echo "📜 Loglar için: docker-compose logs -f"
