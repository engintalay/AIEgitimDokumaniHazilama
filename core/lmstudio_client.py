"""LM Studio AI client implementation."""
import requests
from typing import Dict, Any
from .ai_client import AIClient


class LMStudioClient(AIClient):
    """LM Studio AI client (OpenAI-compatible API)."""
    
    def generate(self, prompt: str) -> str:
        """Generate response from LM Studio."""
        url = f"{self.endpoint}/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            raise RuntimeError(f"LM Studio generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if LM Studio is running."""
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
