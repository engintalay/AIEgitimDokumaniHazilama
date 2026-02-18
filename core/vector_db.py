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

    def query(self, query_embedding: List[float], n_results: int = 3, user_id: Optional[int] = None, source: Optional[str] = None) -> Dict[str, Any]:
        """Search for most similar documents with ownership and optional source filtering."""
        filters = []
        
        # Ownership/Public Filter
        if user_id is not None:
            filters.append({"$or": [
                {"user_id": user_id},
                {"is_public": True}
            ]})
        
        # Source Filter
        if source:
            filters.append({"source": source})
            
        # Combine filters
        if len(filters) == 1:
            where = filters[0]
        elif len(filters) > 1:
            where = {"$and": filters}
        else:
            where = None
            
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        return results

    def get_collection_count(self) -> int:
        """Return total document count in collection."""
        return self.collection.count()

    def get_unique_sources(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return list of unique source filenames with their metadata (owner, shared status)."""
        where = None
        if user_id is not None:
             where = {"$or": [
                {"user_id": user_id},
                {"is_public": True}
            ]}
             
        data = self.collection.get(include=['metadatas'], where=where)
        sources_map = {}
        if data and data['metadatas']:
            for m in data['metadatas']:
                if m and 'source' in m:
                    src = m['source']
                    if src not in sources_map:
                        sources_map[src] = {
                            "name": src,
                            "user_id": m.get('user_id'),
                            "is_public": m.get('is_public', False),
                            "is_owner": m.get('user_id') == user_id
                        }
        return sorted(list(sources_map.values()), key=lambda x: x['name'])

    def delete_by_source(self, source: str, user_id: int):
        """Delete documents associated with a source only if current user is owner."""
        # Note: We must ensure user_id matches to prevent unauthorized deletions
        self.collection.delete(where={"$and": [
            {"source": source},
            {"user_id": user_id}
        ]})

    def update_visibility(self, source: str, user_id: int, is_public: bool):
        """Update is_public status for all documents of a source owned by user."""
        # ChromaDB doesn't have a direct "update metadata by where" easily in some versions.
        # We might need to get all IDs and update them.
        data = self.collection.get(where={"$and": [
            {"source": source},
            {"user_id": user_id}
        ]}, include=['metadatas'])
        
        if data and data['ids']:
            new_metadatas = []
            for m in data['metadatas']:
                m['is_public'] = is_public
                new_metadatas.append(m)
            
            self.collection.update(
                ids=data['ids'],
                metadatas=new_metadatas
            )
            return True
        return False

    def reset(self):
        """Clear all documents in the collection."""
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.create_collection(name=name)
