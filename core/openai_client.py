"""OpenAI AI client implementation (for future use)."""
import requests
from typing import Dict, Any
from .ai_client import AIClient


class OpenAIClient(AIClient):
    """OpenAI AI client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
    
    def generate(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response from OpenAI with optional parameter overrides."""
        options = options or {}
        
        # Merge options into defaults with safety checks
        endpoint = options.get('endpoint', self.endpoint) or "https://api.openai.com"
        url = f"{endpoint}/v1/chat/completions"
        
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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
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
            data = response.json()
            usage_data = data.get('usage', {})
            usage = {
                "prompt_tokens": usage_data.get('prompt_tokens', 0),
                "completion_tokens": usage_data.get('completion_tokens', 0)
            }
            return {
                "text": data['choices'][0]['message']['content'],
                "usage": usage
            }
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
