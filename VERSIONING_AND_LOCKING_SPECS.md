# Content Export Framework - Versioning & Locking Specifications

## VERSION CONTROL STRATEGY

### Semantic Versioning (MAJOR.MINOR.PATCH)

```
Format: v{MAJOR}.{MINOR}.{PATCH}-{BUILD}
Example: v1.0.0-alpha, v1.2.3, v2.0.0-rc1
```

### Version Components

| Component | Increment | Purpose |
|-----------|-----------|---------|
| **MAJOR** | Breaking changes | New sector, incompatible API changes, database schema changes |
| **MINOR** | Features added | New process, new search filters, OneDrive improvements |
| **PATCH** | Bug fixes | Fixes without breaking changes |
| **BUILD** | Internal iterations | alpha, beta, rc1, rc2, stable |

---

## PHASE VERSIONING

### Phase 1: Core Pipeline (v1.0.0)
- **Status**: Current
- **Components**: Login → Auth → Download → Export → Analyze
- **Platform**: Copilot only
- **Scope**: Verbatim content export, word frequency analysis
- **Lock Status**: ✓ LOCKED - No changes to 5-process architecture

### Phase 2: Installer + Search (v1.1.0)
- **Status**: In Progress
- **Components**: Self-installing .exe, Word Search Engine, OneDrive Sync
- **Platforms**: Copilot (multi-user prep)
- **Features**: Desktop activation, local + cloud backup
- **Lock Status**: IN PROGRESS

### Phase 3: Multi-Platform (v2.0.0) - **OUT OF SCOPE**
- **Components**: Gemini, ChatGPT, Claude pipelines
- **Reason**: Requires platform-specific authentication mechanisms
- **Estimated**: Post-Phase-2 release
- **Lock Status**: ⊘ NOT YET STARTED

### Phase 4: Advanced Analytics (v2.1.0) - **OUT OF SCOPE**
- **Components**: Machine learning analysis, semantic search, trend detection
- **Reason**: Separate ML pipeline required
- **Lock Status**: ⊘ BLOCKED - Requires Phase 2 completion

### Phase 5: Enterprise Features (v3.0.0) - **OUT OF SCOPE**
- **Components**: Multi-user management, audit logging, data governance
- **Lock Status**: ⊘ FUTURE - Beyond current scope

---

## LOCKING PREFERENCES

### File Locking Strategy

| File | Lock Type | Reason | Status |
|------|-----------|--------|--------|
| `copilot_login_detector.py` | HARD LOCK | Process 1 core logic | ✓ Locked |
| `copilot_auth_handler.py` | HARD LOCK | OAuth handling | ✓ Locked |
| `copilot_history_downloader.py` | HARD LOCK | Download mechanism | ✓ Locked |
| `copilot_content_exporter.py` | HARD LOCK | .docx/.xlsx output | ✓ Locked |
| `copilot_word_frequency_analyzer.py` | HARD LOCK | Word analysis | ✓ Locked |
| `word_search_engine.py` | SOFT LOCK | Search filters can expand | 🔒 Editable |
| `onedrive_sync_manager.py` | SOFT LOCK | Sync logic extensible | 🔒 Editable |
| `build_exe.py` | SOFT LOCK | Installer customizable | 🔒 Editable |
| `main.py` | SOFT LOCK | CLI/UI can evolve | 🔒 Editable |
| `DIRECTORY_STRUCTURE.md` | INFO ONLY | Documentation | 📖 Reference |

### Lock Types

**HARD LOCK**: Core functionality - DO NOT MODIFY
- Changes require version bump + testing
- Affects downstream processes

**SOFT LOCK**: Extensible functionality - can enhance without breaking
- Add features without modifying core logic
- Backward compatible

**INFO ONLY**: Documentation - for reference
- Can be updated without version bump

---

## OUT OF SCOPE FOR THIS BUILD (v1.0-v1.1)

### ⊘ NOT INCLUDED - Defer to Phase 3+

1. **Multi-Platform Pipelines**
   - Google Gemini authentication
   - OpenAI ChatGPT authentication
   - Anthropic Claude authentication
   - Reason: Platform-specific OAuth flows differ significantly

2. **Advanced Search Features**
   - Boolean search with parentheses: `(python OR java) AND machine`
   - Fuzzy matching / typo correction
   - Semantic search (requires ML)
   - Reason: SQLite full-text search sufficient for Phase 1

3. **Enterprise Features**
   - Multi-user RBAC (role-based access control)
   - Centralized audit logging
   - Data encryption at rest
   - Reason: Single-user focus for initial release

4. **Analytics & Reporting**
   - Timeline visualization
   - Conversation clustering
   - Trend analysis
   - Reason: Separate analytics module (Phase 4+)

