"""LM Studio AI client implementation."""
import requests
import logging
from typing import Dict, Any
from .ai_client import AIClient

logger = logging.getLogger(__name__)


class LMStudioClient(AIClient):
    """LM Studio AI client (OpenAI-compatible API)."""
    
    def generate(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response from LM Studio with optional parameter overrides."""
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
            # Join system prompt with user prompt to avoid "system role not supported" errors in some model templates
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            messages.append({"role": "user", "content": full_prompt})
        else:
            messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens
        }
        
        # Add JSON mode if enabled (some LM Studio versions may not support this)
        if self.json_mode:
            try:
                payload["response_format"] = {"type": "json_object"}
            except:
                logger.warning("JSON mode requested but may not be supported by LM Studio")
        
        # Log request
        logger.debug(f"=== LM STUDIO REQUEST ===")
        logger.debug(f"URL: {url}")
        logger.debug(f"Model: {self.model_name}")
        logger.debug(f"Temperature: {self.temperature}")
        logger.debug(f"JSON Mode: {self.json_mode}")
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
            logger.debug(f"=== LM STUDIO RESPONSE ===")
            logger.debug(f"Usage: {usage}")
            logger.debug(f"Response:\n{result[:500]}..." if len(result) > 500 else f"Response:\n{result}")
            logger.debug(f"=========================\n")
            
            return {"text": result, "usage": usage}
        except requests.exceptions.HTTPError as e:
            # Log detailed error
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            logger.error(f"LM Studio HTTP Error: {e}")
            logger.error(f"Response: {error_detail}")
            raise RuntimeError(f"LM Studio generation failed: {str(e)}")
        except Exception as e:
            logger.error(f"LM Studio generation failed: {str(e)}")
            raise RuntimeError(f"LM Studio generation failed: {str(e)}")
    
    def generate_stream(self, prompt: str, options: Dict[str, Any] = None):
        """Generate streaming response from LM Studio."""
        options = options or {}
        endpoint = options.get('endpoint', self.endpoint) or self.endpoint
        url = f"{endpoint}/v1/chat/completions"
        model = options.get('name', self.model_name) or self.model_name
        
        try:
            temp = float(options.get('temperature', self.temperature))
            tokens = int(options.get('max_tokens', self.max_tokens))
        except:
            temp = self.temperature
            tokens = self.max_tokens

        messages = []
        if self.use_system_prompt and self.system_prompt:
            messages.append({"role": "user", "content": f"{self.system_prompt}\n\n{prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
            "stream": True # Enable streaming
        }
        
        try:
            import json
            # Using context manager for automatic closure
            with requests.post(url, json=payload, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            data_str = line_text[6:].strip()
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                chunk_text = data['choices'][0]['delta'].get('content', '')
                                if chunk_text:
                                    yield {"type": "content", "text": chunk_text}
                                    
                                if 'usage' in data:
                                    yield {"type": "usage", "usage": data['usage']}
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"LM Studio streaming failed: {str(e)}")
            yield {"type": "error", "message": str(e)}
        finally:
            logger.info("LM Studio stream generator closed.")

    def is_available(self) -> bool:
        """Check if LM Studio is running."""
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_available_models(self) -> list:
        """Fetch models from LM Studio /v1/models."""
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            response.raise_for_status()
            models = response.json().get('data', [])
            return [m['id'] for m in models]
        except Exception as e:
            logger.error(f"LM Studio model fetch failed: {e}")
            return []
