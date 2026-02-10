"""AI client factory."""
from typing import Dict, Any
from core.ai_client import AIClient
from core.ollama_client import OllamaClient
from core.lmstudio_client import LMStudioClient
from core.openai_client import OpenAIClient


class AIClientFactory:
    """Factory for creating AI clients."""
    
    @staticmethod
    def create(config: Dict[str, Any]) -> AIClient:
        """Create AI client based on config."""
        model_type = config.get('type', '').lower()
        
        if model_type == 'ollama':
            return OllamaClient(config)
        elif model_type == 'lmstudio':
            return LMStudioClient(config)
        elif model_type == 'openai':
            return OpenAIClient(config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
