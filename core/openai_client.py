"""OpenAI AI client implementation (for future use)."""
import requests
from typing import Dict, Any
from .ai_client import AIClient


class OpenAIClient(AIClient):
    """OpenAI AI client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
    
    def generate(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """Generate response from OpenAI with optional parameter overrides."""
        url = "https://api.openai.com/v1/chat/completions"
        
        # Merge options into defaults
        temp = float(options.get('temperature', self.temperature)) if options and 'temperature' in options else self.temperature
        tokens = int(options.get('max_tokens', self.max_tokens)) if options and 'max_tokens' in options else self.max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temp,
            "max_tokens": tokens
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def get_available_models(self) -> list:
        """Fetch models from OpenAI."""
        if not self.api_key: return []
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
            response.raise_for_status()
            models = response.json().get('data', [])
            return [m['id'] for m in models]
        except:
            return []
