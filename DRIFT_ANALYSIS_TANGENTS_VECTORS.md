# Drift Analysis, Tangents, Vectors & Alignment
## Framework for Detecting Unintended Divergence from Lock State

---

## DRIFT: THE CORE PROBLEM

**Drift** = Actual state diverges from declared state (lock.json)

### Example:
```
Day 1 (locked):
  lock.json declares: python-docx>=0.8.11
  pip installs: python-docx 0.8.11 ✓

Day 180 (drift):
  lock.json still says: python-docx>=0.8.11
  But someone ran: pip install python-docx (latest)
  pip installs: python-docx 0.8.15 ✗
  
  Question: Was this intentional upgrade, or accidental drift?
  Answer: Unclear. This is the problem.
```

---

## WHY DRIFT BREAKS REPRODUCIBILITY

```
Scenario A (No Drift):
  Build Date 1: python-docx 0.8.11 → .exe (SHA256: ABC...)
  Build Date 180: python-docx 0.8.11 → .exe (SHA256: ABC...)
  ✓ Same hash. Reproducible.

Scenario B (Accidental Drift):
  Build Date 1: python-docx 0.8.11 → .exe (SHA256: ABC...)
  Build Date 180: python-docx 0.8.15 (drifted) → .exe (SHA256: XYZ...)
  ✗ Different hash. Not reproducible. Bug introduced?
  ❓ Question: Who upgraded docx? When? Why?
```

---

## THREE TYPES OF DRIFT

### 1. CONFIGURATION DRIFT
Definition: Actual configuration differs from declared configuration.

```
lock.json declares:
  "requires_python": ">=3.8,<4.0"

Actual environment:
  User is running Python 3.11
  
Drift detected: YES
Question: Is this intentional? (Maybe user upgraded OS)
```

### 2. DEPENDENCY DRIFT
Definition: Installed packages differ from locked versions.

```
lock.json declares:
  "requests>=2.28.0"

Actual installed:
  requests 2.31.0 (newer than lock)
  
Drift type: UPGRADE DRIFT
Question: Intentional? Or accidental `pip install -U`?
```

### 3. ALIGNMENT DRIFT
Definition: Behavior diverges from intent.

```
intent: "One .exe, self-contained, no distributed components"

current state: Someone added plugin_loader.py to the .exe

Drift detected: YES (architecture violated)
Question: Was plugin system intentionally added?
```

---

## VECTORS: DIRECTION & MAGNITUDE OF DRIFT

A **vector** describes:
- **Direction**: Which way is it changing? (upgrade? downgrade? new feature?)
- **Magnitude**: How big is the change? (patch bump? major rewrite?)
- **Intentionality**: Is this change planned/approved?

### Drift Vector Examples:

```
Vector 1 (Intentional, Approved):
  Declared: "Lock Phase 2 features"
  Direction: Add OneDrive sync → entry_points.json updated
  Magnitude: Feature addition (minor)
  Intentionality: YES (planned in Phase 2)
  Status: ✓ Expected drift (planned evolution)

Vector 2 (Unintentional, Unapproved):
  Declared: "pin requests>=2.28.0"
  Actual: pip upgraded to requests 2.31.0 (user ran pip -U)
  Direction: Dependency upgrade
  Magnitude: Patch version (+3 versions)
  Intentionality: NO (accidental)
  Status: ✗ Unexpected drift (bug introduction risk)

Vector 3 (Tangent - Off Course):
  Declared: "legacy self-contained .exe"
  Actual: Someone added multi-user authentication
  Direction: Architecture change
  Magnitude: MAJOR (fundamental change)
  Intentionality: UNCLEAR (no approval record)
  Status: ⚠️ TANGENT (diverges from Phase 1 scope)
```

---

## TANGENTS: UNPLANNED DIVERGENCE

**Tangent** = Change that moves off the intended course.

### Tangent Warning Signs:

```
Red Flags:
  ❌ lock.json changed without commit message
  ❌ New dependencies added not in lock.json
  ❌ Entry point modified without approval
  ❌ Code added to .exe that's not in lock
  ❌ Configuration changed at runtime (no audit trail)
  ❌ Build produces different SHA256 but no change log
```

### Tangent Examples:

