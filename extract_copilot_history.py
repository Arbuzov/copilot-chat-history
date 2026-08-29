#!/usr/bin/env python3
"""
Process 3: Extract Copilot Chat History
Reads from Copilot's SQLite database (session-store.db)
Exports verbatim content to external folder with all metadata retained
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class CopilotHistoryExtractor:
    def __init__(self):
        self.copilot_db_path = Path(
            r"C:\Users\April Peterson\AppData\Roaming\Code\User\globalStorage\GitHub.copilot-chat\session-store.db"
        )
        # Follow lock.json directory structure
        self.output_dir = Path(r"C:\Users\April Peterson\AppData\Local\ContentExportFramework\data\copilot\raw-export")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract(self):
        """Extract chat history from Copilot database"""
        if not self.copilot_db_path.exists():
            print(f"ERROR: Database not found at {self.copilot_db_path}")
            return False
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.copilot_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Try common table names
            chat_data = {}
            for table_name in ['conversations', 'messages', 'chat_sessions', 'chat_messages']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                try:
                    result = cursor.fetchall()
                    if result:
                        print(f"\n✓ Found data in table: {table_name}")
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        chat_data[table_name] = [dict(row) for row in rows]
                except Exception as e:
                    pass
            
            # Export data
            if chat_data:
                # Save as JSON (with all metadata)
                json_file = self.output_dir / f"copilot-history-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(chat_data, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n✓ Exported to: {json_file}")
                return True
            else:
                print("\nNo chat data found in database")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False

if __name__ == '__main__':
    extractor = CopilotHistoryExtractor()
    success = extractor.extract()
    exit(0 if success else 1)
