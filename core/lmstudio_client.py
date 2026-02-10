"""LM Studio AI client implementation."""
import requests
import logging
from typing import Dict, Any
from .ai_client import AIClient

logger = logging.getLogger(__name__)


class LMStudioClient(AIClient):
    """LM Studio AI client (OpenAI-compatible API)."""
    
    def generate(self, prompt: str) -> str:
        """Generate response from LM Studio."""
        url = f"{self.endpoint}/v1/chat/completions"
        
        # Qwen2.5 için system prompt
        system_prompt = "Sen bir Türkçe eğitim dataset uzmanısın. Verilen talimatlara göre JSON formatında soru-cevap çiftleri oluşturursun."
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}  # JSON mode
        }
        
        # Log request
        logger.debug(f"=== LM STUDIO REQUEST ===")
        logger.debug(f"URL: {url}")
        logger.debug(f"Model: {self.model_name}")
        logger.debug(f"Temperature: {self.temperature}")
        logger.debug(f"System: {system_prompt}")
        logger.debug(f"Prompt:\n{prompt[:500]}..." if len(prompt) > 500 else f"Prompt:\n{prompt}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()['choices'][0]['message']['content']
            
            # Log response
            logger.debug(f"=== LM STUDIO RESPONSE ===")
            logger.debug(f"Response:\n{result[:500]}..." if len(result) > 500 else f"Response:\n{result}")
            logger.debug(f"=========================\n")
            
            return result
        except Exception as e:
            logger.error(f"LM Studio generation failed: {str(e)}")
            raise RuntimeError(f"LM Studio generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if LM Studio is running."""
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