5. **Mobile Support**
   - Mobile app
   - Sync to mobile devices
   - Reason: Desktop-first (Windows only)

6. **GUI / Web Dashboard**
   - Graphical user interface
   - Web-based management console
   - Real-time sync monitoring
   - Reason: CLI sufficient; GUI deferred to Phase 2.1+

---

## CHANGE TRACKING REQUIREMENTS

### Commit Message Format

```
[PHASE] [TYPE] Brief description

TYPE: feature|fix|docs|refactor|test|chore

Example:
[P1] feature: Add OneDrive sync capability
[P2] fix: Handle OAuth timeout gracefully
[P2] docs: Update versioning specs
```

### Version Bump Checklist

Before incrementing version:

- [ ] All tests passing
- [ ] Changelog updated
- [ ] Documentation complete
- [ ] Breaking changes documented (if MAJOR bump)
- [ ] Migration guide provided (if needed)
- [ ] Tag created: `git tag v{VERSION}`

### Database Schema Versioning

**Current**: v1.0 (Phase 1)
- `documents` table (search indexing)
- `word_index` table (word frequency)
- `phrase_index` table (phrase search)
- `search_history` table (logging)

**Next**: v1.1 (Phase 2)
- Multi-platform support fields
- User association metadata

---

## SCOPE BOUNDARIES

### ✓ WITHIN SCOPE (v1.0-v1.1)

**Core Capabilities**:
- Single-user Copilot export
- Verbatim content preservation
- Local file storage
- OneDrive backup/restore
- Word frequency analysis
- Full-text search (basic)
- Desktop shortcut activation

**File Formats**:
- .docx (Word) - verbatim content with formatting
- .xlsx (Excel) - structured metadata
- .json (raw history backup)
- .db (SQLite search index)

**Platforms**:
- Windows 10/11 (desktop)
- OneDrive (cloud backup)

---

### ⊘ OUT OF SCOPE (Future Phases)

**Will NOT implement in v1.0-v1.1**:
- ❌ Multi-sector pipelines (Gemini, ChatGPT, Claude)
- ❌ Machine learning analysis
- ❌ Web dashboard / GUI
- ❌ Mobile sync
- ❌ Multi-user management
- ❌ Data encryption (at rest)
- ❌ Federated search across sectors
- ❌ Real-time streaming
- ❌ API / Plugin system

**Rationale**: Single-user, desktop-first MVP for Copilot data export.

---

## DEPENDENCIES & COMPATIBILITY

### Python Version
- **Minimum**: 3.8
- **Recommended**: 3.10+
- **Lock**: Cannot change without MAJOR version bump

### External Libraries (Locked)
```
python-docx>=0.8.11       # .docx generation (hard lock)
openpyxl>=3.8.0           # .xlsx generation (hard lock)
requests>=2.28.0          # HTTP requests for OAuth (hard lock)
PyInstaller>=5.0          # .exe packaging (soft lock)
```

### Windows-Specific (Locked)
- Windows 10+
- .NET Framework (for OneDrive integration)
- Administrator privileges (for installation)

---

## TESTING REQUIREMENTS FOR VERSION RELEASE

Before releasing v1.x or v2.x:

```python
# Minimum test coverage
pytest --cov=processes --cov=search --cov=onedrive

# Must pass:
- test_5_process_pipeline()      # Complete flow
- test_word_frequency_accuracy()  # Analysis quality
- test_search_performance()       # Index speed
- test_onedrive_sync()            # Cloud backup
- test_data_preservation()        # Verbatim integrity
```

---

## BRANCH STRATEGY

```
main (stable releases only)
  ↓
release/v1.1.0 (pre-release testing)
  ↓
develop (integration branch)
  ↓
feature/p2-* (feature branches)
  ↓
bugfix/p2-* (bug fix branches)
```

---

## RELEASE NOTES TEMPLATE

```markdown
# Content Export Framework v1.1.0

## What's New
- Self-installing .exe with proper directory structure
- Word search engine with full-text indexing
- OneDrive sync for aprilapeterson@gmail.com
- Desktop shortcuts for activation

## Breaking Changes
None

## Known Limitations
- Single-platform (Copilot only)
- Single user per installation
- OneDrive sync manual (not automatic)

## Installation
Run `ContentExportFramework-Installer.exe`

## Upgrade Path
From v1.0 → v1.1: Data automatically preserved in AppData
```

---

## SIGNOFF

**Framework Lock Date**: 2026-08-28
**Phase 1 Status**: COMPLETE ✓
**Phase 2 Status**: IN PROGRESS 🔨
**Beyond Phase 2**: OUT OF SCOPE ⊘

**Locked Components** (v1.0):
- 5-Process Pipeline (Processes 1-5)
- Copilot-specific implementation

**Next Review**: After Phase 2 completion (v1.1.0 release)
