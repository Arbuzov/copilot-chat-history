#!/usr/bin/env python3
"""
Copilot Login Detection Process (Phase 1, Process 1)
Detects when user logs into web Copilot and triggers authorization flow
Independent module - logs events to JSON, does NOT execute download/export
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class CopilotLoginDetector:
    def __init__(self, log_dir: str = './logs/copilot-login'):
        self.log_dir = Path(log_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.log_dir / f'login-events-{today}.json'
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_login_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a login detection event to JSON file
        
        Args:
            event: Dict with userId, sessionId, and other event details
            
        Returns:
            The logged entry dict
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'login_detected',
            'platform': 'copilot',
            'userId': event.get('userId', 'unknown'),
            'sessionId': event.get('sessionId'),
            'eventDetails': event,
            'status': 'pending_authorization'  # Next process: p1-auth
        }

        try:
            events = []
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    events = json.load(f)

            events.append(log_entry)
            with open(self.log_file, 'w') as f:
                json.dump(events, f, indent=2)

            print(f"✓ Login event logged: {log_entry['timestamp']}")
            return log_entry

        except Exception as err:
            print(f"✗ Failed to log login event: {err}")
            raise

    def get_browser_detection_script(self) -> str:
        """
        Return browser JavaScript to detect Copilot login
        For use in browser extension or monitoring script
        """
        return """
// Browser script to detect Copilot login
(function() {
    const originalSetItem = Storage.prototype.setItem;
    
    Storage.prototype.setItem = function(key, value) {
        // Detect Copilot auth tokens or session markers
        if (key.includes('auth') || key.includes('session') || key.includes('copilot')) {
            if (value && !value.includes('undefined')) {
                const event = {
                    type: 'login_detected',
                    timestamp: new Date().toISOString(),
                    storageKey: key,
                    platform: 'copilot_web'
                };
                console.log('[Copilot Login Detector]', event);
                
                // Dispatch custom event for external monitoring
                window.dispatchEvent(new CustomEvent('copilot:login', { detail: event }));
            }
        }
        return originalSetItem.call(this, key, value);
    };
})();
        """

    def get_webhook_format(self) -> Dict[str, Any]:
        """
        Return webhook endpoint format for login notifications
        To be used by Process 2 (Authorization Handler)
        """
        return {
            'endpoint': '/webhook/copilot-login',
            'method': 'POST',
            'payload': {
                'userId': 'string (required)',
                'sessionId': 'string (optional)',
                'timestamp': 'ISO 8601',
                'platform': 'copilot',
                'triggerNextProcess': 'p1-auth'
            }
        }

    def read_pending_logins(self) -> list:
        """Read all login events with status='pending_authorization'"""
        if not self.log_file.exists():
            return []

        with open(self.log_file, 'r') as f:
            events = json.load(f)

        return [e for e in events if e.get('status') == 'pending_authorization']


if __name__ == '__main__':
    detector = CopilotLoginDetector()
    
    # Example: simulate a login event
    example_event = {
        'userId': 'user@example.com',
        'sessionId': 'sess_abc123',
        'source': 'browser_login_form'
    }
    
    detector.log_login_event(example_event)
    print('\nBrowser detection script:')
    print(detector.get_browser_detection_script())
    print('\nWebhook format for next process:')
    print(json.dumps(detector.get_webhook_format(), indent=2))
