"""Text processor for splitting text into paragraphs."""
import re
from typing import List


class TextProcessor:
    """Process and split text into paragraphs."""
    
    @staticmethod
    def split_into_paragraphs(text: str, min_length: int = 50, mode: str = 'paragraph') -> List[str]:
        """Split text into paragraphs or pages, filter, and merge logical units."""
        
        if mode == 'page':
            # Split by page marker
            pages = re.split(r'---\s*SAYFA\s*\d+\s*---', text)
            return [p.strip() for p in pages if p.strip()]

        # Normalize broken PDF font extractions (Missing dotless 'ı' usually becomes U+FFFD or similar)
        # Because 'ı' is overwhelmingly the most common missing glyph in TR PDFs, we map the unknown char to it
        text = text.replace('\ufffd', 'ı')
        text = text.replace('\uf0fd', 'ı') # Common PUA mapping for 'ı'

        # Initial split by double newlines or single newlines with spacing
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Initial cleanup and noise filtering
        initial_units = []
        page_number_pattern = re.compile(r'^\d+$')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Skip standalone page/section numbers
            if page_number_pattern.match(para):
                continue
                
            # Preserve special markers always
            is_special = (para.startswith('[GÖRSEL:') and para.endswith(']')) or \
                         (para.startswith('|') and para.endswith('|')) or \
                         ('|--' in para)
            
            if is_special:
                initial_units.append(para)
                continue
            
            # Filter noise (short wordless strings)
            word_count = len(para.split())
            if len(para) < 20 and word_count < 2 and not para.endswith(':'):
                continue
                
            initial_units.append(para)

        # Filtering Phase (Exclude TOC, Foreword, Introduction, Appendix, etc.)
        filtered_units = []
        is_skipping = False
        
        # Keywords that start a section we want to skip until a main clause is found
        skip_start_patterns = re.compile(r'^(Annex|Appendix|Bibliography|Contents|İçindekiler|Foreword|Introduction|European foreword|Endorsement notice|National foreword|Dizin|Önsöz|Giriş|Kaynaķça)', re.I)
        # Keywords that signal a main clause (e.g., "1 Scope", "2 Normative...") to stop skipping
        keep_start_pattern = re.compile(r'^\d+(\.\d+)?\s+[A-ZÇÖÜİŞĞ]', re.I) 
        
        for unit in initial_units:
            lines = [l.strip() for l in unit.splitlines() if l.strip()]
            if not lines: continue
            
            # Check triggers in ANY line of the unit (to catch headers after document IDs/images)
            has_skip_trigger = False
            has_keep_trigger = False
            for l in lines:
                if skip_start_patterns.match(l) and len(l) < 150:
                    has_skip_trigger = True
                if keep_start_pattern.match(l):
                    has_keep_trigger = True
            
            if has_keep_trigger:
                is_skipping = False
            elif has_skip_trigger:
                is_skipping = True
            
            # TOC Detection: Multiple dots in any line always skips the block
            is_toc = any(re.search(r'\.{5,}', l) for l in lines)
            
            if not is_skipping and not is_toc:
                filtered_units.append(unit)
        
        initial_units = filtered_units

        # Merging Phase
        merged = []
        if not initial_units:
            return merged
            
        current = initial_units[0]
        
        # List marker pattern (matches common bullets and markers at line start)
        list_line_pattern = re.compile(r'^(\s*[\da-zÇÖÜİŞĞçöüişğ]{1,3}[.)]\s*|\s*[^\w\s]\s*)', re.IGNORECASE)

        for i in range(1, len(initial_units)):
            next_unit = initial_units[i]
            should_merge = False
            
            # Helper for list detection
            next_is_list = bool(list_line_pattern.match(next_unit))
            lines = [l.strip() for l in current.splitlines() if l.strip()]
            current_is_list = any(list_line_pattern.match(l) for l in lines)
            current_ends_colon = current.strip().endswith(':')
            
            # Rule 1: Header/Category merge (Balanced threshold: 150)
            is_header = len(current) < 150 and not re.search(r'[.!?]$', current.strip())
            
            # Rule 2: Citation/Reference Detection (Merge short trailing block with previous)
            is_citation = len(next_unit) < 100 and not re.search(r'[.!?]$', next_unit.strip()) and \
                          (',' in next_unit or re.search(r'^[A-ZÇÖÜİŞĞçöüişğ]', next_unit))
            
            # Rule 3: Literary connectors
            next_starts_connector = re.match(r'^(İmdi|\(\.\.\.\)|Ha,|Meğer|Oysa|Halbuki)', next_unit, re.I)

            # Rule 4: Title Detection (Current is a short title leading into next)
            current_is_title = len(current) < 100 and (current.isupper() or not re.search(r'[.!?]$', current.strip()))

            if is_header or current_ends_colon or current_is_title:
                if not (next_unit.startswith('|') or next_unit.startswith('[GÖRSEL:')):
                    should_merge = True
            elif is_citation or next_starts_connector:
                should_merge = True
            elif current_is_list and next_is_list:
                should_merge = True
            elif is_header and len(next_unit) < 150 and not (next_unit.startswith('|') or next_unit.startswith('[GÖRSEL:')):
                 should_merge = True
            elif (current.startswith('|') or '|--' in current) and next_unit.startswith('|'):
                should_merge = True
            elif (re.match(r'^(Not|Önemli|Dikkat)$', current.strip(), re.I) or re.match(r'^\(\d+\)$', current.strip())) and next_unit.startswith('|'):
                should_merge = True

            if should_merge:
                current += "\n\n" + next_unit
            else:
                merged.append(current)
                current = next_unit
        
        merged.append(current)

        # Final cleanup and unwrapping
        final = []
        for unit in merged:
            unit = unit.strip()
            # Clean stray single numbers
            if re.match(r'^\d+$', unit):
                continue

            is_table = '|--' in unit or unit.count('|') > 4
            is_marker = unit.startswith('[GÖRSEL:')
            
            if is_table or is_marker:
                final.append(unit)
                continue

            # Process block with list awareness
            sub_blocks = unit.split("\n\n")
            processed_blocks = []
            
            for block in sub_blocks:
                block = block.strip()
                if not block: continue
                if re.match(r'^\d+$', block) and len(block) < 3: continue
                
                block_lines = block.splitlines()
                has_list = any(list_line_pattern.match(line.strip()) for line in block_lines)
                
                if has_list:
                    # Smart list unwrapping
                    list_items = []
                    current_item = ""
                    for line in block_lines:
                        line = line.strip()
                        if not line: continue
                        
                        if list_line_pattern.match(line):
                            if current_item:
                                list_items.append(re.sub(r'\s+', ' ', current_item).strip())
                            current_item = line
                        else:
                            if current_item:
                                current_item += " " + line
                            else:
                                current_item = line
                    if current_item:
                        list_items.append(re.sub(r'\s+', ' ', current_item).strip())
                    processed_blocks.append("\n".join(list_items))
                else:
                    # Unwrap regular text
                    unwrapped = " ".join(block_lines)
                    unwrapped = re.sub(r'\s+', ' ', unwrapped).strip()
                    processed_blocks.append(unwrapped)
            
            if processed_blocks:
                final_unit = "\n\n".join(processed_blocks)
                if len(final_unit) >= min_length:
                    final.append(final_unit)
                
        return final
