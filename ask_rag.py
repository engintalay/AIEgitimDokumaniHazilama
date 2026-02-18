import yaml
import argparse
from colorama import Fore, Style, init
from core.embedding_client import EmbeddingClient
from core.vector_db import VectorDB
from core.ai_client_factory import AIClientFactory

init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(description='Ask questions using RAG (Retrieval-Augmented Generation).')
    parser.add_argument('query', help='The question you want to ask')
    parser.add_argument('--config', default='config/config.yaml', help='Path to the config file')
    args = parser.parse_args()

    # Load config
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    rag_cfg = config.get('rag', {})
    model_cfg = config.get('model', {})
    
    # Initialize components
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

    print(f"\n{Fore.CYAN}Searching for relevant context...{Style.RESET_ALL}")
    
    try:
        # 1. Get embedding for query
        query_emb = embedding_client.get_embedding(args.query)
        
        # 2. Query Vector DB
        top_k = rag_cfg.get('top_k', 3)
        results = db.query(query_emb, n_results=top_k)
        
        contexts = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        
        if not contexts:
            print(f"{Fore.YELLOW}No relevant context found. Asking the model directly...{Style.RESET_ALL}")
            context_text = "No context available."
        else:
            print(f"{Fore.GREEN}Found {len(contexts)} relevant paragraphs.{Style.RESET_ALL}")
            context_text = "\n\n".join([f"[Source: {m['source']}]\n{c}" for c, m in zip(contexts, metadatas)])

        # 3. Construct RAG Prompt
        prompt = f"""Aşağıdaki bağlamı (context) kullanarak kullanıcı sorusunu cevapla. 
Bağlamda bilgi yoksa, kendi bilgini kullanabilirsin ama bağlamda bilgi varsa ona sadık kal.

BAĞLAM:
{context_text}

SORU:
{args.query}

CEVAP:"""

        print(f"{Fore.CYAN}Generating answer...{Style.RESET_ALL}\n")
        
        # 4. Get completion
        response = ai_client.generate(prompt)
        
        print(f"{Fore.YELLOW}AI CEVABI:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{response}\n")
        
        if contexts:
            print(f"{Fore.BLUE}--- Kullanılan Kaynaklar ---{Style.RESET_ALL}")
            sources = set(m['source'] for m in metadatas)
            for s in sources:
                print(f"- {s}")

    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}")

if __name__ == "__main__":
    main()
