#!/usr/bin/env python3
"""
Process 3: Extract Copilot Chat History from CSV
Reads downloaded CSV files from Copilot website export
Preserves ALL metadata and attributes verbatim
Exports to user-accessible folder following lock.json directory structure
STANDALONE EXECUTABLE - can run independently
"""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

class CopilotCSVExtractor:
    """Extract Copilot chat history from CSV format with full metadata preservation"""
    
    def __init__(self):
        # lock.json specifies: AppData\Local\ContentExportFramework\data\copilot\raw-export
        self.output_dir = Path(
            r"C:\Users\April Peterson\AppData\Local\ContentExportFramework\data\copilot\raw-export"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def extract_csv(self, csv_file_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Extract Copilot CSV export file
        Preserve all columns, metadata, formatting
        
        Args:
            csv_file_path: Path to downloaded CSV file
            
        Returns:
            (success: bool, result: dict with file paths and record count)
        """
        csv_path = Path(csv_file_path)
        
        if not csv_path.exists():
            return False, {'error': f'File not found: {csv_file_path}'}
        
        try:
            # Read CSV preserving all data
            conversations = []
            metadata = {
                'source_file': str(csv_path),
                'extracted_at': datetime.now().isoformat(),
                'total_records': 0,
                'columns': []
            }
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                metadata['columns'] = reader.fieldnames or []
                
                for row_num, row in enumerate(reader, start=2):  # start=2 (skip header)
                    # Preserve verbatim - no modifications
                    conversations.append({
                        'row_number': row_num,
                        **row
                    })
            
            metadata['total_records'] = len(conversations)
            
            if not conversations:
                return False, {'error': 'CSV file is empty'}
            
            # Export as JSON (preserves all metadata and formatting)
            json_result = self._save_json(csv_path.stem, conversations, metadata)
            
            # Export as XML (preserves structure and metadata)
            xml_result = self._save_xml(csv_path.stem, conversations, metadata)
            
            result = {
                'success': True,
                'source_file': str(csv_path),
                'json_file': json_result,
                'xml_file': xml_result,
                'total_records': metadata['total_records'],
                'columns': metadata['columns'],
                'output_dir': str(self.output_dir)
            }
            
            print(f"[OK] Successfully extracted: {csv_path.name}")
            print(f"  Records: {metadata['total_records']}")
            print(f"  Columns: {', '.join(metadata['columns'])}")
            print(f"  JSON export: {json_result}")
            print(f"  XML export: {xml_result}")
            
            return True, result
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def _save_json(self, base_name: str, data: List[Dict], metadata: Dict) -> str:
        """Save data as JSON with metadata"""
        json_file = self.output_dir / f"{base_name}-{self.timestamp}.json"
        
        # Clean BOM from all strings
        cleaned_data = []
        for record in data:
            cleaned_record = {}
            for key, value in record.items():
                if isinstance(value, str):
                    cleaned_record[key] = value.replace('\ufeff', '')
                else:
                    cleaned_record[key] = value
            cleaned_data.append(cleaned_record)
        
        export_data = {
            'metadata': metadata,
            'data': cleaned_data
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(json_file)
    
    def _save_xml(self, base_name: str, data: List[Dict], metadata: Dict) -> str:
        """Save data as XML with metadata"""
        xml_file = self.output_dir / f"{base_name}-{self.timestamp}.xml"
        
        # Create root element
        root = ET.Element('copilot_export')
        
        # Add metadata section
        meta_elem = ET.SubElement(root, 'metadata')
        for key, value in metadata.items():
            if key == 'columns':
                cols_elem = ET.SubElement(meta_elem, 'columns')
                for col in value:
                    col_elem = ET.SubElement(cols_elem, 'column')
                    col_elem.text = str(col)
            else:
                elem = ET.SubElement(meta_elem, key)
                elem.text = str(value)
        
        # Add data section (conversations)
        data_elem = ET.SubElement(root, 'conversations')
        for record in data:
            conv_elem = ET.SubElement(data_elem, 'conversation')
            for key, value in record.items():
                # Preserve verbatim - handle special characters
                elem = ET.SubElement(conv_elem, key.replace(' ', '_').lower())
                # Clean BOM and other special chars from value
                if value:
                    clean_value = str(value).replace('\ufeff', '')
                    elem.text = clean_value
                else:
                    elem.text = ''
        
        # Write with proper UTF-8 encoding
        tree = ET.ElementTree(root)
        tree.write(str(xml_file), encoding='utf-8', xml_declaration=True)
        
        return str(xml_file)


def main():
    """Main entry point - accepts CSV file as argument"""
    import sys
    
    if len(sys.argv) < 2:
        # Use latest downloaded file if no argument
        downloads_dir = Path(r"C:\Users\April Peterson\Downloads")
        csv_files = sorted(
            downloads_dir.glob("copilot-activity-history*.csv"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not csv_files:
            print("ERROR: No Copilot CSV files found in Downloads folder")
            print("Usage: python process3_extract_copilot_csv.py [csv_file_path]")
            sys.exit(1)
        
        csv_file = csv_files[0]
        print(f"Using latest downloaded file: {csv_file.name}")
    else:
        csv_file = sys.argv[1]
    
    extractor = CopilotCSVExtractor()
    success, result = extractor.extract_csv(str(csv_file))
    
    if success:
        print(f"\n[SUCCESS] Export complete")
        print(f"Output directory: {result['output_dir']}")
        print("\nExported files:")
        print(f"  - {Path(result['json_file']).name}")
        print(f"  - {Path(result['xml_file']).name}")
        sys.exit(0)
    else:
        print(f"\n[ERROR] Export failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