```
Tangent 1 (Feature Creep):
  Phase 1 Scope: "5-process pipeline for Copilot"
  Phase 2 (v1.1) Scope: "Installer + Word Search"
  
  Actual v1.1: Someone added multi-platform support (Gemini pipelines)
  
  This is a TANGENT:
  - Not in scope for v1.1
  - Not in lock.json
  - Not approved
  - Violates "Deferred to Phase 3" boundary
  
  Risk: Delays release, increases testing burden

Tangent 2 (Dependency Inflation):
  lock.json declares: 3 dependencies (docx, openpyxl, requests)
  
  6 months later:
  lock.json has: 12 dependencies (someone added ML libraries, GUI frameworks)
  
  This is a TANGENT:
  - Not in Phase 1 scope
  - Increases .exe size
  - Increases security surface (more packages to audit)
  - Not approved
  
  Risk: .exe becomes bloated, reproducibility harder
```

---

## ALIGNMENT DRIFT: THE INTENT vs REALITY GAP

**Alignment** = Does the system match its declared intent?

### Alignment Checks (Continuous Monitoring):

```
Intent Statement (from lock.json):
  "Self-contained legacy .exe, no plugins, single entry point"

Alignment Checks:
  □ .exe size < 50 MB? (Check: Is it bloated?)
  □ No plugin_registry module? (Check: No extensibility added?)
  □ Single entry point in entry_points.json? (Check: No new CLI modes?)
  □ All dependencies in lock.json? (Check: No secret dependencies?)
  □ Reproducible hash on rebuild? (Check: Bit-for-bit identical?)
  □ No external network calls at startup? (Check: Self-contained?)
  □ No configuration server dependency? (Check: Pure local execution?)
```

### Alignment Score:

```
Version v1.0.0:
  Size: 38 MB (target: <50 MB) ✓
  Plugins: 0 (target: 0) ✓
  Entry points: 1 (target: 1) ✓
  Dependencies: 3 (in lock.json) ✓
  SHA256 reproducible: YES ✓
  
  Alignment Score: 100% ✓ (In alignment)

Version v1.0.2 (6 months later):
  Size: 62 MB (target: <50 MB) ✗
  Plugins: 0 (target: 0) ✓
  Entry points: 3 (target: 1) ✗ (someone added CLI modes)
  Dependencies: 8 (not all in lock.json) ✗
  SHA256 reproducible: NO ✗
  
  Alignment Score: 20% ✗ (DRIFT DETECTED)
  Action Required: Investigate what changed between v1.0.0 and v1.0.2
```

---

## DRIFT DETECTION FRAMEWORK (For v2.0+)

**This is out of scope for v1.0, but important to plan.**

### Automated Drift Detection:

```python
# drift_detector.py (future module)
class DriftAnalyzer:
    def detect_configuration_drift(self):
        """Compare lock.json vs actual environment"""
        pass
    
    def detect_dependency_drift(self):
        """Compare index.json vs pip freeze output"""
        pass
    
    def detect_alignment_drift(self):
        """Check if .exe matches declared intent"""
        pass
    
    def compute_drift_vector(self):
        """Calculate magnitude + direction of change"""
        pass
    
    def flag_tangents(self):
        """Alert if changes move off intended course"""
        pass
    
    def generate_drift_report(self):
        """Document all drift since last lock"""
        pass
```

### Drift Report Example:

```
Drift Report for v1.0.2
Generated: 2026-09-15

Configuration Drift:
  Python version: Expected 3.8-3.10, Found 3.11
  Status: DRIFT (user upgraded OS)
  Action: Test with Python 3.11, update lock if compatible

Dependency Drift:
  requests: Expected 2.28.0, Found 2.31.0 (+3 patch versions)
  Status: DRIFT (unexpected)
  Cause: Unknown (no commit message)
  Action: Lock to 2.28.0 or document upgrade reason

Alignment Drift:
  .exe size: Expected <50 MB, Found 62 MB
  Status: DRIFT (12 MB increase)
  Cause: 5 new dependencies added (not in lock.json)
  Action: Remove unnecessary dependencies or update intent

Tangent Detection:
  Status: TANGENT DETECTED
  Change: Multi-platform support (Gemini) added
  Scope: Should be Phase 3, not Phase 1
  Action: Move to separate branch, wait for v2.0 release

Overall Drift Score: 40% (ALERT)
Recommendation: Code review + lock file audit required
```

