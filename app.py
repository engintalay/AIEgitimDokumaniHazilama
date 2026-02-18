import os
import yaml
import uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB
from core.ai_client_factory import AIClientFactory

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
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Dosya seçilmedi"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # 1. Parse
            raw_text = DocumentParser.parse(file_path)
            
            # 2. Split
            paragraphs = TextProcessor.split_into_paragraphs(raw_text)
            
            # 3. Embed and Index
            documents, embeddings, metadatas, ids = [], [], [], []
            for i, para in enumerate(paragraphs):
                emb = embedding_client.get_embedding(para)
                documents.append(para)
                embeddings.append(emb)
                metadatas.append({"source": filename, "index": i})
                ids.append(f"{filename}_{uuid.uuid4()}_{i}")
                
                if len(documents) >= 10:
                    db.add_documents(documents, embeddings, metadatas, ids)
                    documents, embeddings, metadatas, ids = [], [], [], []
            
            if documents:
                db.add_documents(documents, embeddings, metadatas, ids)
                
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
    if not query:
        return jsonify({"error": "Soru boş olamaz"}), 400
    
    try:
        # 1. Get embedding
        query_emb = embedding_client.get_embedding(query)
        
        # 2. Query Vector DB
        rag_cfg = config.get('rag', {})
        results = db.query(query_emb, n_results=rag_cfg.get('top_k', 3))
        
        contexts = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        
        context_text = "\n\n".join([f"[Kaynak: {m['source']}]\n{c}" for c, m in zip(contexts, metadatas)])
        
        # 3. Prompt
        prompt = f"""Bağlam:
{context_text}

Soru: {query}

Cevap:"""

        # 4. Generate
        answer = ai_client.generate(prompt)
        
        return jsonify({
            "answer": answer,
            "sources": list(set(m['source'] for m in metadatas)) if contexts else []
        })
        
    except Exception as e:
        return jsonify({"error": f"Soru işlenirken hata oluştu: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
