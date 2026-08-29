#!/usr/bin/env python3
"""
Create Desktop Shortcut for ContentExportFramework
Points to main.py as entry point
"""

import os
from pathlib import Path
import json

# Desktop location
desktop = Path.home() / "Desktop"

# Shortcut target - main.py
target_script = Path(r"C:\Users\April Peterson\.copilot\repos\copilot-worktrees\copilot-chat-history\sahstaacked-laughing-journey\main.py")

# Create Windows .bat launcher (since we can't create .lnk directly easily)
bat_file = desktop / "ContentExportFramework.bat"
bat_content = f"""@echo off
cd /d "{target_script.parent}"
python "{target_script}"
pause
"""

with open(bat_file, 'w') as f:
    f.write(bat_content)

print(f"[OK] Created desktop launcher: {bat_file}")

# Also create a VBS shortcut wrapper for better UX (no console window)
vbs_file = desktop / "ContentExportFramework.vbs"
vbs_content = f"""Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{desktop}\\ContentExportFramework.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "python.exe"
oLink.Arguments = "{target_script}"
oLink.WorkingDirectory = "{target_script.parent}"
oLink.Description = "Content Export Framework - Extract and analyze chat histories"
oLink.Save
"""

with open(vbs_file, 'w') as f:
    f.write(vbs_content)

print(f"[OK] Created VBS helper: {vbs_file}")
print(f"\nTo create proper shortcut, run:")
print(f"  python {vbs_file}")
print(f"\nOr use .bat file directly:")
print(f"  {bat_file}")
