"""Dataset writer for JSONL format."""
import json
import os
from typing import Dict, Any, List


class DatasetWriter:
    """Write dataset entries to JSONL file."""
    
    def __init__(self, output_path: str, append: bool = True):
        self.output_path = output_path
        self.append = append
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Open file in append or write mode
        mode = 'a' if append and os.path.exists(output_path) else 'w'
        self.file = open(output_path, mode, encoding='utf-8')
    
    def write(self, entry: Dict[str, Any]):
        """Write a single entry to JSONL file."""
        self.file.write(json.dumps(entry, ensure_ascii=False) + '\n')
        self.file.flush()
    
    def write_batch(self, entries: List[Dict[str, Any]]):
        """Write multiple entries to JSONL file."""
        for entry in entries:
            self.write(entry)
    
    def close(self):
        """Close the file."""
        if self.file:
            self.file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
