#!/usr/bin/env python3
"""
Copilot Authorization Handler (Phase 1, Process 2)
Handles authorization requests (GitHub sign-in/PC integration model)
Separate per platform - does NOT download or export, only auth
Independent module triggered by login detection (Process 1)
"""

import os
import json
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen, Request


class CopilotAuthHandler:
    def __init__(self, 
                 client_id: str = None,
                 client_secret: str = None,
                 config_file: str = './config/copilot-auth.json'):
        """
        Initialize auth handler
        
        Args:
            client_id: GitHub OAuth client ID (or load from config)
            client_secret: GitHub OAuth client secret (or load from config)
            config_file: Path to config file with credentials
        """
        self.config_file = Path(config_file)
        self.log_dir = Path('./logs/copilot-auth')
        self.token_dir = Path('./tokens/copilot')
        
        # Load from config or use provided
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = 'http://localhost:8000/callback'
        self.platform = 'copilot'
        
        self._ensure_dirs()
        self._load_config()

    def _ensure_dirs(self):
        """Create required directories"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.token_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """Load credentials from config file if exists"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.client_id = config.get('client_id') or self.client_id
                self.client_secret = config.get('client_secret') or self.client_secret
                self.redirect_uri = config.get('redirect_uri', self.redirect_uri)
            except Exception as e:
                print(f"⚠ Could not load config: {e}")

    def generate_auth_url(self, state: str = None) -> str:
        """
        Generate GitHub OAuth authorization URL
        (mimicking GitHub sign-in / PC integration model)
        
        Args:
            state: CSRF protection state parameter
            
        Returns:
            Full authorization URL
        """
        if not state:
            import uuid
            state = str(uuid.uuid4())

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'read:user read:org',  # Minimal scopes for reading history
            'state': state,
            'allow_signup': 'true'
        }

        auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        return auth_url

    def initiate_browser_auth(self) -> Dict[str, Any]:
        """
        Initiate browser-based authentication flow
        Mimics GitHub/PC sign-in pattern
        
        Returns:
            Auth session dict with state, timestamp, waiting status
        """
        import uuid
        state = str(uuid.uuid4())
        
        auth_session = {
            'session_id': state,
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform,
            'state': state,
            'status': 'awaiting_browser_callback',
            'auth_url': self.generate_auth_url(state)
        }

        # Log the auth initiation
        self._log_auth_event('auth_initiated', auth_session)

        # Open browser
        try:
            webbrowser.open(auth_session['auth_url'])
            print(f"✓ Browser opened for authorization")
            print(f"If browser didn't open, visit: {auth_session['auth_url']}")
        except Exception as e:
            print(f"⚠ Could not open browser: {e}")
            print(f"Visit manually: {auth_session['auth_url']}")

        return auth_session

    def handle_callback(self, code: str, state: str) -> Optional[Dict[str, Any]]:
        """
        Handle OAuth callback from GitHub
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from GitHub
            state: State parameter for verification
            
        Returns:
            Access token dict or None if failed
        """
        try:
            # Verify state (CSRF protection)
            # In production: verify against session store
            
            # Exchange code for token
            token_url = "https://github.com/login/oauth/access_token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': self.redirect_uri,
                'state': state
            }

            req = Request(
                token_url,
                data=urlencode(data).encode('utf-8'),
                headers={'Accept': 'application/json'}
            )

            with urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))

            if 'access_token' in response_data:
                token_data = {
                    'access_token': response_data['access_token'],
                    'token_type': response_data.get('token_type', 'bearer'),
                    'scope': response_data.get('scope', ''),
                    'timestamp': datetime.now().isoformat(),
                    'platform': self.platform,
                    'status': 'authorized'
                }

                # Save token securely
                self._save_token(token_data)
                self._log_auth_event('auth_success', token_data)

                print(f"✓ Authorization successful")
                return token_data
            else:
                error = response_data.get('error_description', 'Unknown error')
                self._log_auth_event('auth_failed', {'error': error})
                print(f"✗ Authorization failed: {error}")
                return None

        except Exception as e:
            self._log_auth_event('auth_error', {'error': str(e)})
            print(f"✗ Error handling callback: {e}")
            return None

    def get_stored_token(self) -> Optional[Dict[str, Any]]:
        """Retrieve stored access token if available"""
        token_file = self.token_dir / 'access_token.json'
        
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Could not read token: {e}")
        
        return None

    def _save_token(self, token_data: Dict[str, Any]):
        """Save token securely (basic JSON, should use encryption in production)"""
        token_file = self.token_dir / 'access_token.json'
        
        try:
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            # Restrict permissions (Unix-like systems)
            os.chmod(token_file, 0o600)
            print(f"✓ Token saved: {token_file}")
        except Exception as e:
            print(f"✗ Failed to save token: {e}")

    def _log_auth_event(self, event_type: str, data: Dict[str, Any]):
        """Log authorization events"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f'auth-events-{today}.json'

        try:
            events = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    events = json.load(f)

            event_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'platform': self.platform,
                'data': data
            }

            events.append(event_entry)
            with open(log_file, 'w') as f:
                json.dump(events, f, indent=2)

        except Exception as e:
            print(f"⚠ Failed to log auth event: {e}")


if __name__ == '__main__':
    # Example usage
    handler = CopilotAuthHandler(
        client_id='your_github_client_id',
        client_secret='your_github_client_secret'
    )

    # Initiate authorization
    auth_session = handler.initiate_browser_auth()
    print(json.dumps(auth_session, indent=2))

    # After user authorizes and callback is received:
    # handler.handle_callback(code='auth_code_from_github', state=auth_session['state'])

    # Check for stored token
    token = handler.get_stored_token()
    if token:
        print("✓ Stored token found")
    else:
        print("ℹ No stored token (awaiting authorization)")
