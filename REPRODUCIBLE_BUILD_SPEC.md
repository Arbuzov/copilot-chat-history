# Reproducible Build Specification
## How Lock, Index, and Entry Points Enable Exact Reproducibility

---

## REPRODUCIBILITY GUARANTEE

**Given identical inputs:**
- lock.json (unchanged)
- index.json (unchanged)
- source code (unchanged)
- build environment (Python 3.8-3.10, PyInstaller 5.0+, Windows)

**Result: IDENTICAL .exe binary**

This is the entire purpose of separating Lock / Index / Entry Points.

---

## WHY THIS MATTERS

### Problem (without Lock/Index/Entry):
```
Build A (today):   ContentExportFramework_v1.0.exe
Build B (6 months):  ContentExportFramework_v1.0.exe
Are they the same? ❓ Unknown. Timestamps differ. Can't verify.
```

### Solution (with Lock/Index/Entry):
```
Build A (today):   lock.json + index.json → ContentExportFramework_v1.0.exe (SHA256: abc123...)
Build B (6 months): lock.json + index.json → ContentExportFramework_v1.0.exe (SHA256: abc123...)
Are they the same? ✓ YES. SHA256 matches. Verified.
```

---

## REPRODUCIBILITY CHECKLIST

Before tagging a release:

```bash
# Step 1: Verify lock.json is committed and unchanged
git show HEAD:lock.json > lock_committed.json
diff lock.json lock_committed.json
# Must be identical

# Step 2: Verify index.json is committed and unchanged
git show HEAD:index.json > index_committed.json
diff index.json index_committed.json
# Must be identical

# Step 3: Build the .exe
python build_exe.py

# Step 4: Compute SHA256 hash
certutil -hashfile dist/ContentExportFramework.exe SHA256
# Record: SHA256 (ContentExportFramework.exe) = ABC123...DEF789

# Step 5: Commit hash to git tag
git tag -a v1.0.0 \
  -m "Reproducible build. SHA256: ABC123...DEF789"

# Step 6: Later, verify reproducibility
# (same Python version, same PyInstaller version)
python build_exe.py
certutil -hashfile dist/ContentExportFramework.exe SHA256
# Must match: ABC123...DEF789
```

---

## WHAT lock.json LOCKS (Reproducibility)

```json
{
  "lock_version": "1.0",
  "packages": {
    "runtime_dependencies": [
      "python-docx>=0.8.11",
      "openpyxl>=3.8.0",
      "requests>=2.28.0"
    ]
  }
}
```

**Locked because:**
- ✓ Version pinned (`>=0.8.11` = "at least 0.8.11, no newer")
- ✓ Not latest (would change, breaking reproducibility)
- ✓ Not wildcard `*` (would be non-deterministic)
- ✓ Declared upfront (known before build starts)

**Result:** Same versions always installed → Same .exe.

---

## WHAT index.json LOCKS (Resolution)

```json
{
  "python-docx": {
    "version": "0.8.11",
    "source": "pypi",
    "included_in_exe": true,
    "compressed": true,
    "size_kb": 450
  }
}
```

**Locked because:**
- ✓ Version is concrete (`0.8.11`, not `>=`)
- ✓ Source is explicit (`pypi`, not "auto-find")
- ✓ Size recorded (audit trail if someone tries to swap it)
- ✓ Compression state recorded

**Result:** Index is immutable proof of what resolved.

---

## WHAT entry_points.json LOCKS (Execution)

```json
{
  "console_scripts": {
    "ContentExportFramework": {
      "module": "main",
      "class": "ContentExportFramework",
      "method": "run"
    }
  }
}
```

**Locked because:**
- ✓ Entry point is hardcoded (not auto-discovered)
- ✓ Single entry point (no ambiguity)
- ✓ No dynamic plugin loading
- ✓ Same code path every time

**Result:** Same execution flow always.

---

## VERIFICATION ACROSS TIME

### Build on Day 1:
```
$ python build_exe.py
$ certutil -hashfile dist/ContentExportFramework.exe SHA256
SHA256 (ContentExportFramework.exe) = 
  A1B2C3D4E5F6...7890ABCDEF01
```

### Build on Day 180 (different machine, different user):
```
$ python build_exe.py
$ certutil -hashfile dist/ContentExportFramework.exe SHA256
SHA256 (ContentExportFramework.exe) = 
  A1B2C3D4E5F6...7890ABCDEF01
```

