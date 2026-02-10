#!/usr/bin/env python3
"""Main CLI application for dataset generation."""
import argparse
import os
import sys
import yaml
from colorama import init, Fore, Style

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.document_parser import DocumentParser
from core.text_processor import TextProcessor
from core.ai_client_factory import AIClientFactory
from core.question_generator import QuestionGenerator
from core.dataset_writer import DatasetWriter
from utils.progress import ProgressTracker
from utils.checkpoint import CheckpointManager
from utils.logger import setup_logger

# Initialize colorama
init(autoreset=True)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description='AI Eğitim Dokümanı Hazırlama - Dataset Generator'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input file path (PDF, DOCX, TXT)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output JSONL file path'
    )
    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Config file path (default: config/config.yaml)'
    )
    parser.add_argument(
        '--resume', '-r',
        action='store_true',
        help='Resume from checkpoint'
    )
    parser.add_argument(
        '--clear-checkpoint',
        action='store_true',
        help='Clear checkpoint and start fresh'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"{Fore.RED}✗ Config yüklenemedi: {e}{Style.RESET_ALL}")
        return 1
    
    # Setup logger
    log_level = 'DEBUG' if args.verbose else config['logging']['level']
    logger = setup_logger(
        level=log_level,
        log_file=config['logging']['file'],
        console=config['logging']['console']
    )
    
    # Determine output path
    output_path = args.output or os.path.join(
        config['output']['directory'],
        config['output']['filename']
    )
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}AI Eğitim Dokümanı Hazırlama - Dataset Generator")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Parse document
    print(f"{Fore.YELLOW}📄 Doküman okunuyor: {args.input}{Style.RESET_ALL}")
    try:
        text = DocumentParser.parse(args.input)
        logger.info(f"Document parsed: {len(text)} characters")
    except Exception as e:
        print(f"{Fore.RED}✗ Doküman okunamadı: {e}{Style.RESET_ALL}")
        return 1
    
    # Split into paragraphs
    print(f"{Fore.YELLOW}📝 Paragraflar ayrıştırılıyor...{Style.RESET_ALL}")
    min_length = config['generation']['min_paragraph_length']
    paragraphs = TextProcessor.split_into_paragraphs(text, min_length)
    print(f"{Fore.GREEN}✓ {len(paragraphs)} paragraf bulundu{Style.RESET_ALL}\n")
    logger.info(f"Found {len(paragraphs)} paragraphs")
    
    if len(paragraphs) == 0:
        print(f"{Fore.RED}✗ Hiç paragraf bulunamadı!{Style.RESET_ALL}")
        return 1
    
    # Setup checkpoint
    checkpoint_manager = None
    if config['checkpoint']['enabled']:
        checkpoint_manager = CheckpointManager(
            config['checkpoint']['directory'],
            args.input
        )
        
        if args.clear_checkpoint:
            checkpoint_manager.clear()
            print(f"{Fore.YELLOW}🔄 Checkpoint temizlendi{Style.RESET_ALL}\n")
        
        already_processed = checkpoint_manager.get_progress()
        if already_processed > 0 and args.resume:
            print(f"{Fore.CYAN}📌 Checkpoint bulundu: {already_processed} paragraf zaten işlenmiş{Style.RESET_ALL}\n")
    
    # Create AI client
    print(f"{Fore.YELLOW}🤖 AI modeli bağlanıyor: {config['model']['type']} - {config['model']['name']}{Style.RESET_ALL}")
    try:
        ai_client = AIClientFactory.create(config['model'])
        if not ai_client.is_available():
            print(f"{Fore.RED}✗ AI servisi erişilebilir değil!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  Lütfen {config['model']['type']} servisinin çalıştığından emin olun.{Style.RESET_ALL}")
            return 1
        print(f"{Fore.GREEN}✓ AI modeli hazır{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ AI client oluşturulamadı: {e}{Style.RESET_ALL}")
        return 1
    
    # Create question generator
    question_generator = QuestionGenerator(
        ai_client,
        min_questions=config['generation']['min_questions_per_paragraph'],
        max_questions=config['generation']['max_questions_per_paragraph']
    )
    
    # Setup progress tracker
    progress = ProgressTracker(
        len(paragraphs),
        show_detailed=config['progress']['show_detailed']
    )
    
    # Process paragraphs
    print(f"{Fore.CYAN}🚀 İşlem başlıyor...{Style.RESET_ALL}\n")
    
    with DatasetWriter(output_path, append=config['output']['append_mode']) as writer:
        for idx, paragraph in enumerate(paragraphs):
            # Skip if already processed
            if checkpoint_manager and checkpoint_manager.is_processed(idx):
                continue
            
            try:
                # Generate questions
                questions = question_generator.generate_questions(paragraph)
                
                # Write to file
                writer.write_batch(questions)
                
                # Update progress
                progress.update(len(questions))
                
                # Save checkpoint
                if checkpoint_manager:
                    checkpoint_manager.save(idx)
                
                logger.debug(f"Processed paragraph {idx+1}/{len(paragraphs)}: {len(questions)} questions")
                
            except Exception as e:
                logger.error(f"Error processing paragraph {idx+1}: {e}")
                print(f"\n{Fore.RED}✗ Hata (paragraf {idx+1}): {e}{Style.RESET_ALL}")
                continue
    
    # Finish
    progress.finish()
    print(f"{Fore.GREEN}✓ Dataset başarıyla oluşturuldu: {output_path}{Style.RESET_ALL}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
