"""Ollama AI client implementation."""
import requests
import json
import logging
from typing import Dict, Any
from .ai_client import AIClient

logger = logging.getLogger(__name__)


class OllamaClient(AIClient):
    """Ollama AI client."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.trust_env = False  # Proxy ayarlarını yoksay
    
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
        
        # Log request
        logger.debug(f"=== OLLAMA REQUEST ===")
        logger.debug(f"URL: {url}")
        logger.debug(f"Model: {self.model_name}")
        logger.debug(f"Temperature: {self.temperature}")
        logger.debug(f"Prompt:\n{prompt[:500]}..." if len(prompt) > 500 else f"Prompt:\n{prompt}")
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json().get('response', '')
            
            # Log response
            logger.debug(f"=== OLLAMA RESPONSE ===")
            logger.debug(f"Response:\n{result[:500]}..." if len(result) > 500 else f"Response:\n{result}")
            logger.debug(f"======================\n")
            
            return result
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            raise RuntimeError(f"Ollama generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = self.session.get(f"{self.endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
