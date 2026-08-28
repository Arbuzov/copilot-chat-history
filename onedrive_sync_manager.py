#!/usr/bin/env python3
"""
OneDrive Sync Handler for Content Export Framework
Syncs exported content to OneDrive (aprilapeterson@gmail.com account)
Local storage + cloud backup strategy
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import subprocess
import shutil

try:
    from onedrive_sdk.client import OneDriveClient
    from onedrive_sdk.auth_provider import MsAuthProvider
    HAS_ONEDRIVE_SDK = True
except ImportError:
    HAS_ONEDRIVE_SDK = False


class OneDriveSyncManager:
    def __init__(self,
                 local_data_dir: str = None,
                 onedrive_folder: str = 'ContentExportFramework',
                 account_email: str = 'aprilapeterson@gmail.com'):
        """
        Initialize OneDrive sync manager
        
        Args:
            local_data_dir: Local data directory (typically %APPDATA%/ContentExportFramework/data)
            onedrive_folder: Folder name in OneDrive root
            account_email: Microsoft account email
        """
        self.account_email = account_email
        self.onedrive_folder = onedrive_folder
        
        # Set local data directory
        if not local_data_dir:
            appdata = os.getenv('APPDATA')
            self.local_data_dir = Path(appdata) / 'ContentExportFramework' / 'data'
        else:
            self.local_data_dir = Path(local_data_dir)
        
        # OneDrive path (symlink or direct)
        self.onedrive_base = self._get_onedrive_path()
        self.onedrive_sync_dir = self.onedrive_base / onedrive_folder if self.onedrive_base else None
        
        self.log_dir = self.local_data_dir / 'logs' / 'onedrive'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.local_data_dir / 'onedrive-config.json'

    def _get_onedrive_path(self) -> Path:
        """
        Detect OneDrive folder location
        Searches common Windows paths
        """
        possible_paths = [
            Path.home() / 'OneDrive',
            Path.home() / 'Microsoft OneDrive',
            Path.home() / 'OneDrive - Personal',
            Path(os.getenv('OneDriveCommercial', '')),
            Path(os.getenv('OneDriveConsumer', ''))
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                print(f"✓ Found OneDrive: {path}")
                return path
        
        print("⚠ OneDrive not found in common locations")
        return None

    def setup_sync(self, enable_background: bool = True) -> Dict[str, Any]:
        """
        Setup OneDrive sync for exported content
        Creates folder structure and symbolic links
        
        Args:
            enable_background: Enable automatic sync on file changes
            
        Returns:
            Setup result
        """
        try:
            if not self.onedrive_base:
                return {
                    'status': 'warning',
                    'message': 'OneDrive not found. Manual sync only.',
                    'onedrive_path': None,
                    'local_path': str(self.local_data_dir)
                }
            
            # Create OneDrive folder structure
            onedrive_raw = self.onedrive_sync_dir / 'raw-exports'
            onedrive_formatted = self.onedrive_sync_dir / 'formatted-exports'
            onedrive_analysis = self.onedrive_sync_dir / 'analysis'
            
            for folder in [onedrive_raw, onedrive_formatted, onedrive_analysis]:
                folder.mkdir(parents=True, exist_ok=True)
            
            # Save config
            config = {
                'account_email': self.account_email,
                'onedrive_path': str(self.onedrive_base),
                'onedrive_folder': self.onedrive_folder,
                'local_data_path': str(self.local_data_dir),
                'sync_enabled': True,
                'background_sync': enable_background,
                'last_sync': datetime.now().isoformat(),
                'setup_date': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ OneDrive sync configured")
            print(f"  Account: {self.account_email}")
            print(f"  Local: {self.local_data_dir}")
            print(f"  OneDrive: {self.onedrive_sync_dir}")
            
            result = {
                'status': 'configured',
                'account_email': self.account_email,
                'onedrive_path': str(self.onedrive_sync_dir),
                'local_path': str(self.local_data_dir),
                'background_sync': enable_background,
                'config_file': str(self.config_file)
            }
            
            self._log_event('sync_setup', result)
            return result
        
        except Exception as e:
            self._log_event('setup_error', {'error': str(e)})
            return {'status': 'error', 'error': str(e)}

    def sync_to_onedrive(self, folder_type: str = 'formatted-exports') -> Dict[str, Any]:
        """
        Sync specific folder to OneDrive
        
        Args:
            folder_type: 'formatted-exports', 'analysis', or 'raw-exports'
            
        Returns:
            Sync result
        """
        try:
            if not self.onedrive_sync_dir:
                return {'status': 'warning', 'message': 'OneDrive not available'}
            
            local_folder = self.local_data_dir / folder_type
            onedrive_folder = self.onedrive_sync_dir / folder_type
            
            if not local_folder.exists():
                return {'status': 'warning', 'message': f'Local folder not found: {folder_type}'}
            
            onedrive_folder.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            copied_files = 0
            for file_path in local_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_folder)
                    dest_path = onedrive_folder / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(file_path, dest_path)
                        copied_files += 1
                    except Exception as e:
                        print(f"⚠ Could not copy {rel_path}: {e}")
            
            result = {
                'status': 'synced',
                'folder_type': folder_type,
                'files_copied': copied_files,
                'local_path': str(local_folder),
                'onedrive_path': str(onedrive_folder),
                'timestamp': datetime.now().isoformat()
            }
            
            self._log_event('sync_complete', result)
            return result
        
        except Exception as e:
            self._log_event('sync_error', {'error': str(e)})
            return {'status': 'error', 'error': str(e)}

    def sync_from_onedrive(self) -> Dict[str, Any]:
        """
        Sync latest from OneDrive to local (backup restore)
        """
        try:
            if not self.onedrive_sync_dir:
                return {'status': 'warning', 'message': 'OneDrive not available'}
            
            copied_files = 0
            
            for onedrive_file in self.onedrive_sync_dir.rglob('*'):
                if onedrive_file.is_file():
                    rel_path = onedrive_file.relative_to(self.onedrive_sync_dir)
                    local_file = self.local_data_dir / rel_path
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Only copy if OneDrive version is newer
                    if not local_file.exists() or onedrive_file.stat().st_mtime > local_file.stat().st_mtime:
                        shutil.copy2(onedrive_file, local_file)
                        copied_files += 1
            
            result = {
                'status': 'restored',
                'files_updated': copied_files,
                'timestamp': datetime.now().isoformat()
            }
            
            self._log_event('restore_complete', result)
            return result
        
        except Exception as e:
            self._log_event('restore_error', {'error': str(e)})
            return {'status': 'error', 'error': str(e)}

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log sync events"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f'sync-events-{today}.json'
        
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
            print(f"⚠ Failed to log sync event: {e}")


if __name__ == '__main__':
    sync_manager = OneDriveSyncManager(account_email='aprilapeterson@gmail.com')
    
    # Setup sync
    print("Setting up OneDrive sync...")
    setup_result = sync_manager.setup_sync()
    print(json.dumps(setup_result, indent=2))
    
    # Sync to OneDrive
    print("\nSyncing to OneDrive...")
    sync_result = sync_manager.sync_to_onedrive('formatted-exports')
    print(json.dumps(sync_result, indent=2))
