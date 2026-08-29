#!/usr/bin/env python3
"""
Process 4: Convert CSV to Word (.docx)
- Keep original CSV untouched
- Create duplicate for processing
- Convert to Word format with simple formatting
- Use lock.json versioning
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import csv
from datetime import datetime

class CSVToWordConverter:
    def __init__(self):
        # Input: raw extracted CSVs
        self.input_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-raw-export")
        
        # Output: duplicates for processing
        self.duplicate_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-processed-duplicates")
        self.duplicate_dir.mkdir(parents=True, exist_ok=True)
        
        # Final word documents
        self.word_output_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-word-exports")
        self.word_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def convert_csv_to_word(self, csv_file: Path) -> bool:
        """Convert single CSV to .docx"""
        try:
            # Read CSV
            rows = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                print(f"[ERROR] CSV is empty: {csv_file.name}")
                return False
            
            # Create Word document
            doc = Document()
            
            # Add header
            title = doc.add_heading(f'Copilot Chat History - {csv_file.stem}', level=1)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            metadata = doc.add_paragraph()
            metadata.add_run(f"Exported: {datetime.now().isoformat()}\n")
            metadata.add_run(f"Source: {csv_file.name}\n")
            metadata.add_run(f"Records: {len(rows)}\n")
            metadata.add_run(f"Version: 1.0 (lock.json)\n")
            
            doc.add_paragraph()  # Blank line
            
            # Add table with headers
            columns = list(rows[0].keys())
            table = doc.add_table(rows=1, cols=len(columns))
            table.style = 'Light Grid Accent 1'
            
            # Header row
            hdr_cells = table.rows[0].cells
            for i, col in enumerate(columns):
                hdr_cells[i].text = col
                # Format header
                for paragraph in hdr_cells[i].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Data rows
            for row_data in rows:
                row_cells = table.add_row().cells
                for i, col in enumerate(columns):
                    row_cells[i].text = str(row_data.get(col, ''))
            
            # Save document
            word_file = self.word_output_dir / f"{csv_file.stem}-{self.timestamp}.docx"
            doc.save(word_file)
            
            print(f"[OK] Converted to Word: {word_file.name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to convert {csv_file.name}: {e}")
            return False
    
    def create_duplicate_for_indexing(self, csv_file: Path) -> Path:
        """Create duplicate copy for word frequency analysis"""
        import shutil
        duplicate_file = self.duplicate_dir / f"{csv_file.stem}-DUPLICATE-{self.timestamp}.csv"
        shutil.copy2(csv_file, duplicate_file)
        print(f"[OK] Created duplicate: {duplicate_file.name}")
        return duplicate_file
    
    def process_all(self):
        """Process all CSV files"""
        csv_files = list(self.input_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"[ERROR] No CSV files found in {self.input_dir}")
            return False
        
        print(f"Found {len(csv_files)} CSV files to process\n")
        
        success_count = 0
        for csv_file in csv_files:
            print(f"Processing: {csv_file.name}")
            
            # Create duplicate for indexing (ORIGINAL STAYS UNTOUCHED)
            duplicate = self.create_duplicate_for_indexing(csv_file)
            
            # Convert to Word
            if self.convert_csv_to_word(csv_file):
                success_count += 1
            
            print()
        
        print(f"[SUCCESS] Processed {success_count}/{len(csv_files)} files")
        print(f"\nOutput directories:")
        print(f"  Word documents: {self.word_output_dir}")
        print(f"  Duplicates (for indexing): {self.duplicate_dir}")
        
        return success_count > 0


if __name__ == '__main__':
    converter = CSVToWordConverter()
    success = converter.process_all()
    exit(0 if success else 1)
