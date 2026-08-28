#!/usr/bin/env python3
"""
Copilot History Download Process (Phase 1, Process 3)
Downloads chat histories from Copilot Privacy tab
Stores to local folder in Excel/XML format
Independent module - triggered by Process 2 (auth success)
Does NOT process or export content, only downloads verbatim
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests


class CopilotHistoryDownloader:
    def __init__(self, 
                 token: str = None,
                 output_dir: str = './data/copilot-raw-export',
                 api_base: str = 'https://api.github.com'):
        """
        Initialize history downloader
        
        Args:
            token: GitHub OAuth access token (from Process 2)
            output_dir: Directory to store downloaded histories
            api_base: GitHub API base URL
        """
        self.token = token
        self.output_dir = Path(output_dir)
        self.api_base = api_base
        self.headers = {
            'Authorization': f'Bearer {token}' if token else '',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self.log_dir = Path('./logs/copilot-download')
        
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create required directories"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def download_history(self, user_id: str = None) -> Dict[str, Any]:
        """
        Download Copilot chat history from Privacy tab
        Endpoint: /user/copilot_chat_history or similar
        
        Args:
            user_id: Optional user ID (for multi-account support)
            
        Returns:
            Download result dict with status, file path, record count
        """
        if not self.token:
            raise ValueError("No access token provided. Run Process 2 (Authorization) first.")

        try:
            # Attempt to fetch history from GitHub API
            # Note: Copilot history endpoint may vary or require special permissions
            endpoint = f"{self.api_base}/user/copilot_chat_history"
            
            print(f"📥 Requesting history from: {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                history_data = response.json()
                result = self._save_history(history_data, user_id)
                self._log_download_event('download_success', result)
                return result

            elif response.status_code == 401:
                error = 'Unauthorized - token expired or invalid'
                self._log_download_event('download_failed', {'error': error})
                print(f"✗ {error}")
                return {'status': 'failed', 'error': error}

            elif response.status_code == 404:
                error = 'History endpoint not found - may require special Copilot permissions'
                self._log_download_event('download_failed', {'error': error})
                print(f"⚠ {error}")
                return {'status': 'not_available', 'error': error}

            else:
                error = f"API error: {response.status_code}"
                self._log_download_event('download_failed', {'error': error})
                print(f"✗ {error}")
                return {'status': 'failed', 'error': error}

        except Exception as e:
            self._log_download_event('download_error', {'error': str(e)})
            print(f"✗ Download error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _save_history(self, history_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """
        Save downloaded history to local folder
        Preserves verbatim content in JSON and XML formats
        
        Args:
            history_data: Raw history data from API
            user_id: Optional user ID for file naming
            
        Returns:
            Save result dict
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_folder = user_id or 'default_user'
        user_dir = self.output_dir / user_folder
        user_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSON (verbatim)
        json_file = user_dir / f'copilot-history-{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

        # Save as XML (verbatim content structure)
        xml_file = user_dir / f'copilot-history-{timestamp}.xml'
        xml_content = self._convert_to_xml(history_data)
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        record_count = len(history_data.get('conversations', []))

        result = {
            'status': 'saved',
            'user_id': user_folder,
            'json_file': str(json_file),
            'xml_file': str(xml_file),
            'record_count': record_count,
            'timestamp': timestamp,
            'next_process': 'p1-extract'  # Trigger Process 4
        }

        print(f"✓ History saved:")
        print(f"  JSON: {json_file}")
        print(f"  XML: {xml_file}")
        print(f"  Records: {record_count}")

        return result

    def _convert_to_xml(self, data: Dict[str, Any]) -> str:
        """
        Convert JSON history to XML format
        Preserves all content verbatim
        """
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<copilot_history>')
        xml_lines.append(f'  <exported_at>{datetime.now().isoformat()}</exported_at>')

        if isinstance(data, dict):
            for key, value in data.items():
                xml_lines.append(f'  <{key}>')
                xml_lines.extend(self._dict_to_xml_lines(value, indent=4))
                xml_lines.append(f'  </{key}>')
        
        xml_lines.append('</copilot_history>')
        return '\n'.join(xml_lines)

    def _dict_to_xml_lines(self, obj: Any, indent: int = 4) -> List[str]:
        """Recursive helper to convert object to XML lines"""
        lines = []
        prefix = ' ' * indent

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    lines.append(f'{prefix}<{key}>')
                    lines.extend(self._dict_to_xml_lines(value, indent + 2))
                    lines.append(f'{prefix}</{key}>')
                else:
                    safe_key = key.replace(' ', '_').lower()
                    safe_value = str(value).replace('<', '&lt;').replace('>', '&gt;')
                    lines.append(f'{prefix}<{safe_key}>{safe_value}</{safe_key}>')

        elif isinstance(obj, list):
            for item in obj:
                lines.append(f'{prefix}<item>')
                lines.extend(self._dict_to_xml_lines(item, indent + 2))
                lines.append(f'{prefix}</item>')

        else:
            safe_value = str(obj).replace('<', '&lt;').replace('>', '&gt;')
            lines.append(f'{prefix}{safe_value}')

        return lines

    def _log_download_event(self, event_type: str, data: Dict[str, Any]):
        """Log download events"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f'download-events-{today}.json'

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
            print(f"⚠ Failed to log download event: {e}")


if __name__ == '__main__':
    # Example usage (requires valid token from Process 2)
    import sys

    token = os.getenv('COPILOT_AUTH_TOKEN')
    if not token:
        print("⚠ COPILOT_AUTH_TOKEN environment variable not set")
        print("   Run Process 2 (Authorization) first, then set token")
        sys.exit(1)

    downloader = CopilotHistoryDownloader(token=token)
    result = downloader.download_history(user_id='default_user')
    print(json.dumps(result, indent=2))
