import os
import yaml
import argparse
from tqdm import tqdm
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB

def main():
    parser = argparse.ArgumentParser(description='Ingest documents into the vector database.')
    parser.add_argument('--input', required=True, help='Path to the input file or directory')
    parser.add_argument('--config', default='config/config.yaml', help='Path to the config file')
    args = parser.parse_args()

    # Load config
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Initialize components
    embed_cfg = config.get('rag', {})
    model_cfg = config.get('model', {})
    
    # Use model endpoint for embeddings by default if ollama
    provider = model_cfg.get('type', 'ollama')
    endpoint = model_cfg.get('endpoint', 'http://127.0.0.1:11434')
    api_key = model_cfg.get('api_key', '')
    
    embedding_client = EmbeddingClient(
        provider=provider,
        endpoint=endpoint,
        model=embed_cfg.get('embedding_model', 'nomic-embed-text'),
        api_key=api_key
    )
    
    db = VectorDB(
        db_path=embed_cfg.get('db_path', './data/vector_db'),
        collection_name=embed_cfg.get('collection_name', 'training_docs')
    )

    # Resolve input files
    files = []
    if os.path.isfile(args.input):
        files.append(args.input)
    elif os.path.isdir(args.input):
        for f in os.listdir(args.input):
            if f.lower().endswith(('.pdf', '.docx', '.txt')):
                files.append(os.path.join(args.input, f))

    if not files:
        print(f"No valid documents found in {args.input}")
        return

    print(f"Ingesting {len(files)} documents...")

    for file_path in files:
        print(f"Processing: {file_path}")
        try:
            # 1. Parse
            raw_text = DocumentParser.parse(file_path)
            
            # 2. Split into paragraphs
            paragraphs = TextProcessor.split_into_paragraphs(raw_text)
            
            if not paragraphs:
                print(f"No content found in {file_path}")
                continue

            # 3. Generate embeddings and add to DB
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            filename = os.path.basename(file_path)
            
            for i, para in enumerate(tqdm(paragraphs, desc="Generating embeddings")):
                try:
                    emb = embedding_client.get_embedding(para)
                    
                    documents.append(para)
                    embeddings.append(emb)
                    metadatas.append({"source": filename, "index": i})
                    ids.append(f"{filename}_{i}")
                    
                    # Batch add every 10 to avoid too large requests if necessary
                    if len(documents) >= 10:
                        db.add_documents(documents, embeddings, metadatas, ids)
                        documents, embeddings, metadatas, ids = [], [], [], []
                        
                except Exception as e:
                    print(f"\nError generating embedding for paragraph {i}: {str(e)}")
                    continue
            
            # Final batch
            if documents:
                db.add_documents(documents, embeddings, metadatas, ids)
                
            print(f"Finished ingesting {filename}. Total items in DB: {db.get_collection_count()}")
            
        except Exception as e:
            print(f"Failed to process {file_path}: {str(e)}")

if __name__ == "__main__":
    main()
