#!/usr/bin/env python3
"""
Content Export Framework - Main Entry Point
Desktop activation from shortcut
Local + OneDrive sync for aprilapeterson@gmail.com
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from copilot_login_detector import CopilotLoginDetector
from copilot_auth_handler import CopilotAuthHandler
from copilot_history_downloader import CopilotHistoryDownloader
from copilot_content_exporter import CopilotContentExporter
from copilot_word_frequency_analyzer import CopilotWordFrequencyAnalyzer
from word_search_engine import WordSearchEngine
from onedrive_sync_manager import OneDriveSyncManager


class ContentExportFramework:
    def __init__(self):
        """Initialize framework with proper directory structure"""
        
        # Setup data directory (AppData)
        appdata = os.getenv('APPDATA')
        self.data_dir = Path(appdata) / 'ContentExportFramework' / 'data'
        self.config_dir = Path(appdata) / 'ContentExportFramework' / 'config'
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OneDrive sync
        self.onedrive_sync = OneDriveSyncManager(
            local_data_dir=str(self.data_dir),
            account_email='aprilapeterson@gmail.com'
        )
        
        # Initialize components
        self.login_detector = CopilotLoginDetector(
            log_dir=str(self.data_dir / 'logs' / 'process-1')
        )
        self.auth_handler = CopilotAuthHandler(
            config_file=str(self.config_dir / 'copilot-auth.json')
        )
        self.downloader = CopilotHistoryDownloader(
            output_dir=str(self.data_dir / 'raw-exports')
        )
        self.exporter = CopilotContentExporter(
            source_dir=str(self.data_dir / 'raw-exports'),
            export_base_dir=str(self.data_dir / 'formatted-exports')
        )
        self.analyzer = CopilotWordFrequencyAnalyzer(
            source_dir=str(self.data_dir / 'formatted-exports' / 'Copilot'),
            output_dir=str(self.data_dir / 'analysis')
        )
        self.search_engine = WordSearchEngine(
            data_dir=str(self.data_dir),
            db_path=str(self.data_dir / 'search-indexes' / 'content.db')
        )

    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("CONTENT EXPORT FRAMEWORK")
        print("="*60)
        print("\n📁 Data Location: " + str(self.data_dir))
        print("☁️  OneDrive Sync: aprilapeterson@gmail.com")
        print("\nOPTIONS:")
        print("  1. Start Copilot Export Pipeline (5 processes)")
        print("  2. Search Exported Content (Word Search)")
        print("  3. Sync to OneDrive (backup)")
        print("  4. Restore from OneDrive (recover data)")
        print("  5. Open Data Folder")
        print("  6. Settings")
        print("  7. Exit")
        print("\n" + "-"*60)

    def run_copilot_pipeline(self):
        """Execute full 5-process pipeline"""
        print("\n🚀 Starting Copilot Export Pipeline...")
        
        user_id = input("\nEnter user ID (or press Enter for 'default_user'): ").strip() or 'default_user'
        
        # Process 1: Login Detection
        print("\n[1/5] Login Detection...")
        login_event = {
            'userId': user_id,
            'sessionId': None,
            'source': 'manual_start'
        }
        self.login_detector.log_login_event(login_event)
        
        # Process 2: Authorization
        print("[2/5] Authorization...")
        auth_session = self.auth_handler.initiate_browser_auth()
        print("⏳ Waiting for browser authorization...")
        input("Press Enter after authorizing in browser...")
        token = self.auth_handler.get_stored_token()
        
        if not token:
            print("✗ Authorization failed")
            return
        
        # Process 3: Download
        print("[3/5] Downloading History...")
        self.downloader.token = token['access_token']
        download_result = self.downloader.download_history(user_id=user_id)
        
        if download_result.get('status') != 'saved':
            print(f"✗ Download failed: {download_result.get('error')}")
            return
        
        # Process 4: Export
        print("[4/5] Exporting Content...")
        export_result = self.exporter.export_copilot_history(user_id=user_id)
        
        if export_result.get('status') != 'exported':
            print(f"✗ Export failed: {export_result.get('error')}")
            return
        
        # Process 5: Analyze
        print("[5/5] Analyzing Word Frequency...")
        analysis_result = self.analyzer.analyze_history(user_id=user_id)
        
        if analysis_result.get('status') != 'analyzed':
            print(f"⚠ Analysis completed with warnings: {analysis_result.get('error')}")
        else:
            print("✓ Analysis complete")
        
        # Sync to OneDrive
        print("\n☁️  Syncing to OneDrive...")
        self.onedrive_sync.sync_to_onedrive('formatted-exports')
        self.onedrive_sync.sync_to_onedrive('analysis')
        
        print("\n✓ Pipeline complete!")
        print(f"📁 Data saved to: {self.data_dir}")

    def search_content(self):
        """Search exported content"""
        print("\n🔍 Content Search")
        print("Supported: keywords, 'exact phrases', AND/OR operators, wildcards*")
        
        query = input("\nEnter search query: ").strip()
        
        if not query:
            return
        
        # Index first
        print("\n📑 Indexing content...")
        self.search_engine.index_exports()
        
        # Search
        print("Searching...")
        result = self.search_engine.search(query, limit=20)
        
        if result.get('status') == 'success':
            print(f"\n✓ Found {result['results_count']} results in {result['search_time_ms']:.2f}ms")
            
            for idx, hit in enumerate(result['results'], 1):
                print(f"\n  {idx}. {hit['filename']}")
                print(f"     Platform: {hit['sector']}")
                print(f"     User: {hit['user_id']}")
                print(f"     Export: {hit['export_date']}")
                print(f"     Match: {hit['matched_word']}")
        else:
            print(f"✗ Search failed: {result.get('error')}")

    def sync_to_onedrive(self):
        """Sync data to OneDrive"""
        print("\n☁️  OneDrive Backup")
        print("Account: aprilapeterson@gmail.com")
        
        folders = ['formatted-exports', 'analysis', 'raw-exports']
        
        print("\nFolders to sync:")
        for idx, folder in enumerate(folders, 1):
            print(f"  {idx}. {folder}")
        
        choice = input("\nSync all? (y/n): ").strip().lower()
        
        if choice == 'y':
            for folder in folders:
                result = self.onedrive_sync.sync_to_onedrive(folder)
                if result.get('status') == 'synced':
                    print(f"✓ {folder}: {result['files_copied']} files")
                else:
                    print(f"⚠ {folder}: {result.get('message', result.get('error'))}")
        else:
            idx = int(input("Select folder (1-3): "))
            if 1 <= idx <= 3:
                result = self.onedrive_sync.sync_to_onedrive(folders[idx-1])
                print(f"✓ Synced: {result.get('files_copied')} files")

    def restore_from_onedrive(self):
        """Restore data from OneDrive"""
        print("\n☁️  OneDrive Restore")
        print("Account: aprilapeterson@gmail.com")
        print("\n⚠️  This will overwrite local files with newer OneDrive versions")
        
        confirm = input("\nContinue? (y/n): ").strip().lower()
        
        if confirm == 'y':
            result = self.onedrive_sync.sync_from_onedrive()
            if result.get('status') == 'restored':
                print(f"✓ Restored: {result['files_updated']} files updated")
            else:
                print(f"⚠ {result.get('message', result.get('error'))}")

    def open_data_folder(self):
        """Open data folder in explorer"""
        print(f"\n📁 Opening: {self.data_dir}")
        os.startfile(self.data_dir)

    def show_settings(self):
        """Show settings"""
        print("\n⚙️  Settings")
        print(f"Data Directory: {self.data_dir}")
        print(f"Config Directory: {self.config_dir}")
        print(f"OneDrive Account: aprilapeterson@gmail.com")
        
        # Show OneDrive config
        try:
            onedrive_config = self.onedrive_sync.config_file
            if onedrive_config.exists():
                with open(onedrive_config) as f:
                    config = json.load(f)
                    print(f"OneDrive Sync Enabled: {config.get('sync_enabled', True)}")
                    print(f"Background Sync: {config.get('background_sync', False)}")
        except:
            pass
        
        print("\nPress Enter to return...")
        input()

    def run(self):
        """Main loop"""
        while True:
            self.show_menu()
            choice = input("Select option (1-7): ").strip()
            
            if choice == '1':
                self.run_copilot_pipeline()
            elif choice == '2':
                self.search_content()
            elif choice == '3':
                self.sync_to_onedrive()
            elif choice == '4':
                self.restore_from_onedrive()
            elif choice == '5':
                self.open_data_folder()
            elif choice == '6':
                self.show_settings()
            elif choice == '7':
                print("\nGoodbye!")
                break
            else:
                print("Invalid option. Please try again.")


if __name__ == '__main__':
    try:
        app = ContentExportFramework()
        app.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
