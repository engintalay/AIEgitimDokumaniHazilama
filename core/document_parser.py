"""Document parser for PDF, DOCX, and TXT files."""
import os
from typing import Optional
import fitz  # pymupdf
from docx import Document


class DocumentParser:
    """Parse various document formats and extract text."""
    
    @staticmethod
    def parse(file_path: str) -> str:
        """Parse document and return text content."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return DocumentParser._parse_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return DocumentParser._parse_docx(file_path)
        elif ext == '.txt':
            return DocumentParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """Extract text from PDF using pymupdf (more robust than pdfplumber)."""
        text = []
        try:
            doc = fitz.open(file_path)
            for page in doc:
                page_text = page.get_text()
                if page_text and page_text.strip():
                    text.append(page_text)
            doc.close()
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF: {str(e)}")
        
        return "\n".join(text)
    
    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """Extract text from DOCX."""
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    
    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """Read text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
