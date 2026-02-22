import requests
from typing import List, Optional

class EmbeddingClient:
    """Handle embedding generation via various providers (Ollama, OpenAI)."""
    
    def __init__(self, provider: str = "ollama", endpoint: str = "http://127.0.0.1:11434", model: str = "nomic-embed-text", api_key: str = ""):
        self.provider = provider.lower()
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.api_key = api_key

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text block."""
        if self.provider == "ollama":
            return self._get_ollama_embedding(text)
        elif self.provider == "openai":
            return self._get_openai_embedding(text)
        elif self.provider == "llamacpp":
            return self._get_llamacpp_embedding(text)
        elif self.provider == "lmstudio":
            return self._get_lmstudio_embedding(text)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def _get_lmstudio_embedding(self, text: str) -> List[float]:
        """Call LM Studio embedding API (OpenAI compatible)."""
        url = f"{self.endpoint}/v1/embeddings"
        payload = {
            "model": self.model,
            "input": text
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            raise RuntimeError(f"LM Studio embedding failed: {str(e)}")

    def _get_llamacpp_embedding(self, text: str) -> List[float]:
        """Call llama.cpp embedding API."""
        # llama.cpp standard endpoint is /embedding
        url = f"{self.endpoint}/embedding"
        payload = {
            "content": text
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            raise RuntimeError(f"llama.cpp embedding failed: {str(e)}")

    def _get_ollama_embedding(self, text: str) -> List[float]:
        """Call Ollama embedding API."""
        # Use newer /api/embed endpoint which is more robust
        url = f"{self.endpoint}/api/embed"
        payload = {
            "model": self.model,
            "input": text
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 404:
                # Fallback to legacy /api/embeddings
                url_legacy = f"{self.endpoint}/api/embeddings"
                payload_legacy = {"model": self.model, "prompt": text}
                response = requests.post(url_legacy, json=payload_legacy, timeout=30)
                response.raise_for_status()
                return response.json()["embedding"]
            
            response.raise_for_status()
            data = response.json()
            # /api/embed returns "embeddings": [[...]]
            if "embeddings" in data:
                return data["embeddings"][0]
            # fallback for some versions
            return data["embedding"]
        except Exception as e:
            raise RuntimeError(f"Ollama embedding failed: {str(e)}")

    def _get_openai_embedding(self, text: str) -> List[float]:
        """Call OpenAI embedding API."""
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model if self.model else "text-embedding-3-small",
            "input": text
        }
        try:
            response = requests.post(url, json=headers, payload=payload, timeout=30)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failed: {str(e)}")
