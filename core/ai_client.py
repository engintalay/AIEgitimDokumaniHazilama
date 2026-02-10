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
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate response from AI model."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI service is available."""
        pass
