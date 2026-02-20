#!/bin/bash

# AI Eğitim Dokümanı Hazırlama - Prod Kurulum Betiği (Bare Metal)

PROJECT_DIR="/home/engin/projects/AIEgitimDokumaniHazilama"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Prod kurulumu başlatılıyor..."

# 1. Sistem paketlerini güncelle ve gerekli araçları kur
echo "📦 Sistem paketleri kuruluyor..."
sudo apt update
sudo apt install -y nginx python3-venv build-essential

# 2. Virtual env kontrolü ve kurulumu
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Virtual environment oluşturuluyor..."
    python3 -m venv "$VENV_DIR"
fi

echo "📥 Python bağımlılıkları yükleniyor..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
"$VENV_DIR/bin/pip" install gunicorn

# 3. Klasör izinlerini ayarla
echo "🔐 Klasör izinleri düzenleniyor..."
chmod o+x /home/engin
mkdir -p "$PROJECT_DIR/data/logs" "$PROJECT_DIR/data/uploads"
chmod -R 755 "$PROJECT_DIR/static"

# 4. Systemd servisini kopyala ve aktif et
echo "⚙️ Systemd servisi yapılandırılıyor..."
sudo cp "$PROJECT_DIR/ai_app.service" /etc/systemd/system/ai_app.service
sudo systemctl daemon-reload
sudo systemctl start ai_app
sudo systemctl enable ai_app

# 5. Nginx yapılandırmasını kopyala ve aktif et
echo "🌐 Nginx yapılandırılıyor..."
sudo cp "$PROJECT_DIR/nginx_site.conf" /etc/nginx/sites-available/ai_app
sudo ln -sf /etc/nginx/sites-available/ai_app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "✅ Kurulum tamamlandı!"
echo "🔍 Uygulama durumu: sudo systemctl status ai_app"
echo "🌐 Uygulama şu an 81 portunda yayında."
