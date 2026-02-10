"""Progress tracker with ETA and detailed statistics."""
import time
from datetime import timedelta
from typing import Optional


class ProgressTracker:
    """Track progress with detailed statistics and ETA."""
    
    def __init__(self, total_items: int, show_detailed: bool = True):
        self.total_items = total_items
        self.show_detailed = show_detailed
        self.current_item = 0
        self.total_questions = 0
        self.start_time = time.time()
        self.last_update = self.start_time
    
    def update(self, questions_generated: int = 0):
        """Update progress."""
        self.current_item += 1
        self.total_questions += questions_generated
        self.last_update = time.time()
        
        if self.show_detailed:
            self._print_progress()
    
    def _print_progress(self):
        """Print detailed progress information."""
        elapsed = time.time() - self.start_time
        progress_pct = (self.current_item / self.total_items) * 100
        
        # Calculate ETA
        if self.current_item > 0:
            avg_time_per_item = elapsed / self.current_item
            remaining_items = self.total_items - self.current_item
            eta_seconds = avg_time_per_item * remaining_items
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = "Hesaplanıyor..."
        
        # Calculate speed
        speed = self.current_item / elapsed if elapsed > 0 else 0
        
        print(f"\r[{self.current_item}/{self.total_items}] "
              f"{progress_pct:.1f}% | "
              f"Sorular: {self.total_questions} | "
              f"Hız: {speed:.2f} para/sn | "
              f"ETA: {eta} | "
              f"Geçen: {str(timedelta(seconds=int(elapsed)))}", 
              end='', flush=True)
    
    def finish(self):
        """Print final statistics."""
        print()  # New line
        elapsed = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"✓ Tamamlandı!")
        print(f"  Toplam paragraf: {self.total_items}")
        print(f"  Toplam soru: {self.total_questions}")
        print(f"  Toplam süre: {str(timedelta(seconds=int(elapsed)))}")
        print(f"  Ortalama: {self.total_questions/self.total_items:.1f} soru/paragraf")
        print(f"{'='*60}\n")
