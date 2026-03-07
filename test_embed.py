from core.embedding_client import EmbeddingClient
import yaml

with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

rag_cfg = config.get('rag', {})
embedding_client = EmbeddingClient(
    provider=rag_cfg.get('embedding_provider', 'ollama'),
    endpoint=rag_cfg.get('embedding_endpoint', 'http://127.0.0.1:11434'),
    model=rag_cfg.get('embedding_model', 'nomic-embed-text'),
    api_key=rag_cfg.get('embedding_api_key', '')
)

try:
    emb = embedding_client.get_embedding("test")
    print("Success: embedding length", len(emb))
except Exception as e:
    import traceback
    traceback.print_exc()

