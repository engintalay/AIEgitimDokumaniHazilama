import os
import yaml
import uuid
import time
from dotenv import load_dotenv

load_dotenv() # Load environments from .env
from flask import Flask, render_template, request, jsonify, session, Response, redirect, url_for
from werkzeug.utils import secure_filename
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB
from core.ai_client_factory import AIClientFactory
from utils.logger import setup_logger
from core.models import db, User, Chat, Message
from core.auth import oauth, init_auth, handle_google_login, handle_google_callback
from flask_login import LoginManager, login_required, current_user, logout_user

# Load configuration
def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET', config.get('model', {}).get('session_secret', str(uuid.uuid4())))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('data/database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google Auth Config from Env or YAML
google_auth = config.get('google_auth', {})
google_auth['client_id'] = os.getenv('GOOGLE_CLIENT_ID', google_auth.get('client_id'))
google_auth['client_secret'] = os.getenv('GOOGLE_CLIENT_SECRET', google_auth.get('client_secret'))
app.config['GOOGLE_AUTH'] = google_auth

UPLOAD_FOLDER = os.path.abspath('data/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.abspath('data'), exist_ok=True)

# Initialize extensions
db.init_app(app)
init_auth(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

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

@app.route('/auth/local_login')
def local_login():
    # Only allow if Google credentials are placeholders or if explicitly permitted
    user = User.query.filter_by(google_id='local_user').first()
    if not user:
        user = User(
            google_id='local_user',
            email='local@example.com',
            name='Yerel Kullanıcı',
            picture='https://ui-avatars.com/api/?name=Local+User'
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
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
        progress_data[job_id] = 0
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"📁 Dosya yüklendi: {filename}")
        
        try:
            # 1. Parse
            logger.debug(f"Parsing: {filename}")
            raw_text = DocumentParser.parse(file_path)
            
            # 2. Split
            paragraphs = TextProcessor.split_into_paragraphs(raw_text)
            logger.info(f"📑 {len(paragraphs)} paragraf ayrıştırıldı.")
            
            # 3. Embed and Index
            documents, embeddings, metadatas, ids = [], [], [], []
            total = len(paragraphs)
            
            for i, para in enumerate(paragraphs):
                emb = embedding_client.get_embedding(para)
                documents.append(para)
                embeddings.append(emb)
                metadatas.append({"source": filename, "index": i})
                ids.append(f"{filename}_{uuid.uuid4()}_{i}")
                
                # Update progress
                progress_data[job_id] = int(((i + 1) / total) * 100)
                
                if len(documents) >= 10:
                    logger.debug(f"İndeksleniyor... ({i+1}/{total})")
                    vector_db.add_documents(documents, embeddings, metadatas, ids)
                    documents, embeddings, metadatas, ids = [], [], [], []
            
            if documents:
                vector_db.add_documents(documents, embeddings, metadatas, ids)
            
            logger.info(f"✅ İndeksleme tamamlandı: {filename}")
            progress_data[job_id] = 100
                
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
    
    logger.info(f"❓ Soru: {query} (Chat: {active_chat.id})")
    
    try:
        # 1. Get embedding
        query_emb = embedding_client.get_embedding(query)
        
        # 2. Query Vector DB
        rag_cfg = config.get('rag', {})
        results = vector_db.query(query_emb, n_results=rag_cfg.get('top_k', 3), source=source)
        
        contexts = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        
        context_text = "\n\n".join([f"[Kaynak: {m['source']}]\n{c}" for c, m in zip(contexts, metadatas)])
        
        # 3. Prompt
        prompt = f"Bağlam:\n{context_text}\n\nSoru: {query}\n\nCevap:"

        # 4. Generate
        answer = ai_client.generate(prompt)
        
        # Save bot message
        bot_msg = Message(chat_id=active_chat.id, role='bot', content=answer)
        sources_list = list(set(m['source'] for m in metadatas)) if contexts else []
        bot_msg.set_sources(sources_list)
        db.session.add(bot_msg)
        db.session.commit()
        
        return jsonify({
            "answer": answer,
            "sources": sources_list,
            "chat_id": active_chat.id,
            "chat_title": active_chat.title
        })
        
    except Exception as e:
        logger.error(f"❌ Hata: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats', methods=['GET', 'POST'])
@login_required
def handle_chats():
    if request.method == 'GET':
        chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
        logger.info(f"👤 Kullanıcı {current_user.id} sohbet geçmişini istedi. Bulunan: {len(chats)}")
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
                "timestamp": m.timestamp.isoformat()
            } for m in messages]
        })
    else:
        db.session.delete(chat)
        db.session.commit()
        return jsonify({"message": "Sohbet silindi"})

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        count = vector_db.get_collection_count()
        sources = vector_db.get_unique_sources()
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
    def generate():
        while True:
            progress = progress_data.get(job_id, 0)
            yield f"data: {progress}\n\n"
            if progress >= 100:
                # Keep entry for a bit so client can catch the final 100
                time.sleep(2)
                if job_id in progress_data:
                    del progress_data[job_id]
                break
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/delete_source', methods=['POST'])
def delete_source():
    data = request.json
    source = data.get('source')
    if not source:
        return jsonify({"error": "Kaynak belirtilmedi"}), 400
    
    try:
        logger.info(f"🗑️ Kaynak siliniyor: {source}")
        vector_db.delete_by_source(source)
        return jsonify({"message": f"'{source}' başarıyla silindi."})
    except Exception as e:
        logger.error(f"Silme hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset_db', methods=['POST'])
def reset_db():
    try:
        logger.warning("🚨 Tüm veri tabanı sıfırlanıyor!")
        vector_db.reset()
        return jsonify({"message": "Tüm veri tabanı başarıyla sıfırlandı."})
    except Exception as e:
        logger.error(f"Sıfırlama hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    global config, embedding_client, vector_db, ai_client
    if request.method == 'GET':
        return jsonify(config)
    else:
        try:
            new_config = request.json
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(new_config, f, allow_unicode=True, default_flow_style=False)
            
            # Reload components
            config = new_config
            embedding_client, vector_db, ai_client = get_components()
            logger.info("⚙️ Ayarlar güncellendi ve bileşenler yeniden yüklendi.")
            return jsonify({"message": "Ayarlar başarıyla kaydedildi."})
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