---

## PREVENTING DRIFT (Best Practices)

### For Developers:

```
✓ DO:
  - Update lock.json whenever you add a dependency
  - Commit lock.json changes with detailed commit message
  - Run `python build_exe.py && record SHA256` before release
  - Document WHY a change was made (not just WHAT changed)
  - Get code review before modifying lock.json
  - Test that rebuild produces same SHA256

✗ DON'T:
  - Upgrade dependencies without updating lock.json
  - Run `pip install -U` without recording it
  - Commit code without committing lock.json
  - Modify entry_points.json without justification
  - Add "temporary" dependencies
  - Use version ranges like ">=2.0" (too loose)
```

### For Project Leads:

```
✓ DO:
  - Review every lock.json change in pull requests
  - Maintain alignment checklist (size, entry points, dependencies)
  - Tag releases with SHA256 hash
  - Document scope boundaries (what's Phase 1 vs Phase 2+)
  - Monitor drift report monthly
  - Require approval before out-of-scope changes

✗ DON'T:
  - Allow feature creep into wrong phase
  - Ignore alignment drift warnings
  - Accept "temporary" API dependencies
  - Permit undocumented dependency upgrades
  - Release without reproducibility verification
```

---

## VECTORS IN PRACTICE

### Intentional Vector (Good):

```
Phase 1 → Phase 2 (Planned evolution)

lock.json v1.0:
  dependencies: [docx, openpyxl, requests]

lock.json v1.1:
  dependencies: [docx, openpyxl, requests, onedrive-sdk]

Approval: Phase 2 spec approved by stakeholders
Vector Direction: FORWARD (as planned)
Vector Magnitude: Feature addition (intentional)
Alignment: ✓ Still self-contained, still one .exe
```

### Unintentional Vector (Bad):

```
v1.0 (released) → v1.0.1 (critical bug fix)

lock.json v1.0.1:
  dependencies: [docx, openpyxl, requests, tensorflow, flask, react]

Approval: NO approval
Vector Direction: SIDEWAYS (tangent off course)
Vector Magnitude: MAJOR (6x dependencies)
Alignment: ✗ No longer self-contained, .exe bloated
Action: ROLLBACK + CODE REVIEW
```

---

## SUMMARY: DRIFT, TANGENTS, VECTORS, ALIGNMENT

| Concept | Definition | Detection Method | Action |
|---------|-----------|------------------|--------|
| **Drift** | Actual ≠ Declared | Compare lock.json vs reality | Investigate cause |
| **Tangent** | Off intended course | Check scope boundaries | Get approval or rollback |
| **Vector** | Direction + magnitude of change | Analyze commit history | Determine if intentional |
| **Alignment** | Behavior matches intent | Alignment checklist | Verify before release |

---

## OUT OF SCOPE (v1.0) - TO DO IN v2.0+

This entire drift detection framework is **deferred to v2.0+**:
- Automated drift detection module
- Monthly drift reports
- Real-time alignment monitoring
- Vector analysis dashboard
- Tangent warning system
- CI/CD drift checks

**Why deferred:**
- Adds complexity to v1.0
- Not needed for single-user legacy .exe
- Becomes critical when multi-platform (v2.0+)
- Requires admin/audit infrastructure (Phase 5)

**When needed:**
- Phase 3+: Multiple platforms (need to prevent scope creep)
- Multi-user (Phase 5): Need audit trail
- Distributed (Phase 7): Need global state tracking

---

## KEY INSIGHT

**Lock + Index + Entry Points prevents drift FROM DAY ONE.**

By having immutable, documented, committed declarations:
1. lock.json makes drift VISIBLE (if someone changes it, git shows diff)
2. index.json makes resolution AUDITABLE (what went in, when)
3. entry_points.json makes execution PREDICTABLE (same code path)

**Result:** Drift detection is built-in to the architecture, even in v1.0.

You just need to:
1. Commit lock.json, index.json, entry_points.json to git
2. Check git diff before building
3. Record SHA256 when you release
4. In v2.0+, automate drift detection

**Reproducibility + Drift Detection = Long-term System Integrity**
