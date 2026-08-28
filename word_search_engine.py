#!/usr/bin/env python3
"""
Word Search Engine for Content Export Framework
Full-text indexing and searching across all exported content
Supports complex queries: AND, OR, phrases, wildcards, case-insensitive
"""

import os
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class WordSearchEngine:
    def __init__(self, 
                 data_dir: str = './data',
                 db_path: str = './data/search-indexes/content.db'):
        """
        Initialize search engine
        
        Args:
            data_dir: Root data directory
            db_path: Path to SQLite search index database
        """
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path('./logs/search')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for indexing"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector TEXT,
                user_id TEXT,
                export_date TEXT,
                filename TEXT,
                file_path TEXT,
                content_hash TEXT UNIQUE,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Full-text index table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                doc_id INTEGER,
                position INTEGER,
                frequency INTEGER DEFAULT 1,
                FOREIGN KEY (doc_id) REFERENCES documents(id),
                UNIQUE(word, doc_id, position)
            )
        ''')
        
        # Phrase index (for quoted searches)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phrase_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT NOT NULL,
                doc_id INTEGER,
                first_word_position INTEGER,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        ''')
        
        # Search history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results_count INTEGER,
                search_time_ms REAL,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON word_index(word)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc ON word_index(doc_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_phrase ON phrase_index(phrase)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sector ON documents(sector)')
        
        conn.commit()
        conn.close()
        
        print(f"✓ Search database initialized: {self.db_path}")

    def index_exports(self, sector: str = None) -> Dict[str, Any]:
        """
        Index all exported content (from Process 4)
        
        Args:
            sector: Specific sector to index, or None for all
            
        Returns:
            Indexing result with stats
        """
        try:
            exports_dir = self.data_dir / 'formatted-exports'
            
            if not exports_dir.exists():
                return {'status': 'failed', 'error': f"Exports directory not found: {exports_dir}"}
            
            # Find all export files
            sectors_to_index = [sector] if sector else self._get_sectors(exports_dir)
            
            total_docs = 0
            total_words = 0
            
            for sec in sectors_to_index:
                sector_dir = exports_dir / sec
                
                if not sector_dir.exists():
                    continue
                
                # Recursively find and index files
                for user_dir in sector_dir.iterdir():
                    if not user_dir.is_dir():
                        continue
                    
                    for export_session in user_dir.iterdir():
                        if not export_session.is_dir():
                            continue
                        
                        # Index JSON files
                        for json_file in export_session.glob('*.json'):
                            if 'MANIFEST' not in json_file.name:
                                words_indexed = self._index_file(
                                    json_file, 
                                    sector=sec,
                                    user_id=user_dir.name,
                                    export_date=export_session.name
                                )
                                total_docs += 1
                                total_words += words_indexed
            
            result = {
                'status': 'indexed',
                'total_documents': total_docs,
                'total_words_indexed': total_words,
                'sectors': sectors_to_index,
                'timestamp': datetime.now().isoformat()
            }
            
            self._log_search_event('index_complete', result)
            return result
        
        except Exception as e:
            self._log_search_event('index_error', {'error': str(e)})
            return {'status': 'error', 'error': str(e)}

    def _index_file(self, file_path: Path, sector: str, user_id: str, export_date: str) -> int:
        """Index a single file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract all text
            text = self._extract_from_json(data)
            
            # Hash for uniqueness
            content_hash = hash(text)
            
            # Insert document
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO documents 
                (sector, user_id, export_date, filename, file_path, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sector, user_id, export_date, file_path.name, str(file_path), content_hash))
            
            conn.commit()
            
            # Get doc_id
            cursor.execute('SELECT id FROM documents WHERE content_hash = ?', (content_hash,))
            doc_id = cursor.fetchone()[0]
            
            # Tokenize and index
            words = self._tokenize(text)
            word_positions = defaultdict(list)
            
            for pos, word in enumerate(words):
                if word not in word_positions:
                    word_positions[word].append(pos)
                else:
                    word_positions[word].append(pos)
            
            # Insert word index
            for word, positions in word_positions.items():
                for pos in positions:
                    cursor.execute('''
                        INSERT OR IGNORE INTO word_index 
                        (word, doc_id, position, frequency)
                        VALUES (?, ?, ?, ?)
                    ''', (word, doc_id, pos, len(positions)))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Indexed: {file_path.name} ({len(words)} words)")
            return len(words)
        
        except Exception as e:
            print(f"⚠ Could not index {file_path.name}: {e}")
            return 0

    def search(self, query: str, sector: str = None, limit: int = 100) -> Dict[str, Any]:
        """
        Execute search query
        Supports: AND, OR, phrases, wildcards, case-insensitive
        
        Args:
            query: Search query (e.g., "python AND machine", '"exact phrase"', "search*")
            sector: Optional sector filter
            limit: Maximum results
            
        Returns:
            Search results with context
        """
        try:
            start_time = datetime.now()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Parse query
            results = self._execute_query(cursor, query, sector)
            
            # Get document details
            detailed_results = []
            for doc_id, word, position in results[:limit]:
                cursor.execute('SELECT sector, user_id, export_date, filename FROM documents WHERE id = ?', (doc_id,))
                doc_info = cursor.fetchone()
                
                if doc_info:
                    detailed_results.append({
                        'sector': doc_info[0],
                        'user_id': doc_info[1],
                        'export_date': doc_info[2],
                        'filename': doc_info[3],
                        'matched_word': word,
                        'context_position': position
                    })
            
            conn.close()
            
            # Log search
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            self._log_search_event('search_executed', {
                'query': query,
                'results': len(detailed_results),
                'time_ms': search_time
            })
            
            return {
                'status': 'success',
                'query': query,
                'results_count': len(detailed_results),
                'results': detailed_results,
                'search_time_ms': search_time,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self._log_search_event('search_error', {'error': str(e)})
            return {'status': 'error', 'error': str(e)}

    def _execute_query(self, cursor, query: str, sector: str = None) -> List[Tuple]:
        """Execute parsed query against index"""
        
        # Handle quoted phrases
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        
        query_clean = re.sub(phrase_pattern, '', query).strip()
        
        results = []
        
        # Phrase search
        for phrase in phrases:
            words = phrase.lower().split()
            sql = 'SELECT DISTINCT wi.doc_id, wi.word, wi.position FROM word_index wi JOIN documents d ON wi.doc_id = d.id WHERE d.word IN ({})'.format(
                ','.join('?' * len(words))
            )
            if sector:
                sql += f' AND d.sector = ?'
                cursor.execute(sql, words + [sector])
            else:
                cursor.execute(sql, words)
            
            results.extend(cursor.fetchall())
        
        # Regular word search (AND/OR)
        tokens = query_clean.split()
        
        for token in tokens:
            if token.upper() in ('AND', 'OR'):
                continue
            
            # Handle wildcards
            if '*' in token:
                pattern = token.replace('*', '%')
                sql = 'SELECT wi.doc_id, wi.word, wi.position FROM word_index wi JOIN documents d ON wi.doc_id = d.id WHERE wi.word LIKE ?'
            else:
                sql = 'SELECT wi.doc_id, wi.word, wi.position FROM word_index wi JOIN documents d ON wi.doc_id = d.id WHERE wi.word = ?'
            
            if sector:
                sql += f' AND d.sector = ?'
                cursor.execute(sql, (token.lower(), sector))
            else:
                cursor.execute(sql, (token.lower(),))
            
            results.extend(cursor.fetchall())
        
        return results

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable words"""
        
        text = text.lower()
        words = re.findall(r'\b[a-z0-9_-]+\b', text)
        return words

    def _extract_from_json(self, obj: Any) -> str:
        """Recursively extract text from JSON"""
        
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

    def _get_sectors(self, exports_dir: Path) -> List[str]:
        """Get list of available sectors"""
        return [d.name for d in exports_dir.iterdir() if d.is_dir()]

    def _log_search_event(self, event_type: str, data: Dict[str, Any]):
        """Log search events"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f'search-events-{today}.json'
        
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
            print(f"⚠ Failed to log search event: {e}")


if __name__ == '__main__':
    engine = WordSearchEngine()
    
    # Index all exports
    print("\n📑 Indexing content...")
    index_result = engine.index_exports()
    print(json.dumps(index_result, indent=2))
    
    # Example searches
    print("\n🔍 Executing searches...")
    
    search_queries = [
        'python',
        'machine learning',
        '"exact phrase search"',
        'python AND machine',
        'data*'
    ]
    
    for query in search_queries:
        print(f"\nSearching: {query}")
        result = engine.search(query, limit=10)
        print(f"  Found: {result.get('results_count')} results in {result.get('search_time_ms'):.2f}ms")
