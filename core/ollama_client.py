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
    
    def generate(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response from Ollama with optional parameter overrides."""
        options = options or {}
        
        # Merge options into defaults
        endpoint = options.get('endpoint', self.endpoint) or self.endpoint
        url = f"{endpoint}/api/generate"
        
        model = options.get('name', self.model_name) or self.model_name
        
        try:
            temp_val = options.get('temperature', self.temperature)
            temp = float(temp_val) if temp_val not in (None, '') else self.temperature
        except (ValueError, TypeError):
            temp = self.temperature

        try:
            tokens_val = options.get('max_tokens', self.max_tokens)
            tokens = int(tokens_val) if tokens_val not in (None, '') else self.max_tokens
        except (ValueError, TypeError):
            tokens = self.max_tokens

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": tokens
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
            data = response.json()
            result = data.get('response', '')
            
            # Extract usage
            usage = {
                "prompt_tokens": data.get('prompt_eval_count', 0),
                "completion_tokens": data.get('eval_count', 0)
            }
            
            # Log response
            logger.debug(f"=== OLLAMA RESPONSE ===")
            logger.debug(f"Usage: {usage}")
            logger.debug(f"Response:\n{result[:500]}..." if len(result) > 500 else f"Response:\n{result}")
            logger.debug(f"======================\n")
            
            return {"text": result, "usage": usage}
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

    def get_available_models(self) -> list:
        """Fetch models from Ollama /api/tags."""
        try:
            response = self.session.get(f"{self.endpoint}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        except Exception as e:
            logger.error(f"Ollama model fetch failed: {e}")
            return []
