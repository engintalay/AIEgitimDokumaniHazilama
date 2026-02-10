"""Question generator using AI models."""
import json
import re
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
        return f"""Aşağıdaki metinden {self.min_questions}-{self.max_questions} adet soru-cevap çifti oluştur.

KURALLAR:
1. Her soru metinde açıkça geçen bilgilerden oluşturulmalı
2. Cevaplar net, kısa ve doğru olmalı
3. Halüsinasyon yapma, sadece metinde olan bilgileri kullan
4. Sorular çeşitli olmalı (ne, nasıl, neden, kaç, hangi vb.)
5. Her soru-cevap için confidence değeri belirle:
   - "high": Metinde açıkça yazıyorsa, net kural varsa, menü yolu verilmişse
   - "low": Metinde geçmiyorsa, belirsizse, dış kaynak gerektiriyorsa

METIN:
{paragraph}

ÇIKTI FORMATI (JSON array):
[
  {{
    "instruction": "Soru metni",
    "input": "",
    "output": "Cevap metni",
    "confidence": "high"
  }}
]

Sadece JSON array döndür, başka açıklama ekleme."""
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract questions."""
        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON array found in response")
        
        try:
            questions = json.loads(json_match.group(0))
            
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
            
            return validated
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {str(e)}")
