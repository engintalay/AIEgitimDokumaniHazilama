"""Abstract base class for AI clients."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class AIClient(ABC):
    """Abstract base class for AI model clients."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('name', '')
        self.endpoint = config.get('endpoint', '')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        self.timeout = config.get('timeout', 120)
        
        # Prompt format settings
        self.use_system_prompt = config.get('use_system_prompt', False)
        self.system_prompt = config.get('system_prompt', '')
        self.json_mode = config.get('json_mode', False)
        self.json_wrapper = config.get('json_wrapper', '')
    
    @abstractmethod
    def generate(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """Generate response from AI model with optional parameter overrides."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI service is available."""
        pass

    @abstractmethod
    def get_available_models(self) -> list:
        """Fetch list of available models from the provider."""
        pass
