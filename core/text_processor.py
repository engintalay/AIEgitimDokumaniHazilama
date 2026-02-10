"""Text processor for splitting text into paragraphs."""
import re
from typing import List


class TextProcessor:
    """Process and split text into paragraphs."""
    
    @staticmethod
    def split_into_paragraphs(text: str, min_length: int = 50) -> List[str]:
        """Split text into paragraphs and filter by minimum length."""
        # Split by double newlines or single newlines
        paragraphs = re.split(r'\n\s*\n|\n', text)
        
        # Clean and filter paragraphs
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            if len(para) >= min_length:
                cleaned.append(para)
        
        return cleaned
