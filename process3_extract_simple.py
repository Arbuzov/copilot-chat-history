#!/usr/bin/env python3
"""
Process 3: Extract Copilot Chat History
Read CSV, copy content verbatim to OUTPUT FOLDER
User-accessible location
"""

import shutil
from pathlib import Path

# User-accessible output folder (visible on Desktop/user home)
OUTPUT_DIR = Path(r"C:\Users\April Peterson\ContentExportFramework\copilot-raw-export")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Source folder with downloaded histories
SOURCE_DIR = Path(r"C:\Users\April Peterson\OneDrive\copilot Chat Exports pc to\copilot history download")

# Copy all CSV files verbatim
csv_files = SOURCE_DIR.glob("*.csv")
count = 0
for csv_file in csv_files:
    output_file = OUTPUT_DIR / csv_file.name
    shutil.copy2(csv_file, output_file)
    print(f"[OK] Copied: {csv_file.name}")
    print(f"     To: {output_file}")
    print(f"     Size: {output_file.stat().st_size} bytes")
    print()
    count += 1

print(f"[SUCCESS] All {count} files exported to:")
print(f"  {OUTPUT_DIR}")
print(f"\nThis folder is user-accessible and can be opened/edited directly.")
