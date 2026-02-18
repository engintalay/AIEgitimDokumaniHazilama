import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional

class VectorDB:
    """Wrapper for ChromaDB operations."""
    
    def __init__(self, db_path: str = "./data/vector_db", collection_name: str = "training_docs"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Add batch of documents to the collection."""
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_embedding: List[float], n_results: int = 3) -> Dict[str, Any]:
        """Search for most similar documents."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

    def get_collection_count(self) -> int:
        """Return total document count in collection."""
        return self.collection.count()
