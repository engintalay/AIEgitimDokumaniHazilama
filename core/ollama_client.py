"""Ollama AI client implementation."""
import requests
import json
from typing import Dict, Any
from .ai_client import AIClient


class OllamaClient(AIClient):
    """Ollama AI client."""
    
    def generate(self, prompt: str) -> str:
        """Generate response from Ollama."""
        url = f"{self.endpoint}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
