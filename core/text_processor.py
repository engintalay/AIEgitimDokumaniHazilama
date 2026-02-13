"""Text processor for splitting text into paragraphs."""
import re
from typing import List


class TextProcessor:
    """Process and split text into paragraphs."""
    
    @staticmethod
    def split_into_paragraphs(text: str, min_length: int = 50) -> List[str]:
        """Split text into paragraphs and filter by minimum length."""
        # Try double newlines first (better for structured documents)
        paragraphs = re.split(r'\n\n+', text)
        
        # If too few paragraphs, try single newlines
        if len(paragraphs) < 5:
            paragraphs = re.split(r'\n\s*\n|\n', text)
        
        # Clean and filter paragraphs
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            
            # Skip if too short or too long
            if not (min_length <= len(para) <= 2000):
                continue
            
            # Skip if mostly dots (table of contents) - more than 40% dots
            dot_ratio = para.count('.') / len(para) if len(para) > 0 else 0
            if dot_ratio > 0.4:
                continue
            
            # Skip if too few words (likely headers/titles) - less than 5 words
            word_count = len(para.split())
            if word_count < 5:
                continue
            
            cleaned.append(para)
        
        return cleaned
