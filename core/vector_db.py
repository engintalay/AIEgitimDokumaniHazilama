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

    def query(self, query_embedding: List[float], n_results: int = 3, source: Optional[str] = None) -> Dict[str, Any]:
        """Search for most similar documents with optional source filtering."""
        where = {"source": source} if source else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        return results

    def get_collection_count(self) -> int:
        """Return total document count in collection."""
        return self.collection.count()

    def get_unique_sources(self) -> List[str]:
        """Return list of unique source filenames in the DB."""
        data = self.collection.get(include=['metadatas'])
        sources = set()
        if data and data['metadatas']:
            for m in data['metadatas']:
                if m and 'source' in m:
                    sources.add(m['source'])
        return sorted(list(sources))

    def delete_by_source(self, source: str):
        """Delete all documents associated with a specific source."""
        self.collection.delete(where={"source": source})

    def reset(self):
        """Clear all documents in the collection."""
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.create_collection(name=name)
