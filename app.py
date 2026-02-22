import os
import yaml
import uuid
import time
from dotenv import load_dotenv

from werkzeug.middleware.proxy_fix import ProxyFix
load_dotenv()
import logging
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, Response
import json
from werkzeug.utils import secure_filename
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB
from core.ai_client_factory import AIClientFactory
from utils.logger import setup_logger
from core.models import db, User, Chat, Message, Report, ReportMessage
from core.auth import oauth, init_auth, handle_google_login, handle_google_callback
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
from functools import wraps

# Load configuration
def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.secret_key = os.getenv('SESSION_SECRET', config.get('model', {}).get('session_secret', str(uuid.uuid4())))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('data/database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google Auth Config from Env or YAML
google_auth = config.get('google_auth', {})
google_auth['client_id'] = os.getenv('GOOGLE_CLIENT_ID', google_auth.get('client_id'))
google_auth['client_secret'] = os.getenv('GOOGLE_CLIENT_SECRET', google_auth.get('client_secret'))
google_auth['redirect_uri'] = os.getenv('GOOGLE_REDIRECT_URI', google_auth.get('redirect_uri'))
app.config['GOOGLE_AUTH'] = google_auth

# Ensure upload and data directories exist
os.makedirs('data/uploads', exist_ok=True)
os.makedirs('data/reports', exist_ok=True)
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['REPORT_FOLDER'] = 'data/reports'

# Initialize extensions
db.init_app(app)
init_auth(app)

# JSON Turkish Character Fix
app.json.ensure_ascii = False 

login_manager = LoginManager()
login_manager.init_app(app)

@app.after_request
def add_header(response):
    if response.mimetype == 'application/javascript' or response.mimetype == 'application/json':
        response.charset = 'utf-8'
    return response
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            return "Bu alan sadece admin yetkisine sahip kullanıcılar içindir.", 403
        return f(*args, **kwargs)
    return decorated_function

# Progress tracking

# Progress tracking
progress_data = {}

# Setup Logger
log_cfg = config.get('logging', {})
logger = setup_logger(
    name="web_app",
    level=log_cfg.get('level', 'DEBUG'),
    log_file=log_cfg.get('file', './data/logs/app.log'),
    console=log_cfg.get('console', True)
)

# Initialize Backend Components
def get_components():
    rag_cfg = config.get('rag', {})
    model_cfg = config.get('model', {})
    
    embedding_client = EmbeddingClient(
        provider=model_cfg.get('type', 'ollama'),
        endpoint=model_cfg.get('endpoint', 'http://127.0.0.1:11434'),
        model=rag_cfg.get('embedding_model', 'nomic-embed-text'),
        api_key=model_cfg.get('api_key', '')
    )
    
    vector_db = VectorDB(
        db_path=rag_cfg.get('db_path', './data/vector_db'),
        collection_name=rag_cfg.get('collection_name', 'training_docs')
    )
    
    ai_client = AIClientFactory.create(model_cfg)
    
    return embedding_client, vector_db, ai_client

embedding_client, vector_db, ai_client = get_components()

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    return render_template('index.html')

@app.route('/login')
def login():
    return handle_google_login()

@app.route('/auth/callback')
def auth_callback():
    if handle_google_callback():
        return redirect(url_for('index'))
    return "Giriş başarısız", 400

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Dosya bulunamadı"}), 400
    
    job_id = request.form.get('job_id')
    if not job_id:
        return jsonify({"error": "Job ID bulunamadı"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Dosya seçilmedi"}), 400
    
    if file:
        progress_data[job_id] = {"progress": 0, "status": "Dosya sunucuya alındı, işleme başlanıyor..."}
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"📁 Dosya yüklendi: {filename} (Kullanıcı: {current_user.name})")
        
        try:
            # 1. Parse
            logger.info(f"📑 {filename} okunuyor ve metin ayrıştırılıyor...")
            progress_data[job_id] = {"progress": 5, "status": "Doküman içerisindeki metinler çıkarılıyor..."}
            raw_text = DocumentParser.parse(file_path)
            
            # 2. Split
            logger.info(f"📑 {filename} paragraflara bölünüyor...")
            progress_data[job_id] = {"progress": 10, "status": "Metinler küçük paragraflara ayrıştırılıyor..."}
            paragraphs = TextProcessor.split_into_paragraphs(raw_text)
            logger.info(f"📑 {len(paragraphs)} paragraf başarıyla ayrıştırıldı.")
            
            # 3. Embed and Index
            documents, embeddings, metadatas, ids = [], [], [], []
            total = len(paragraphs)
            
            for i, para in enumerate(paragraphs):
                emb = embedding_client.get_embedding(para)
                documents.append(para)
                embeddings.append(emb)
                metadatas.append({
                    "source": filename, 
                    "index": i, 
                    "user_id": current_user.id,
                    "is_public": False
                })
                ids.append(f"{filename}_{uuid.uuid4()}_{i}")
                
                # Update progress
                current_percent = 10 + int(((i + 1) / total) * 90)
                status_msg = f"Vektörleştiriliyor ve İndeksleniyor... ({i+1}/{total})"
                progress_data[job_id] = {"progress": current_percent, "status": status_msg}
                
                if len(documents) >= 10:
                    logger.info(f"İndeksleniyor... ({i+1}/{total})")
                    vector_db.add_documents(documents, embeddings, metadatas, ids)
                    documents, embeddings, metadatas, ids = [], [], [], []
            
            if documents:
                vector_db.add_documents(documents, embeddings, metadatas, ids)
            
            logger.info(f"✅ İndeksleme tamamlandı: {filename}")
            progress_data[job_id] = {"progress": 100, "status": "İşlem tamamlandı!"}
                
            return jsonify({
                "message": f"'{filename}' başarıyla yüklendi ve {len(paragraphs)} paragraf indekslendi.",
                "filename": filename,
                "count": len(paragraphs)
            })
            
        except Exception as e:
            return jsonify({"error": f"İşlem hatası: {str(e)}"}), 500

@app.route('/ask', methods=['POST'])
@login_required
def ask_question():
    data = request.json
    query = data.get('query')
    source = data.get('source')
    chat_id = data.get('chat_id')
    
    if not query:
        return jsonify({"error": "Soru boş olamaz"}), 400
    
    # Ensure chat belongs to user or create a new one
    active_chat = None
    if chat_id:
        active_chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    
    if not active_chat:
        active_chat = Chat(user_id=current_user.id, title=query[:30] + "...")
        db.session.add(active_chat)
        db.session.commit()
    
    # Save user message
    user_msg = Message(chat_id=active_chat.id, role='user', content=query)
    db.session.add(user_msg)
    
    logger.info(f"❓ Soru: {query} (Kullanıcı: {current_user.name}, Chat: {active_chat.id})")
    
    try:
        # 1. Get embedding
        query_emb = embedding_client.get_embedding(query)
        
        # 2. Query Vector DB
        rag_cfg = config.get('rag', {})
        results = vector_db.query(query_emb, n_results=rag_cfg.get('top_k', 3), user_id=current_user.id, source=source)
        
        contexts = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        
        context_text = "\n\n".join([f"[Kaynak: {m['source']}]\n{c}" for c, m in zip(contexts, metadatas)])
        
        # 2.5 Retrieve Chat History (last 5 messages)
        history_msgs = Message.query.filter_by(chat_id=active_chat.id).order_by(Message.timestamp.desc()).offset(1).limit(5).all()
        history_msgs.reverse()
        history_text = "\n".join([f"{'Kullanıcı' if m.role == 'user' else 'Asistan'}: {m.content}" for m in history_msgs])
        
        # 3. Prompt
        prompt = "Sen yardımcı bir doküman asistanısın. Aşağıdaki bağlam ve geçmiş konuşmaları dikkate alarak son soruyu cevapla.\n\n"
        if history_text:
            prompt += f"--- Önceki Yazışmalar ---\n{history_text}\n\n"
        
        prompt += f"--- İlgili Doküman Parçaları ---\n{context_text}\n\n"
        prompt += f"Soru: {query}\n\nCevap:"

        # 4. Generate with user-specific settings if available
        user_settings = json.loads(current_user.settings) if current_user.settings else {}
        model_overrides = user_settings.get('model', {})
        
        start_time = time.time()
        try:
            # We pass model options to support per-user settings
            result_data = ai_client.generate(prompt, options=model_overrides) 
        except Exception as e:
            logger.warning(f"User model generation failed ({str(e)}), falling back to system default settings.")
            # Fallback to default properties by ignoring user overrides
            result_data = ai_client.generate(prompt)
            
        generation_time = time.time() - start_time
        
        answer = result_data['text']
        usage = result_data.get('usage', {})
        
        # Save bot message
        bot_msg = Message(
            chat_id=active_chat.id, 
            role='bot', 
            content=answer,
            response_time=generation_time,
            prompt_tokens=usage.get('prompt_tokens', 0),
            completion_tokens=usage.get('completion_tokens', 0)
        )
        sources_list = list(set(m['source'] for m in metadatas)) if contexts else []
        bot_msg.set_sources(sources_list)
        db.session.add(bot_msg)
        db.session.commit()
        
        return jsonify({
            "answer": answer,
            "sources": sources_list,
            "chat_id": active_chat.id,
            "chat_title": active_chat.title,
            "message_id": bot_msg.id,
            "stats": {
                "time": round(generation_time, 2),
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Hata: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats', methods=['GET', 'POST'])
@login_required
def handle_chats():
    if request.method == 'GET':
        chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
        logger.info(f"👤 Kullanıcı '{current_user.name}' sohbet geçmişini istedi. Bulunan: {len(chats)}")
        return jsonify([{
            "id": c.id,
            "title": c.title,
            "updated_at": c.updated_at.isoformat()
        } for c in chats])
    else:
        # Create new chat
        new_chat = Chat(user_id=current_user.id)
        db.session.add(new_chat)
        db.session.commit()
        return jsonify({"id": new_chat.id, "title": new_chat.title})

@app.route('/chats/<int:chat_id>', methods=['GET', 'DELETE'])
@login_required
def chat_detail(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    if request.method == 'GET':
        messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.asc()).all()
        return jsonify({
            "id": chat.id,
            "title": chat.title,
            "messages": [{
                "role": m.role,
                "content": m.content,
                "sources": m.get_sources(),
                "timestamp": m.timestamp.isoformat(),
                "id": m.id,
                "stats": {
                    "time": round(m.response_time, 2) if m.response_time else None,
                    "prompt_tokens": m.prompt_tokens,
                    "completion_tokens": m.completion_tokens
                } if m.role == 'bot' else None
            } for m in messages]
        })
    else:
        db.session.delete(chat)
        db.session.commit()
        return jsonify({"message": "Sohbet silindi"})

@app.route('/stats')
@login_required
def get_stats():
    try:
        is_admin = getattr(current_user, 'is_admin', False)
        # Check if requesting stats for a specific user (admin only)
        target_user_id = request.args.get('user_id', type=int)
        
        if target_user_id and is_admin:
            query_user_id = target_user_id
        else:
            query_user_id = current_user.id
            
        count = vector_db.get_collection_count()
        sources = vector_db.get_unique_sources(user_id=query_user_id, is_admin=is_admin and not target_user_id)
        
        # If target_user_id is set, filter to only their sources
        if target_user_id and is_admin:
            sources = [s for s in sources if s.get('user_id') == target_user_id]

        return jsonify({
            "count": count,
            "sources": sources,
            "collection": config.get('rag', {}).get('collection_name', 'training_docs')
        })
    except Exception as e:
        logger.error(f"Stats hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/progress/<job_id>')
def get_progress(job_id):
    data = progress_data.get(job_id, {"progress": 0, "status": ""})
    if isinstance(data, int): # backward compatibility for safety
        data = {"progress": data, "status": "İşleniyor..."}
    # Frontend will stop polling when it sees 100.
    return jsonify(data)

@app.route('/delete_source', methods=['POST'])
@login_required
def delete_source():
    data = request.json
    source = data.get('source')
    if not source:
        return jsonify({"error": "Kaynak belirtilmedi"}), 400
    
    try:
        is_admin = getattr(current_user, 'is_admin', False)
        logger.info(f"🗑️ Kaynak siliniyor: {source} (User: {current_user.id}, Admin: {is_admin})")
        vector_db.delete_by_source(source, user_id=current_user.id, is_admin=is_admin)
        return jsonify({"message": f"'{source}' başarıyla silindi."})
    except Exception as e:
        logger.error(f"Silme hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset_db', methods=['POST'])
@login_required
def reset_db():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({"error": "Bu işlem için yetkiniz yok (Yalnızca Admin)."}), 403
        
    try:
        logger.warning(f"🚨 Tüm veri tabanı sıfırlanıyor! (Admin: {current_user.id})")
        vector_db.reset()
        return jsonify({"message": "Tüm veri tabanı başarıyla sıfırlandı."})
    except Exception as e:
        logger.error(f"Sıfırlama hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/toggle_public', methods=['POST'])
@login_required
def toggle_public():
    data = request.json
    source = data.get('source')
    is_public = data.get('is_public', False)
    
    if not source:
        return jsonify({"error": "Kaynak belirtilmedi"}), 400
        
    try:
        is_admin = getattr(current_user, 'is_admin', False)
        success = vector_db.update_visibility(source, current_user.id, is_public, is_admin=is_admin)
        if success:
            status = "artık genel" if is_public else "artık özel"
            return jsonify({"message": f"'{source}' {status}."})
        else:
            return jsonify({"error": "Kaynak bulunamadı veya yetkiniz yok"}), 403
    except Exception as e:
        logger.error(f"Görünürlük güncelleme hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
@login_required
def handle_config():
    global config # We still use global for defaults
    if request.method == 'GET':
        user_settings = json.loads(current_user.settings) if current_user.settings else {}
        # Merge user settings into global config for the UI
        full_cfg = config.copy()
        if 'model' in user_settings:
            full_cfg['model'].update(user_settings['model'])
        return jsonify(full_cfg)
    else:
        try:
            new_settings = request.json
            # We only store the 'model' part as user-specific for now
            current_user.settings = json.dumps({
                "model": new_settings.get('model', {})
            })
            db.session.commit()
            
            logger.info(f"⚙️ Kullanıcı '{current_user.name}' ayarları güncellendi.")
            return jsonify({"message": "Kişisel ayarlarınız başarıyla kaydedildi."})
        except Exception as e:
            logger.error(f"Config kaydetme hatası: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/available_models', methods=['GET'])
def get_available_models():
    try:
        models = ai_client.get_available_models()
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"models": []})

# --- Admin Routes ---

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/users.html')

@app.route('/admin/users_data')
@login_required
@admin_required
def admin_users_data():
    users = User.query.all()
    user_list = []
    for u in users:
        chat_count = Chat.query.filter_by(user_id=u.id).count()
        user_list.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "picture": u.picture,
            "chat_count": chat_count,
            "is_admin": u.is_admin
        })
    return jsonify(user_list)

@app.route('/admin/user/<int:user_id>/chats')
@login_required
@admin_required
def admin_view_user_chats(user_id):
    target_user = User.query.get_or_404(user_id)
    return render_template('admin/chats.html', target_user=target_user)

@app.route('/admin/user/<int:user_id>/chats_data')
@login_required
@admin_required
def admin_user_chats_data(user_id):
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated_at.desc()).all()
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "updated_at": c.updated_at.isoformat(),
        "message_count": Message.query.filter_by(chat_id=c.id).count()
    } for c in chats])

@app.route('/admin/chat/<int:chat_id>/messages')
@login_required
@admin_required
def admin_view_messages(chat_id):
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()
    return jsonify([{
        "role": m.role,
        "content": m.content,
        "timestamp": m.timestamp.isoformat(),
        "sources": m.get_sources(),
        "stats": {
            "time": round(m.response_time, 2) if m.response_time else None,
            "prompt_tokens": m.prompt_tokens,
            "completion_tokens": m.completion_tokens
        } if m.role == 'bot' else None
    } for m in messages])

@app.route('/admin/user/<int:user_id>/sources')
@login_required
@admin_required
def admin_view_user_sources(user_id):
    target_user = User.query.get_or_404(user_id)
    return render_template('admin/sources.html', target_user=target_user)

@app.route('/report', methods=['POST'])
@login_required
def submit_report():
    content = request.form.get('content')
    message_id = request.form.get('message_id')
    image = request.files.get('image')
    
    if not content:
        return jsonify({"error": "Rapor içeriği boş olamaz"}), 400
        
    try:
        report = Report(
            user_id=current_user.id,
            message_id=message_id,
            content=content
        )
        
        if image:
            filename = f"report_{current_user.id}_{int(time.time())}.{image.filename.split('.')[-1]}"
            img_path = os.path.join(app.config['REPORT_FOLDER'], filename)
            image.save(img_path)
            report.image_path = filename

        db.session.add(report)
        db.session.commit()
        return jsonify({"message": "Raporunuz başarıyla iletildi. Teşekkür ederiz!"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Report error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/my_reports')
@login_required
def my_reports():
    return render_template('reports/my_reports.html')

@app.route('/my_reports_data')
@login_required
def my_reports_data():
    from sqlalchemy.orm import joinedload
    reports = Report.query.options(joinedload(Report.report_messages)).filter_by(user_id=current_user.id).order_by(Report.updated_at.desc(), Report.timestamp.desc()).all()
    return jsonify([{
        "id": r.id,
        "content": r.content,
        "image_path": r.image_path,
        "status": r.status,
        "timestamp": r.timestamp.isoformat(),
        "updated_at": r.updated_at.isoformat() if r.updated_at else r.timestamp.isoformat(),
        "message_id": r.message_id,
        "reply_count": len(r.report_messages)
    } for r in reports])

@app.route('/my_reports/<int:report_id>')
@login_required
def my_report_detail(report_id):
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    return render_template('reports/ticket_detail.html', report=report, is_admin=False)

@app.route('/my_reports/<int:report_id>/reply', methods=['POST'])
@login_required
def my_report_reply(report_id):
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    
    if report.status == 'closed':
         return jsonify({"error": "Kapanmış bir talebe cevap yazılamaz."}), 400
         
    content = request.json.get('content')
    if not content:
         return jsonify({"error": "Mesaj boş olamaz."}), 400
         
    reply = ReportMessage(
        report_id=report.id,
        user_id=current_user.id,
        content=content
    )
    
    # User replying automatically puts it back to pending/open state for admin
    if report.status in ['resolved']:
        report.status = 'pending'
    
    db.session.add(reply)
    db.session.commit()
    
    return jsonify({
        "message": "Cevap başarıyla iletildi.",
        "reply": {
            "id": reply.id,
            "user_name": current_user.name,
            "content": reply.content,
            "timestamp": reply.timestamp.isoformat(),
            "is_admin": False
        },
        "status": report.status
    })

@app.route('/admin/reports/image/<filename>')
@login_required
def get_report_image(filename):
    return send_from_directory(app.config['REPORT_FOLDER'], filename)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    return render_template('admin/reports.html')

@app.route('/admin/reports_data')
@login_required
@admin_required
def admin_reports_data():
    from sqlalchemy.orm import joinedload
    reports = Report.query.options(joinedload(Report.report_messages)).order_by(Report.updated_at.desc(), Report.timestamp.desc()).all()
    return jsonify([{
        "id": r.id,
        "user_name": r.user_rel.name,
        "user_email": r.user_rel.email,
        "content": r.content,
        "image_path": r.image_path,
        "status": r.status,
        "timestamp": r.timestamp.isoformat(),
        "updated_at": r.updated_at.isoformat() if r.updated_at else r.timestamp.isoformat(),
        "message_id": r.message_id,
        "reply_count": len(r.report_messages)
    } for r in reports])

@app.route('/admin/reports/<int:report_id>')
@login_required
@admin_required
def admin_report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    return render_template('reports/ticket_detail.html', report=report, is_admin=True)

@app.route('/admin/reports/<int:report_id>/reply', methods=['POST'])
@login_required
@admin_required
def admin_report_reply(report_id):
    report = Report.query.get_or_404(report_id)
    content = request.json.get('content')
    
    if not content:
         return jsonify({"error": "Mesaj boş olamaz."}), 400
         
    # Optional status update from the admin
    new_status = request.json.get('status')
    if new_status in ['pending', 'investigating', 'resolved', 'closed']:
        report.status = new_status
         
    reply = ReportMessage(
        report_id=report.id,
        user_id=current_user.id,
        content=content
    )
    
    db.session.add(reply)
    db.session.commit()
    
    return jsonify({
        "message": "Cevap başarıyla eklendi.",
        "reply": {
            "id": reply.id,
            "user_name": current_user.name,
            "content": reply.content,
            "timestamp": reply.timestamp.isoformat(),
            "is_admin": True
        },
        "status": report.status
    })

@app.route('/admin/vector_explorer')
@login_required
@admin_required
def admin_vector_explorer():
    return render_template('admin/vector_explorer.html')

@app.route('/admin/vector_data')
@login_required
@admin_required
def admin_vector_data():
    source = request.args.get('source')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    where = None
    if source:
        where = {"source": source}
        
    try:
        data = vector_db.get_documents_with_metadata(limit=limit, offset=offset, where=where)
        results = []
        if data and data['ids']:
            for i in range(len(data['ids'])):
                results.append({
                    "id": data['ids'][i],
                    "content": data['documents'][i],
                    "metadata": data['metadatas'][i]
                })
        return jsonify({
            "total": vector_db.get_collection_count(),
            "results": results,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        logger.error(f"Vector data error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/vector_search', methods=['POST'])
@login_required
@admin_required
def admin_vector_search():
    data = request.json
    query = data.get('query')
    source = data.get('source')
    n_results = data.get('n_results', 5)
    
    if not query:
        return jsonify({"error": "Sorgu boş olamaz"}), 400
        
    try:
        query_emb = embedding_client.get_embedding(query)
        # Search without user_id filter to see all results
        search_results = vector_db.query(query_emb, n_results=n_results, source=source)
        
        results = []
        if search_results and search_results['ids']:
            ids = search_results['ids'][0]
            docs = search_results['documents'][0]
            metas = search_results['metadatas'][0]
            distances = search_results['distances'][0] if 'distances' in search_results else [0] * len(ids)
            
            for i in range(len(ids)):
                results.append({
                    "id": ids[i],
                    "content": docs[i],
                    "metadata": metas[i],
                    "score": round(1 - distances[i], 4) if distances[i] <= 1 else 0
                })
                
        return jsonify({"results": results})
    except Exception as e:
        logger.error(f"Vector search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/reports/<int:report_id>/resolve', methods=['POST'])
@login_required
@admin_required
def admin_resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = "resolved"
    db.session.commit()
    return jsonify({"message": "Rapor çözüldü olarak işaretlendi."})

@app.route('/admin/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_role(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "Kendi yetkinizi değiştiremezsiniz."}), 400
        
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({"message": f"Kullanıcı artık {'Admin' if user.is_admin else 'Standart'} yetkisine sahip."})

if __name__ == '__main__':
    # Use environment variables for production behavior
    is_prod = os.getenv('FLASK_ENV') == 'production'
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=not is_prod
    )
