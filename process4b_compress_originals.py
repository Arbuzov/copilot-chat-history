#!/usr/bin/env python3
"""
Process 4B: Compress Original Files (After Duplicates Verified)
- Only runs AFTER duplicates are safely created
- Creates ZIP with checksums for integrity verification
- Stores SHA256 manifest
- Original CSVs can be deleted after compression
"""

import hashlib
import json
import zipfile
from pathlib import Path
from datetime import datetime

class OriginalFileCompressor:
    def __init__(self):
        self.raw_export_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-raw-export")
        self.duplicate_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-processed-duplicates")
        self.archive_dir = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-archives")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_duplicates_exist(self) -> bool:
        """Check that all originals have duplicates"""
        original_files = list(self.raw_export_dir.glob("*.csv"))
        
        print("[STEP 1] Verifying duplicates exist and are safe...")
        all_have_duplicates = True
        for orig_file in original_files:
            duplicates = list(self.duplicate_dir.glob(f"{orig_file.stem}*"))
            if duplicates:
                dup_file = duplicates[0]
                orig_size = orig_file.stat().st_size
                dup_size = dup_file.stat().st_size
                print(f"  [OK] {orig_file.name}")
                print(f"       Original: {orig_size:,} bytes")
                print(f"       Duplicate: {dup_size:,} bytes")
                
                if orig_size != dup_size:
                    print(f"       [ERROR] Size mismatch!")
                    all_have_duplicates = False
            else:
                print(f"  [ERROR] No duplicate found for {orig_file.name}")
                all_have_duplicates = False
        
        return all_have_duplicates
    
    def create_checksum_manifest(self, files_to_compress: list) -> dict:
        """Create manifest with checksums"""
        print("\n[STEP 2] Creating checksum manifest...")
        manifest = {
            'created_at': datetime.now().isoformat(),
            'version': '1.0',
            'files': {}
        }
        
        for file_path in files_to_compress:
            checksum = self.calculate_sha256(file_path)
            file_size = file_path.stat().st_size
            
            manifest['files'][file_path.name] = {
                'sha256': checksum,
                'size': file_size,
                'original_path': str(file_path)
            }
            print(f"  [OK] {file_path.name}")
            print(f"       SHA256: {checksum[:16]}...")
        
        return manifest
    
    def compress_to_zip(self, files_to_compress: list, manifest: dict) -> Path:
        """Create compressed archive with manifest"""
        print("\n[STEP 3] Creating compressed archive...")
        
        zip_file = self.archive_dir / f"copilot-originals-{self.timestamp}.zip"
        
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add each file
            for file_path in files_to_compress:
                zf.write(file_path, arcname=file_path.name)
                print(f"  [OK] Added {file_path.name}")
            
            # Add manifest inside archive
            manifest_json = json.dumps(manifest, indent=2)
            zf.writestr('INTEGRITY_MANIFEST.json', manifest_json)
            print(f"  [OK] Added INTEGRITY_MANIFEST.json")
        
        original_size = sum(f.stat().st_size for f in files_to_compress)
        compressed_size = zip_file.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        print(f"\n[COMPRESSION STATS]")
        print(f"  Original total: {original_size:,} bytes")
        print(f"  Compressed: {compressed_size:,} bytes")
        print(f"  Saved: {original_size - compressed_size:,} bytes ({compression_ratio:.1f}%)")
        
        return zip_file
    
    def verify_archive_integrity(self, zip_file: Path, manifest: dict) -> bool:
        """Verify compressed archive integrity"""
        print(f"\n[STEP 4] Verifying archive integrity...")
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            # Extract and verify each file
            for filename, file_info in manifest['files'].items():
                try:
                    file_data = zf.read(filename)
                    calculated_hash = hashlib.sha256(file_data).hexdigest()
                    stored_hash = file_info['sha256']
                    
                    if calculated_hash == stored_hash:
                        print(f"  [OK] {filename} - Checksum verified")
                    else:
                        print(f"  [ERROR] {filename} - Checksum mismatch!")
                        return False
                except KeyError:
                    print(f"  [ERROR] {filename} - Not found in archive!")
                    return False
        
        return True
    
    def save_manifest_externally(self, manifest: dict):
        """Save manifest outside archive for reference"""
        manifest_file = self.archive_dir / f"INTEGRITY_MANIFEST-{self.timestamp}.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"\n[OK] Manifest saved: {manifest_file.name}")
    
    def process_compression(self, delete_originals: bool = False):
        """Complete compression workflow"""
        print("=" * 60)
        print("COMPRESS ORIGINAL FILES (After Duplicates Verified)")
        print("=" * 60)
        
        # Step 1: Verify duplicates exist
        if not self.verify_duplicates_exist():
            print("\n[FATAL] Duplicates not verified! Aborting compression.")
            return False
        
        # Step 2: Get files to compress
        files_to_compress = list(self.raw_export_dir.glob("*.csv"))
        if not files_to_compress:
            print("\n[ERROR] No CSV files found to compress")
            return False
        
        # Step 3: Create manifest with checksums
        manifest = self.create_checksum_manifest(files_to_compress)
        
        # Step 4: Compress to ZIP
        zip_file = self.compress_to_zip(files_to_compress, manifest)
        
        # Step 5: Verify archive integrity
        if not self.verify_archive_integrity(zip_file, manifest):
            print("\n[FATAL] Archive verification failed! Not deleting originals.")
            return False
        
        # Step 6: Save manifest externally
        self.save_manifest_externally(manifest)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Compression complete and verified")
        print("=" * 60)
        print(f"\nArchive: {zip_file.name}")
        print(f"Location: {self.archive_dir}")
        print(f"\nIntegrity manifest saved for future verification")
        
        if delete_originals:
            print("\n[WARNING] Original files NOT deleted (safety: user must delete manually)")
            print(f"When ready, you can delete: {self.raw_export_dir}")
        
        return True


if __name__ == '__main__':
    compressor = OriginalFileCompressor()
    success = compressor.process_compression(delete_originals=False)
    exit(0 if success else 1)
