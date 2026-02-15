#!/usr/bin/env python3
import sys
import os
import argparse
from core.document_parser import DocumentParser
from core.text_processor import TextProcessor

def main():
    parser = argparse.ArgumentParser(description='Split a document into paragraphs and save as .txt')
    parser.add_argument('input_file', help='Path to the input file (PDF, DOCX, TXT)')
    parser.add_argument('--min-length', type=int, default=50, help='Minimum character length for a paragraph (default: 50)')
    
    args = parser.parse_args()
    
    input_path = args.input_file
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
        
    # Generate output file name
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}.txt"
    
    print(f"Processing: {input_path}")
    
    try:
        # Step 1: Parse the document
        text = DocumentParser.parse(input_path)
        
        # Step 2: Split into paragraphs
        paragraphs = TextProcessor.split_into_paragraphs(text, args.min_length)
        
        print(f"Found {len(paragraphs)} paragraphs.")
        
        # Step 3: Save to .txt
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, para in enumerate(paragraphs, 1):
                f.write(f"--- PARAGRAF {i} BAŞLANGIÇ ---\n")
                f.write(para)
                f.write(f"\n--- PARAGRAF {i} BİTİŞ ---\n\n")
            
        print(f"Success! Output saved to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
