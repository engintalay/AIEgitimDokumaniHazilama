"""Checkpoint manager for resume functionality."""
import json
import os
from typing import Set


class CheckpointManager:
    """Manage checkpoints for resume functionality."""
    
    def __init__(self, checkpoint_dir: str, input_file: str):
        self.checkpoint_dir = checkpoint_dir
        self.input_file = input_file
        self.checkpoint_file = self._get_checkpoint_path()
        self.processed_indices: Set[int] = set()
        
        # Create checkpoint directory
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Load existing checkpoint
        self._load()
    
    def _get_checkpoint_path(self) -> str:
        """Get checkpoint file path based on input file."""
        base_name = os.path.basename(self.input_file)
        checkpoint_name = f"{base_name}.checkpoint.json"
        return os.path.join(self.checkpoint_dir, checkpoint_name)
    
    def _load(self):
        """Load checkpoint from file."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.processed_indices = set(data.get('processed_indices', []))
            except:
                self.processed_indices = set()
    
    def save(self, index: int):
        """Save checkpoint."""
        self.processed_indices.add(index)
        with open(self.checkpoint_file, 'w') as f:
            json.dump({
                'processed_indices': list(self.processed_indices),
                'total_processed': len(self.processed_indices)
            }, f)
    
    def is_processed(self, index: int) -> bool:
        """Check if index is already processed."""
        return index in self.processed_indices
    
    def clear(self):
        """Clear checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        self.processed_indices = set()
    
    def get_progress(self) -> int:
        """Get number of processed items."""
        return len(self.processed_indices)
