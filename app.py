import os
import yaml
import uuid
import time
from flask import Flask, render_template, request, jsonify, session, Response
from werkzeug.utils import secure_filename
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB
from core.ai_client_factory import AIClientFactory
from utils.logger import setup_logger

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
UPLOAD_FOLDER = 'data/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load configuration
def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

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
    
    db = VectorDB(
        db_path=rag_cfg.get('db_path', './data/vector_db'),
        collection_name=rag_cfg.get('collection_name', 'training_docs')
    )
    
    ai_client = AIClientFactory.create(model_cfg)
    
    return embedding_client, db, ai_client

embedding_client, db, ai_client = get_components()

@app.route('/')
def index():
    return render_template('index.html')

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
                    db.add_documents(documents, embeddings, metadatas, ids)
                    documents, embeddings, metadatas, ids = [], [], [], []
            
            if documents:
                db.add_documents(documents, embeddings, metadatas, ids)
            
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
def ask_question():
    data = request.json
    query = data.get('query')
    source = data.get('source') # Optional source filter
    
    if not query:
        return jsonify({"error": "Soru boş olamaz"}), 400
    
    logger.info(f"❓ Soru: {query}" + (f" (Filtre: {source})" if source else ""))
    
    try:
        # 1. Get embedding
        query_emb = embedding_client.get_embedding(query)
        
        # 2. Query Vector DB
        rag_cfg = config.get('rag', {})
        results = db.query(query_emb, n_results=rag_cfg.get('top_k', 3), source=source)
        
        contexts = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        
        logger.debug(f"🔍 {len(contexts)} bağlam bulundu.")
        for idx, (c, m) in enumerate(zip(contexts, metadatas)):
            logger.debug(f"Bağlam {idx+1} ({m['source']}): {c[:100]}...")

        context_text = "\n\n".join([f"[Kaynak: {m['source']}]\n{c}" for c, m in zip(contexts, metadatas)])
        
        # 3. Prompt
        prompt = f"""Bağlam:
{context_text}

Soru: {query}

Cevap:"""

        # 4. Generate
        logger.debug("AI cevabı oluşturuluyor...")
        answer = ai_client.generate(prompt)
        logger.info(f"🤖 Cevap üretildi ({len(answer)} karakter)")
        
        return jsonify({
            "answer": answer,
            "sources": list(set(m['source'] for m in metadatas)) if contexts else []
        })
        
    except Exception as e:
        logger.error(f"❌ Hata: {str(e)}")
        return jsonify({"error": f"Soru işlenirken hata oluştu: {str(e)}"}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        count = db.get_collection_count()
        sources = db.get_unique_sources()
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
        db.delete_by_source(source)
        return jsonify({"message": f"'{source}' başarıyla silindi."})
    except Exception as e:
        logger.error(f"Silme hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset_db', methods=['POST'])
def reset_db():
    try:
        logger.warning("🚨 Tüm veri tabanı sıfırlanıyor!")
        db.reset()
        return jsonify({"message": "Tüm veri tabanı başarıyla sıfırlandı."})
    except Exception as e:
        logger.error(f"Sıfırlama hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
