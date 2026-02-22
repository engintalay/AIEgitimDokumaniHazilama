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
            
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"VectorDB query error (likely empty $or match): {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_collection_count(self) -> int:
        """Return total document count in collection."""
        return self.collection.count()

    def get_unique_sources(self, user_id: Optional[int] = None, is_admin: bool = False) -> List[Dict[str, Any]]:
        """Return list of unique source filenames. Admins see all."""
        where = None
        if not is_admin and user_id is not None:
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
                            "is_owner": m.get('user_id') == user_id if user_id else False
                        }
        return sorted(list(sources_map.values()), key=lambda x: x['name'])

    def delete_by_source(self, source: str, user_id: int, is_admin: bool = False):
        """Delete documents. Admins can delete anything."""
        if is_admin:
            where = {"source": source}
        else:
            where = {"$and": [
                {"source": source},
                {"user_id": user_id}
            ]}
        self.collection.delete(where=where)

    def update_visibility(self, source: str, user_id: int, is_public: bool, is_admin: bool = False):
        """Update is_public status. Admins can override."""
        if is_admin:
            where = {"source": source}
        else:
            where = {"$and": [
                {"source": source},
                {"user_id": user_id}
            ]}
            
        data = self.collection.get(where=where, include=['metadatas'])
        
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

    def get_documents_with_metadata(self, limit: int = 100, offset: int = 0, where: Dict = None) -> Dict[str, Any]:
        """Retrieve documents, IDs and metadatas with optional filtering."""
        return self.collection.get(
            limit=limit,
            offset=offset,
            where=where,
            include=['documents', 'metadatas']
        )

    def reset(self):
        """Clear all documents in the collection."""
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.create_collection(name=name)
