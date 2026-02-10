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

ÇIKTI FORMATI (sadece JSON array, başka hiçbir şey yazma):
[
  {{
    "instruction": "Soru metni (düzgün Türkçe)",
    "input": "",
    "output": "Cevap metni (düzgün Türkçe, kısa, net)",
    "confidence": "high"
  }}
]

ÖNEMLİ: Sadece JSON array döndür. İngilizce kelime kullanma. Gramer hatası yapma."""
    
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
