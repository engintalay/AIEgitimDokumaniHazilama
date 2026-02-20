"""llama.cpp AI client implementation."""
import requests
import logging
from typing import Dict, Any
from .ai_client import AIClient

logger = logging.getLogger(__name__)


class LlamaCppClient(AIClient):
    """llama.cpp AI client (OpenAI-compatible API via llama-server)."""
    
    def generate(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response from llama.cpp server with optional parameter overrides."""
        options = options or {}
        
        # Merge options into defaults with safety checks
        endpoint = options.get('endpoint', self.endpoint) or self.endpoint
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

        # Build messages based on config
        messages = []
        if self.use_system_prompt and self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens
        }
        
        # Log request
        logger.debug(f"=== LLAMA.CPP REQUEST ===")
        logger.debug(f"URL: {url}")
        logger.debug(f"Model: {model}")
        logger.debug(f"Temperature: {temp}")
        if self.use_system_prompt:
            logger.debug(f"System: {self.system_prompt}")
        logger.debug(f"Prompt:\n{prompt[:500]}..." if len(prompt) > 500 else f"Prompt:\n{prompt}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            usage_data = data.get('usage', {})
            usage = {
                "prompt_tokens": usage_data.get('prompt_tokens', 0),
                "completion_tokens": usage_data.get('completion_tokens', 0)
            }
            
            # Log response
            logger.debug(f"=== LLAMA.CPP RESPONSE ===")
            logger.debug(f"Usage: {usage}")
            logger.debug(f"Response:\n{result[:500]}..." if len(result) > 500 else f"Response:\n{result}")
            logger.debug(f"==========================\n")
            
            return {"text": result, "usage": usage}
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            logger.error(f"llama.cpp HTTP Error: {e}")
            logger.error(f"Response: {error_detail}")
            raise RuntimeError(f"llama.cpp generation failed: {str(e)}")
        except Exception as e:
            logger.error(f"llama.cpp generation failed: {str(e)}")
            raise RuntimeError(f"llama.cpp generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if llama.cpp server is running."""
        try:
            response = requests.get(f"{self.endpoint}/health", timeout=5)
            return response.status_code == 200
        except:
            # Fallback: try v1/models endpoint
            try:
                response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
                return response.status_code == 200
            except:
                return False

    def get_available_models(self) -> list:
        """Fetch models from llama.cpp /v1/models."""
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            response.raise_for_status()
            models = response.json().get('data', [])
            return [m['id'] for m in models]
        except:
            return []
