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
    parser.add_argument('--mode', choices=['paragraph', 'page'], default='paragraph', help='Segmentation mode: paragraph or page (default: paragraph)')
    
    args = parser.parse_args()
    
    input_path = args.input_file
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
        
    # Generate output file name
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}.txt"
    
    print(f"Processing: {input_path} (Mode: {args.mode})")
    
    try:
        # Step 1: Parse the document
        text = DocumentParser.parse(input_path, args.mode)
        
        # Step 2: Split into paragraphs/pages
        units = TextProcessor.split_into_paragraphs(text, args.min_length, args.mode)
        
        unit_type = "pages" if args.mode == 'page' else "paragraphs"
        print(f"Found {len(units)} {unit_type}.")
        
        # Step 3: Save to .txt
        with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
            for i, unit in enumerate(units, 1):
                label = "SAYFA" if args.mode == 'page' else "PARAGRAF"
                f.write(f"--- {label} {i} BAŞLANGIÇ ---\n")
                f.write(unit)
                f.write(f"\n--- {label} {i} BİTİŞ ---\n\n")
            
        print(f"Success! Output saved to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
