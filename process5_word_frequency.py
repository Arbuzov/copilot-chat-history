#!/usr/bin/env python3
"""
Process 5: Word Frequency Analysis
- Read duplicate CSV files
- Extract all words (exclude stop words)
- Create frequency index with columns:
  Date | Term | Count | First Occurrence
- Sort: Earliest occurrence first, then highest usage
- Output: Excel (.xlsx)
"""

import csv
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

class WordFrequencyAnalyzer:
    # Common English stop words to exclude
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
        'the', 'to', 'was', 'will', 'with', 'you', 'your', 'this', 'these',
        'those', 'what', 'which', 'who', 'where', 'when', 'why', 'how',
        'i', 'me', 'we', 'us', 'them', 'him', 'her', 'my', 'our', 'their',
        'can', 'could', 'should', 'would', 'may', 'might', 'must', 'shall',
        'do', 'does', 'did', 'have', 'having', 'been', 'being', 'get', 'got',
        'make', 'made', 'go', 'going', 'come', 'came', 'see', 'saw', 'know',
        'knew', 'think', 'thought', 'say', 'said', 'ask', 'asked', 'tell',
        'told', 'give', 'gave', 'take', 'took', 'use', 'used', 'work',
        'worked', 'find', 'found', 'right', 'just', 'like', 'well', 'good',
        'new', 'way', 'day', 'man', 'time', 'year', 'people', 'more', 'also',
        'no', 'yes', 'ok', 'not', 'don', 'doesn', 'won', 'can', 'isn'
    }
    
    def __init__(self):
        self.duplicate_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-processed-duplicates")
        self.output_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-frequency-index")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def extract_words(self, text: str) -> list:
        """Extract words from text, lowercase, remove punctuation"""
        if not text:
            return []
        # Remove special chars, keep only alphanumeric and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        words = text.lower().split()
        # Filter: must be > 2 chars and not stop word
        return [w for w in words if len(w) > 2 and w not in self.STOP_WORDS]
    
    def analyze_duplicate(self, csv_file: Path) -> dict:
        """Analyze single duplicate CSV file"""
        word_data = defaultdict(lambda: {
            'count': 0,
            'first_occurrence': None,
            'first_row': None,
            'dates': set()
        })
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):  # start=2 (skip header)
                    # Get date if exists
                    date_str = row.get('Time', row.get('Date', 'Unknown'))
                    message = row.get('Message', '')
                    
                    # Extract words
                    words = self.extract_words(message)
                    
                    for word in words:
                        if word_data[word]['first_occurrence'] is None:
                            word_data[word]['first_occurrence'] = row_num
                            word_data[word]['first_row'] = row_num
                        word_data[word]['count'] += 1
                        if date_str:
                            word_data[word]['dates'].add(date_str)
            
            return dict(word_data)
            
        except Exception as e:
            print(f"[ERROR] Failed to analyze {csv_file.name}: {e}")
            return {}
    
    def create_frequency_report(self, word_data: dict) -> Path:
        """Create Excel report with word frequency"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Word Frequency Index"
        
        # Headers
        headers = ['Date', 'Term', 'Count', 'First Occurrence Row']
        ws.append(headers)
        
        # Format header row
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Sort data: by first occurrence (earliest first), then by count (highest first)
        sorted_words = sorted(
            word_data.items(),
            key=lambda x: (x[1]['first_occurrence'], -x[1]['count'])
        )
        
        # Add data rows
        for word, data in sorted_words:
            # Get earliest date if available
            date_str = min(data['dates']) if data['dates'] else ''
            ws.append([
                date_str,
                word,
                data['count'],
                data['first_occurrence']
            ])
        
        # Auto-fit columns
        ws.column_dimensions['A'].width = 20  # Date
        ws.column_dimensions['B'].width = 20  # Term
        ws.column_dimensions['C'].width = 12  # Count
        ws.column_dimensions['D'].width = 20  # First Occurrence
        
        # Save
        report_file = self.output_dir / f"word-frequency-index-{self.timestamp}.xlsx"
        wb.save(report_file)
        
        return report_file
    
    def process_all(self):
        """Process all duplicate files"""
        duplicate_files = list(self.duplicate_dir.glob("*.csv"))
        
        if not duplicate_files:
            print(f"[ERROR] No duplicate CSV files found in {self.duplicate_dir}")
            return False
        
        print(f"Found {len(duplicate_files)} duplicate files to analyze\n")
        
        all_word_data = defaultdict(lambda: {
            'count': 0,
            'first_occurrence': float('inf'),
            'dates': set()
        })
        
        for dup_file in duplicate_files:
            print(f"Analyzing: {dup_file.name}")
            word_data = self.analyze_duplicate(dup_file)
            
            # Merge word data
            for word, data in word_data.items():
                all_word_data[word]['count'] += data['count']
                all_word_data[word]['first_occurrence'] = min(
                    all_word_data[word]['first_occurrence'],
                    data['first_occurrence']
                )
                all_word_data[word]['dates'].update(data['dates'])
            
            print(f"  Found {len(word_data)} unique words\n")
        
        # Create report
        report_file = self.create_frequency_report(dict(all_word_data))
        
        print(f"[SUCCESS] Word frequency analysis complete")
        print(f"  Total unique words: {len(all_word_data)}")
        print(f"  Report: {report_file.name}")
        print(f"  Location: {self.output_dir}")
        
        return True


if __name__ == '__main__':
    analyzer = WordFrequencyAnalyzer()
    success = analyzer.process_all()
    exit(0 if success else 1)
