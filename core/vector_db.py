import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Union

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

    def query(self, query_embedding: List[float], n_results: int = 3, user_id: Optional[int] = None, source: Optional[Union[str, List[str]]] = None, query_text: Optional[str] = None, is_admin: bool = False) -> Dict[str, Any]:
        """Search for most similar documents with ownership and optional source filtering."""
        filters = []
        
        # Ownership/Public Filter - Skip if admin
        if not is_admin and user_id is not None:
            try:
                # Ensure user_id is an integer for ChromaDB compatibility
                uid = int(user_id)
                filters.append({"$or": [
                    {"user_id": uid},
                    {"is_public": True}
                ]})
            except (ValueError, TypeError):
                # If it's truly a string ID or None, pass as is
                filters.append({"$or": [
                    {"user_id": user_id},
                    {"is_public": True}
                ]})
        
        # Source Filter
        if source:
            if isinstance(source, list):
                if len(source) == 1:
                    filters.append({"source": source[0]})
                elif len(source) > 1:
                    filters.append({"source": {"$in": source}})
            else:
                filters.append({"source": source})
            
        # Combine filters
        if len(filters) == 1:
            where = filters[0]
        elif len(filters) > 1:
            where = {"$and": filters}
        else:
            where = None
            
        try:
            # 1. Semantic Vector Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )

            # Filter by distance threshold (e.g. 0.8) to avoid totally irrelevant matches
            DISTANCE_THRESHOLD = 0.8
            if results and results['ids'] and results['ids'][0]:
                filtered_ids = []
                filtered_docs = []
                filtered_metas = []
                filtered_distances = []
                
                for i in range(len(results['ids'][0])):
                    dist = results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                    if dist <= DISTANCE_THRESHOLD:
                        filtered_ids.append(results['ids'][0][i])
                        filtered_docs.append(results['documents'][0][i])
                        filtered_metas.append(results['metadatas'][0][i])
                        filtered_distances.append(dist)
                
                results['ids'][0] = filtered_ids
                results['documents'][0] = filtered_docs
                results['metadatas'][0] = filtered_metas
                if 'distances' in results:
                    results['distances'][0] = filtered_distances

            # 2. Keyword Fallback (if query_text provided and contains specific patterns or results are weak)
            if query_text and len(query_text) > 3:
                # If the query is a long sentence, $contains will fail as the whole sentence isn't in the doc.
                # Extract the most meaningful part or split by quotes/strong words.
                # For simplicity, if it's over 30 chars, we look for quoted text or just take the first N words
                search_term = query_text.strip()
                if len(search_term) > 30:
                    import re
                    # Try to find quotes first '...' or "..."
                    quoted = re.findall(r'["\'](.*?)["\']', search_term)
                    if quoted and len(quoted[0]) > 3:
                        search_term = quoted[0]
                    else:
                        # Find potential keyword phrases (e.g. "Madde 79", capitalized words, or just fallback to first words)
                        # We use regex to find combinations of Word + Number ("Madde 79") or capitalized sequences
                        important_phrases = re.findall(r'([A-ZÇÖŞİĞÜa-zçöşığü]+\s+\d+)', search_term)
                        if important_phrases:
                            search_term = important_phrases[0]
                        else:
                            words = search_term.split()
                            search_term = " ".join(words[:4]) if len(words) > 4 else search_term

                # To handle basic case variations since $contains is case sensitive in ChromaDB
                q_lower = search_term.lower()
                q_title = search_term.title()
                q_upper = search_term.upper()
                q_cap = search_term.capitalize()
                
                # Use a set to avoid duplicate clauses
                variations = list(set([search_term, q_lower, q_title, q_upper, q_cap]))
                
                if len(variations) == 1:
                    where_doc = {"$contains": variations[0]}
                else:
                    where_doc = {"$or": [{"$contains": v} for v in variations]}

                keyword_results = self.collection.get(
                    where=where,
                    where_document=where_doc,
                    limit=n_results
                )
                
                if keyword_results and keyword_results['ids']:
                    # Merge keyword results into semantic results
                    existing_ids = set(results['ids'][0])
                    for i, doc_id in enumerate(keyword_results['ids']):
                        if doc_id not in existing_ids:
                            # Prepend exact matches to the top 
                            results['ids'][0].insert(0, doc_id)
                            results['documents'][0].insert(0, keyword_results['documents'][i])
                            results['metadatas'][0].insert(0, keyword_results['metadatas'][i])
                            if 'distances' in results and results['distances']:
                                results['distances'][0].insert(0, 0.01) # Near perfect similarity for exact string match
                
            # CRITICAL: Strictly enforce the n_results limit to avoid context-length-driven timeouts (524)
            for key in ['ids', 'documents', 'metadatas', 'distances']:
                if key in results and results[key] and results[key][0]:
                    results[key][0] = results[key][0][:n_results]
                            
            return results
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"VectorDB query error (where={where}): {str(e)}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

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