### Questions Answered:
- ✓ "Did someone modify the source?" → Check hash
- ✓ "Did someone upgrade a dependency?" → Check index.json
- ✓ "Can I rebuild from source?" → Yes, lock + index + source code
- ✓ "What was in v1.0?" → Check git tag (lock + index at that point)
- ✓ "Is this safe to distribute?" → Yes, hash verified

---

## AUDIT TRAIL

Everything is documented:

```
git log --oneline
  - Commit 1: Add Process 1-5 modules
  - Commit 2: Create lock.json (declare universe)
  - Commit 3: Create index.json (resolve dependencies)
  - Commit 4: Create entry_points.json (define execution)
  - Commit 5: Build .exe and tag v1.0.0

git tag -l
  v1.0.0  (points to commit 5, with SHA256 hash in tag message)

git show v1.0.0
  Author: ...
  Date: ...
  Message: Reproducible build. SHA256: A1B2C3D4...
```

**Anyone can:**
1. Check out v1.0.0
2. See lock.json and index.json at that point in time
3. Rebuild .exe
4. Verify hash matches
5. Confirm: "This is the exact build released on [date]"

---

## REPRODUCIBILITY BENEFITS

| Benefit | How Lock/Index/Entry Enables It |
|---------|----------------------------------|
| **Security Audit** | Hash proves nothing was injected |
| **Compliance** | "Here's what was in the build" (auditable) |
| **Bug Investigation** | "This specific .exe version has this bug" |
| **Long-term Maintenance** | Can rebuild years later, exact copy |
| **Tamper Detection** | Hash changes if anything is modified |
| **Distribution Integrity** | Users can verify they got the real thing |
| **CI/CD Automation** | Same build pipeline always produces same .exe |

---

## POTENTIAL PITFALLS (What CAN break reproducibility)

```
❌ Do NOT do this:
  - Use "latest" versions instead of pinned versions
  - Change dependencies without updating lock.json
  - Use dynamic imports or auto-discovery
  - Include build timestamps in .exe
  - Use machine-specific paths
  - Different Python versions between builds

✓ Instead:
  - Pin every version in lock.json
  - Update lock.json + index.json together
  - Explicit imports only
  - Strip timestamps from .exe
  - Use $APPDATA (relative paths)
  - Mandate Python 3.8-3.10 for builds
```

---

## BUILD ENVIRONMENT SPECIFICATION

For reproducible builds, all these must be identical:

```
Windows Version:      Windows 10/11 (both work)
Python Version:       3.8.x, 3.9.x, or 3.10.x (pick ONE)
PyInstaller Version:  5.0 or higher
pip:                  Latest (auto-pins versions)
lock.json:            Committed to git
index.json:           Committed to git
Source Code:          Specific git commit/tag
```

**Record all of these** when you build:
```bash
# build_log.txt
Date: 2026-08-28
Windows: 10 (build 19045)
Python: 3.10.11
PyInstaller: 5.13.0
Git Commit: e33889e (sahstaacked-copilot-history-export-phase1)
SHA256: A1B2C3D4E5F6...7890ABCDEF01

Reproducible? YES (all inputs identical to 2026-08-28 build)
```

---

## FUTURE: DISTRIBUTED REPRODUCIBILITY

**Now (v1.0):** You rebuild locally.

**Future (v2.0+):** Anyone can verify:
```bash
# GitHub Actions or CI/CD
# On every push to main:
$ python build_exe.py
$ certutil -hashfile dist/ContentExportFramework.exe SHA256
$ git tag v1.0.1 -m "SHA256: ..."

# User downloads .exe from GitHub Release
# User verifies:
$ certutil -hashfile downloaded.exe SHA256
# Matches the tag? ✓ Verified authentic
```

---

## SUMMARY

**Lock + Index + Entry Points = Reproducible Builds**

Because:
1. **Lock** declares immutable universe (no surprises)
2. **Index** resolves deterministically (same inputs → same output)
3. **Entry Points** execute identically (same code path)

Result:
- ✓ Same .exe hash every time
- ✓ Auditable (what's inside is documented)
- ✓ Verifiable (anyone can rebuild and check)
- ✓ Long-term maintainable (can rebuild years later)
- ✓ Tamper-proof (hash detects changes)

**This is why the three-layer architecture matters.**
