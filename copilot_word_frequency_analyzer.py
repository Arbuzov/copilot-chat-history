#!/usr/bin/env python3
"""
Copilot Word Frequency Analysis Process (Phase 1, Process 5)
Analyzes chat history content and generates word frequency report
Outputs: Excel (.xlsx) with word statistics
Excludes common stop words (the, a, but, and, or, etc.)
Columns: Date | Term/Word | Count | First Occurrence
Ordered: Earliest occurrence first, then by highest usage
Triggered by Process 4 (export success)
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import Counter

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    print("⚠ openpyxl not installed. Install: pip install openpyxl")


class CopilotWordFrequencyAnalyzer:
    def __init__(self, 
                 source_dir: str = './copilot-chat-exports/Copilot',
                 output_dir: str = './copilot-analysis'):
        """
        Initialize word frequency analyzer
        
        Args:
            source_dir: Directory with exported .docx/.xlsx files from Process 4
            output_dir: Directory for analysis output
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.log_dir = Path('./logs/copilot-analysis')
        
        if not HAS_OPENPYXL:
            raise ImportError("Missing dependencies. Install: pip install openpyxl")
        
        # Common English stop words
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
            'why', 'how', 'all', 'each', 'every', 'both', 'either', 'neither',
            'some', 'any', 'no', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'if', 'because', 'am', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out',
            'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our',
            'their', 'me', 'him', 'them', 'this', 'that', 'more', 'most', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
            'while', 'also', 'about', 'around', 'between', 'even', 'most', 'much',
            'must', 'now', 'should', 'such', 'that', 'them', 'then', 'these',
            'they', 'this', 'those', 'through', 'to', 'too', 'until', 'up',
            'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which',
            'while', 'who', 'will', 'with', 'would', 'you', 'your', 'as',
            'vs', 'etc', 'le', 'la', 'el', 'et', 'qu', 'na', 'de', 'da'
        }
        
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create required directories"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def analyze_history(self, user_id: str = 'default_user') -> Dict[str, Any]:
        """
        Analyze word frequency in exported history
        
        Args:
            user_id: User identifier
            
        Returns:
            Analysis result dict with file path and statistics
        """
        try:
            # Find source export directory
            user_source_dir = self.source_dir / user_id
            
            if not user_source_dir.exists():
                error = f"Source directory not found: {user_source_dir}"
                self._log_analysis_event('analysis_failed', {'error': error})
                print(f"✗ {error}")
                return {'status': 'failed', 'error': error}

            # Find latest export
            export_dirs = sorted([d for d in user_source_dir.iterdir() if d.is_dir()])
            
            if not export_dirs:
                error = f"No export directories found in {user_source_dir}"
                self._log_analysis_event('analysis_failed', {'error': error})
                print(f"✗ {error}")
                return {'status': 'failed', 'error': error}

            latest_export = export_dirs[-1]
            
            # Collect all text content from exported files
            text_content = self._extract_text_from_exports(latest_export)
            
            if not text_content:
                error = f"No content extracted from {latest_export}"
                self._log_analysis_event('analysis_failed', {'error': error})
                print(f"✗ {error}")
                return {'status': 'failed', 'error': error}

            # Analyze word frequency
            word_stats = self._analyze_words(text_content)
            
            # Export to Excel
            output_file = self._export_to_xlsx(user_id, word_stats, latest_export)

            result = {
                'status': 'analyzed',
                'user_id': user_id,
                'source_export': str(latest_export),
                'output_file': str(output_file),
                'total_words_analyzed': len(text_content.split()),
                'unique_terms': len(word_stats),
                'timestamp': datetime.now().isoformat()
            }

            self._log_analysis_event('analysis_success', result)

            print(f"\n✓ Analysis complete:")
            print(f"  Output: {output_file.name}")
            print(f"  Unique terms: {len(word_stats)}")
            print(f"  Total words: {len(text_content.split())}")

            return result

        except Exception as e:
            self._log_analysis_event('analysis_error', {'error': str(e)})
            print(f"✗ Analysis error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _extract_text_from_exports(self, export_dir: Path) -> str:
        """
        Extract all text content from exported files
        
        Args:
            export_dir: Directory containing exported .docx/.xlsx files
            
        Returns:
            Combined text content
        """
        all_text = []
        
        # Try to extract from JSON files first (most reliable)
        json_files = list(export_dir.glob('*.json'))
        for json_file in json_files:
            if 'MANIFEST' not in json_file.name:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract all message content
                    text = self._extract_from_json(data)
                    all_text.append(text)
                except Exception as e:
                    print(f"⚠ Could not read {json_file.name}: {e}")
        
        # Try XML files as fallback
        xml_files = list(export_dir.glob('*.xml'))
        for xml_file in xml_files:
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract text between tags (basic XML parsing)
                    all_text.append(re.sub(r'<[^>]+>', ' ', content))
            except Exception as e:
                print(f"⚠ Could not read {xml_file.name}: {e}")
        
        return ' '.join(all_text)

    def _extract_from_json(self, obj: Any) -> str:
        """
        Recursively extract all text from JSON structure
        
        Args:
            obj: JSON object
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ['content', 'message', 'text', 'body', 'title']:
                    text_parts.append(str(value))
                elif isinstance(value, (dict, list)):
                    text_parts.append(self._extract_from_json(value))
        
        elif isinstance(obj, list):
            for item in obj:
                text_parts.append(self._extract_from_json(item))
        
        elif isinstance(obj, str):
            text_parts.append(obj)
        
        return ' '.join(text_parts)

    def _analyze_words(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze word frequency
        Exclude stop words, normalize case
        
        Args:
            text: Text content to analyze
            
        Returns:
            Sorted list of word stats dicts
        """
        # Normalize: lowercase, remove punctuation
        text = text.lower()
        # Keep alphanumeric and basic punctuation
        words = re.findall(r'\b[a-z0-9_-]+\b', text)
        
        # Filter stop words and short words
        filtered_words = [
            w for w in words 
            if w not in self.stop_words and len(w) > 2
        ]
        
        # Count occurrences
        word_counter = Counter(filtered_words)
        
        # Build stats with first occurrence tracking
        word_stats = []
        word_first_pos = {}
        
        for idx, word in enumerate(filtered_words):
            if word not in word_first_pos:
                word_first_pos[word] = idx
        
        for word, count in word_counter.most_common():
            word_stats.append({
                'term': word,
                'count': count,
                'first_occurrence': word_first_pos[word],
                'date': datetime.now().isoformat()
            })
        
        # Sort: earliest occurrence first, then by highest usage
        word_stats.sort(key=lambda x: (x['first_occurrence'], -x['count']))
        
        return word_stats

    def _export_to_xlsx(self, 
                       user_id: str, 
                       word_stats: List[Dict[str, Any]],
                       source_export: Path) -> Path:
        """
        Export word frequency analysis to Excel
        Columns: Date | Term/Word | Count | First Occurrence
        
        Args:
            user_id: User identifier
            word_stats: List of word statistics
            source_export: Source export directory
            
        Returns:
            Path to created .xlsx file
        """
        wb = openpyxl.Workbook()
        
        # Metadata sheet
        ws_meta = wb.active
        ws_meta.title = "Analysis Metadata"
        
        meta_data = [
            ['Word Frequency Analysis Report', ''],
            ['User ID', user_id],
            ['Analysis Date', datetime.now().isoformat()],
            ['Source Export', source_export.name],
            ['Total Unique Terms', len(word_stats)],
            ['Methodology', 'Stop words excluded, ordered by first occurrence then usage count'],
            ['', ''],
            ['Columns', 'Date | Term | Count | First Occurrence Position']
        ]
        
        for idx, row in enumerate(meta_data, 1):
            for col_idx, val in enumerate(row, 1):
                cell = ws_meta.cell(row=idx, column=col_idx, value=val)
                if idx <= 6 and col_idx == 1:
                    cell.font = Font(bold=True)
        
        # Analysis sheet
        ws_analysis = wb.create_sheet("Word Frequency")
        
        # Headers
        headers = ['Date', 'Term/Word', 'Count', 'First Occurrence Position']
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws_analysis.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Data rows
        for row_idx, stat in enumerate(word_stats, 2):
            ws_analysis.cell(row=row_idx, column=1, value=stat['date'])
            ws_analysis.cell(row=row_idx, column=2, value=stat['term'])
            ws_analysis.cell(row=row_idx, column=3, value=stat['count'])
            ws_analysis.cell(row=row_idx, column=4, value=stat['first_occurrence'])
            
            # Alternate row colors for readability
            if row_idx % 2 == 0:
                fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
                for col in range(1, 5):
                    ws_analysis.cell(row=row_idx, column=col).fill = fill
        
        # Column widths
        ws_analysis.column_dimensions['A'].width = 25
        ws_analysis.column_dimensions['B'].width = 20
        ws_analysis.column_dimensions['C'].width = 12
        ws_analysis.column_dimensions['D'].width = 20
        
        # Freeze header row
        ws_analysis.freeze_panes = 'A2'
        
        # Save
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f'word-frequency-analysis-{user_id}-{timestamp}.xlsx'
        wb.save(output_file)
        
        print(f"✓ Analysis report created: {output_file.name}")
        return output_file

    def _log_analysis_event(self, event_type: str, data: Dict[str, Any]):
        """Log analysis events"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f'analysis-events-{today}.json'

        try:
            events = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    events = json.load(f)

            event_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': data
            }

            events.append(event_entry)
            with open(log_file, 'w') as f:
                json.dump(events, f, indent=2)

        except Exception as e:
            print(f"⚠ Failed to log analysis event: {e}")


if __name__ == '__main__':
    analyzer = CopilotWordFrequencyAnalyzer()
    result = analyzer.analyze_history(user_id='default_user')
    print(json.dumps(result, indent=2))
