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
            raise RuntimeError(f"Question generation failed: {str(e)}")
    
    def _create_prompt(self, paragraph: str) -> str:
        """Create prompt for question generation."""
        return f"""Sen bir Türkçe eğitim dataset uzmanısın. Aşağıdaki metinden {self.min_questions}-{self.max_questions} adet soru-cevap çifti oluştur.

KRİTİK KURALLAR:
1. SADECE metinde açıkça geçen bilgilerden soru oluştur
2. Cevaplar net, kısa, doğru ve TAMAMEN TÜRKÇE olmalı
3. HALÜSİNASYON YAPMA - metinde olmayan bilgi ekleme
4. İngilizce kelime kullanma (available, usually, risk management vb. YASAK)
5. Gramer hatası yapma, düzgün Türkçe cümleler kur
6. Sorular çeşitli olmalı (ne, nasıl, neden, kaç, hangi, nerede vb.)

CONFIDENCE KURALLARI:
- "high": Metinde açıkça yazıyor, net kural var, menü yolu var
- "low": Metinde geçmiyor, belirsiz, dış kaynak gerekiyor

METIN:
{paragraph}

ÇOK ÖNEMLİ: Sadece ve sadece aşağıdaki JSON formatında cevap ver. Başka hiçbir açıklama, yorum veya metin ekleme!

[
  {{
    "instruction": "Soru metni (düzgün Türkçe)",
    "input": "",
    "output": "Cevap metni (düzgün Türkçe, kısa, net)",
    "confidence": "high"
  }}
]"""
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract questions."""
        # Clean response - remove markdown code blocks
        response = response.strip()
        response = re.sub(r'^```json\s*', '', response)
        response = re.sub(r'^```\s*', '', response)
        response = re.sub(r'\s*```$', '', response)
        
        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if not json_match:
            # Log the response for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"No JSON array found. Response was:\n{response[:500]}")
            raise ValueError("No valid JSON array found in response")
        
        json_str = json_match.group(0)
        
        try:
            questions = json.loads(json_str)
            
            # Validate and clean
            validated = []
            for q in questions:
                if all(k in q for k in ['instruction', 'output', 'confidence']):
                    if 'input' not in q:
                        q['input'] = ""
                    # Ensure confidence is only high or low
                    if q['confidence'] not in ['high', 'low']:
                        q['confidence'] = 'low'
                    validated.append(q)
            
            if not validated:
                raise ValueError("No valid questions found in response")
            
            return validated
        except json.JSONDecodeError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"JSON parse error. String was:\n{json_str[:500]}")
            raise ValueError(f"Failed to parse JSON: {str(e)}")
