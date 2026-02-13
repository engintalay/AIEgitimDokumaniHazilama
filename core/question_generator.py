"""Question generator using AI models."""
import json
import re
import logging
from typing import List, Dict, Any
from .ai_client import AIClient


class QuestionGenerator:
    """Generate question-answer pairs from paragraphs."""
    
    def __init__(self, ai_client: AIClient, min_questions: int = 3, max_questions: int = 8):
        self.ai_client = ai_client
        self.min_questions = min_questions
        self.max_questions = max_questions
    
    def generate_questions(self, paragraph: str) -> List[Dict[str, Any]]:
        """Generate questions from a paragraph."""
        prompt = self._create_prompt(paragraph)
        
        try:
            response = self.ai_client.generate(prompt)
            questions = self._parse_response(response)
            return questions
        except Exception as e:
            # Log detailed error information
            logger = logging.getLogger(__name__)
            logger.error(f"\n{'='*80}")
            logger.error(f"QUESTION GENERATION ERROR")
            logger.error(f"{'='*80}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"\nPARAGRAPH ({len(paragraph)} chars):")
            logger.error(f"{paragraph}")
            logger.error(f"\nMODEL CONFIG:")
            logger.error(f"  Type: {self.ai_client.config.get('type')}")
            logger.error(f"  Name: {self.ai_client.model_name}")
            logger.error(f"  Endpoint: {self.ai_client.endpoint}")
            logger.error(f"  Temperature: {self.ai_client.temperature}")
            logger.error(f"  Max Tokens: {self.ai_client.max_tokens}")
            logger.error(f"  Timeout: {self.ai_client.timeout}")
            logger.error(f"  Use System Prompt: {self.ai_client.use_system_prompt}")
            logger.error(f"  JSON Mode: {self.ai_client.json_mode}")
            logger.error(f"  JSON Wrapper: {self.ai_client.json_wrapper}")
            logger.error(f"\nQUESTION SETTINGS:")
            logger.error(f"  Min Questions: {self.min_questions}")
            logger.error(f"  Max Questions: {self.max_questions}")
            logger.error(f"\nPROMPT SENT:")
            logger.error(f"{prompt}")
            logger.error(f"{'='*80}\n")
            raise RuntimeError(f"Question generation failed: {str(e)}")
    
    def _create_prompt(self, paragraph: str) -> str:
        """Create prompt for question generation."""
        # Determine output format based on config
        json_wrapper = self.ai_client.json_wrapper
        
        if json_wrapper:
            # Wrapped format: {"questions": [...]}
            example_format = f'''{{
  "{json_wrapper}": [
    {{
      "instruction": "Soru metni",
      "input": "",
      "output": "Cevap metni",
      "confidence": "high"
    }}
  ]
}}'''
        else:
            # Direct array format: [...]
            example_format = '''[
  {
    "instruction": "Soru metni",
    "input": "",
    "output": "Cevap metni",
    "confidence": "high"
  }
]'''
        
        return f"""Aşağıdaki metinden {self.min_questions}-{self.max_questions} adet soru-cevap çifti oluştur.

KRİTİK KURALLAR:
1. SADECE metinde açıkça geçen bilgilerden soru oluştur
2. Cevaplar net, kısa, doğru ve TAMAMEN TÜRKÇE olmalı
3. HALÜSİNASYON YAPMA - metinde olmayan bilgi ekleme
4. İngilizce kelime kullanma (available, usually vb. YASAK)
5. Gramer hatası yapma, düzgün Türkçe cümleler kur
6. Sorular çeşitli olmalı (ne, nasıl, neden, kaç, hangi vb.)

CONFIDENCE KURALLARI:
- "high": Metinde açıkça yazıyor, net kural var
- "low": Metinde geçmiyor, belirsiz, dış kaynak gerekiyor

JSON KURALLARI:
- Geçerli JSON formatı kullan
- String'lerde çift tırnak kullan
- Özel karakterleri escape et (\\n, \\", \\\\)
- Tırnak işaretlerini kapatmayı unutma

METIN:
{paragraph}

SADECE geçerli JSON formatında cevap ver, başka açıklama ekleme:
{example_format}"""
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract questions."""
        logger = logging.getLogger(__name__)
        
        # Clean response - remove markdown code blocks
        response = response.strip()
        response = re.sub(r'^```json\s*', '', response)
        response = re.sub(r'^```\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        
        try:
            # Try to parse as JSON object first (LM Studio JSON mode)
            data = json.loads(response)
            
            # Check if it's wrapped (e.g., {"questions": [...]} or {"sorular": [...]})
            json_wrapper = self.ai_client.json_wrapper
            wrapper_variants = [json_wrapper, 'sorular', 'questions', 'items']  # Turkish and English variants
            
            if isinstance(data, dict):
                # Try to find questions in any wrapper variant
                questions = None
                for wrapper in wrapper_variants:
                    if wrapper and wrapper in data:
                        questions = data[wrapper]
                        break
                
                if questions is None:
                    logger.error(f"Invalid JSON structure. Expected array or object with wrapper key")
                    logger.error(f"Received: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                    raise ValueError("Invalid JSON structure")
            # Or if it's directly an array
            elif isinstance(data, list):
                questions = data
            else:
                logger.error(f"Invalid JSON structure. Expected array or object")
                logger.error(f"Received: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                raise ValueError("Invalid JSON structure")
                
        except json.JSONDecodeError:
            # Fallback: Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                # Log the full response for debugging
                logger.error(f"No JSON found in response.")
                logger.error(f"FULL RESPONSE ({len(response)} chars):")
                logger.error(f"{response}")
                raise ValueError("No valid JSON found in response")
            
            json_str = json_match.group(0)
            try:
                questions = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                logger.error(f"Attempted to parse:")
                logger.error(f"{json_str[:1000]}")
                raise ValueError(f"Failed to parse JSON: {str(e)}")
        
        # Validate and clean
        validated = []
        for q in questions:
            # Normalize Turkish field names to English
            normalized = {}
            
            # Map Turkish to English field names
            field_mapping = {
                'instruction': 'instruction',
                'soru': 'instruction',
                'input': 'input',
                'giriş': 'input',
                'girdi': 'input',
                'output': 'output',
                'çıkış': 'output',
                'cevap': 'output',
                'confidence': 'confidence',
                'güvenilirlik': 'confidence',
                'güven': 'confidence'
            }
            
            # Normalize fields
            for key, value in q.items():
                normalized_key = field_mapping.get(key.lower(), key)
                normalized[normalized_key] = value
            
            # Check required fields
            if all(k in normalized for k in ['instruction', 'output', 'confidence']):
                if 'input' not in normalized:
                    normalized['input'] = ""
                
                # Normalize confidence values
                conf = str(normalized['confidence']).lower()
                if conf in ['high', 'yüksek', 'yuksek']:
                    normalized['confidence'] = 'high'
                elif conf in ['low', 'düşük', 'dusuk', 'alçak']:
                    normalized['confidence'] = 'low'
                else:
                    normalized['confidence'] = 'low'
                
                validated.append(normalized)
        
        if not validated:
            logger.error(f"No valid questions found after validation")
            logger.error(f"Raw questions: {json.dumps(questions, indent=2, ensure_ascii=False)[:500]}")
            raise ValueError("No valid questions found in response")
        
        return validated
