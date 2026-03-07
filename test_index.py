from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB
import uuid, yaml, os
from dotenv import load_dotenv

load_dotenv()
with open('config/config.yaml', 'r', encoding='utf-8') as f: config = yaml.safe_load(f)

ec = EmbeddingClient(provider=config['rag']['embedding_provider'], endpoint=config['rag']['embedding_endpoint'], model=config['rag']['embedding_model'], api_key=config['rag']['embedding_api_key'])
db = VectorDB(db_path=config['rag']['db_path'], collection_name=config['rag']['collection_name'])

filename = "1.3.6183.pdf"
file_path = f"data/uploads/{filename}"

raw_text = DocumentParser.parse(file_path)
paragraphs = TextProcessor.split_into_paragraphs(raw_text)
print(f"Extracted {len(paragraphs)} paragraphs")

docs, embs, metas, ids = [], [], [], []
for i, para in enumerate(paragraphs):
    try:
        emb = ec.get_embedding(para)
    except Exception as e:
        print("Embedding failed:", e)
        break
    
    docs.append(para)
    embs.append(emb)
    metas.append({"source": filename, "index": i, "user_id": 1, "is_public": False})
    ids.append(f"{filename}_{uuid.uuid4()}_{i}")
    
    if len(docs) >= 10:
        print(f"Adding batch at {i+1}...")
        try:
            db.add_documents(docs, embs, metas, ids)
            docs, embs, metas, ids = [], [], [], []
        except Exception as e:
            import traceback
            traceback.print_exc()
            break

if docs:
    try:
        db.add_documents(docs, embs, metas, ids)
    except Exception as e:
        import traceback
        traceback.print_exc()
        
print("Done")
