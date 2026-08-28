# Content Export Framework - Phase 3+ Planning
## OUT OF SCOPE for v1.0-v1.1 (Current Build)
## Specifications for Future Releases

---

## PHASE 3: MULTI-PLATFORM PIPELINES (v2.0.0+)

### Overview
Add Gemini, ChatGPT, and Claude export pipelines using same 5-process architecture.

### Sector Implementations

#### Google Gemini Pipeline (5 processes)
```
3.1: Gemini Login Detection
     - Detect user authentication via Google account
     - OAuth2 flow (different from GitHub OAuth)
     
3.2: Gemini Authorization Handler
     - Google OAuth2 token exchange
     - Scopes: gemini.history, user profile
     
3.3: Gemini History Download
     - Fetch from Gemini API (vs. Copilot Privacy tab)
     - Handle streaming conversations
     
3.4: Gemini Content Export
     - Export to .docx/.xlsx (same format as Copilot)
     - Store in ./data/formatted-exports/Google Gemini/
     
3.5: Gemini Word Frequency Analysis
     - Same word frequency engine
     - Index into shared search database
```

#### OpenAI ChatGPT Pipeline (5 processes)
```
3.6: ChatGPT Login Detection
     - Detect OpenAI platform login
     - OAuth2 flow (OpenAI provider)
     
3.7: ChatGPT Authorization Handler
     - OpenAI API key or OAuth
     - Scopes: conversations.list, conversation.read
     
3.8: ChatGPT History Download
     - Fetch from OpenAI API or web export
     - Handle conversation threads
     
3.9: ChatGPT Content Export
     - Export to .docx/.xlsx
     - Store in ./data/formatted-exports/ChatGPT/
     
3.10: ChatGPT Word Frequency Analysis
      - Shared search engine indexing
```

#### Anthropic Claude Pipeline (5 processes)
```
3.11: Claude Login Detection
      - Detect Claude.ai login
      - Token-based or OAuth
      
3.12: Claude Authorization Handler
      - Claude API authentication
      - Session management
      
3.13: Claude History Download
      - Fetch conversation history
      - Handle Claude-specific formats
      
3.14: Claude Content Export
      - Export to .docx/.xlsx
      - Store in ./data/formatted-exports/Claude/
      
3.15: Claude Word Frequency Analysis
      - Shared indexing
```

### Platform-Agnostic Modifications

```python
# Sector Registry (new in v2.0)
sectors/
├── registry.json          # Map sectors to implementations
├── base_sector.py         # Abstract base class
├── sector_validator.py    # Validate sector compliance
└── sector_template/       # Template for new sectors
    ├── process_1.py
    ├── process_2.py
    ├── ...
    ├── process_5.py
    ├── config.json
    └── README.md

# CLI Enhancement (v2.0)
main.py --sector copilot     # Run Copilot pipeline
main.py --sector gemini      # Run Gemini pipeline
main.py --sector all         # Run all registered sectors
main.py --list-sectors       # Show available sectors
```

### Database Schema Changes (v2.0)

**New columns in `documents` table**:
```sql
ALTER TABLE documents ADD COLUMN sector_version TEXT;  -- v1.0, v2.0, etc.
ALTER TABLE documents ADD COLUMN platform_api_version TEXT;  -- API versions
ALTER TABLE documents ADD COLUMN extraction_method TEXT;  -- 'api', 'web_export', 'oauth'
```

### Version Pinning

Each sector pins its supported versions:
```json
{
  "sector": "gemini",
  "framework_version": ">=2.0.0,<3.0.0",
  "api_versions": {
    "gemini_api": "v1.2+",
    "google_oauth": "2.0"
  }
}
```

---

## PHASE 4: ADVANCED ANALYTICS (v2.1.0+)

### Components (Out of Current Scope)

#### 4.1: Semantic Search
```python
# Requires: transformers, sentence-transformers, faiss
semantic_search/
├── embeddings.py      # Generate embeddings (BERT-based)
├── similarity.py      # Cosine similarity search
└── index.py           # FAISS index management

# Query: "Show me conversations about machine learning"
# Finds semantically related content, not just keyword matches
```

#### 4.2: Conversation Clustering
```python
# Requires: sklearn, networkx
clustering/
├── topic_extractor.py    # LDA / NMF topic modeling
├── clustering.py         # K-means conversation grouping
└── visualization.py      # Generate cluster visualizations

# Output: Topic maps, conversation groups, trend analysis
```

#### 4.3: Timeline Visualization
```python
# Requires: matplotlib, plotly, dash
analytics/
├── timeline.py       # Conversation frequency over time
├── heatmaps.py       # Activity heatmaps (day/hour)
├── wordclouds.py     # Visual word frequency
└── dashboard.py      # Interactive Plotly dashboard
```

#### 4.4: Trend Detection
```python
# Requires: statsmodels, scipy
trends/
├── time_series.py    # ARIMA forecasting
├── anomaly_detect.py # Detect unusual activity
└── growth_rates.py   # Conversation volume trends
```

### Machine Learning Dependencies (v2.1+)
```
torch>=2.0.0          # ML foundation
transformers>=4.30.0  # BERT, embeddings
sentence-transformers>=2.2.0  # Semantic embeddings
faiss-cpu>=1.7.0      # Vector similarity
scikit-learn>=1.3.0   # Clustering, topic modeling
networkx>=3.1         # Graph analysis
plotly>=5.17.0        # Interactive visualizations
```

### ML Model Storage
```
data/
├── ml-models/
│   ├── embeddings/
│   │   └── sentence-transformer-v2.1/  # ~500MB
│   ├── topic-models/
│   │   └── lda_copilot_v1/
│   └── metadata.json
```

**Storage Warning**: Models can be 500MB+ - separate from core export data.

---

## PHASE 5: ENTERPRISE FEATURES (v3.0.0+)

### 5.1: Multi-User Management

```python
# auth/multi_user.py
enterprise/
├── auth/
│   ├── rbac.py           # Role-based access control
│   ├── user_manager.py   # User administration
│   └── permissions.py    # Permission matrix
├── audit/
│   ├── audit_log.py      # Centralized audit trail
│   └── compliance.py     # GDPR, HIPAA compliance
└── governance/
    ├── retention.py      # Data retention policies
    ├── encryption.py     # At-rest encryption
    └── backup_policy.py  # Backup scheduling
```

### 5.2: Role Definitions

| Role | Export | Search | Manage Users | Delete Data | View Logs |
|------|--------|--------|--------------|-------------|-----------|
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| User | ✓ | ✓ | ✗ | ✗ | ✗ |
| Auditor | ✗ | ✓ | ✗ | ✗ | ✓ |
| Analyst | ✗ | ✓ | ✗ | ✗ | ✗ |

### 5.3: Audit Requirements

```sql
-- audit_events table (new in v3.0)
CREATE TABLE audit_events (
  id INTEGER PRIMARY KEY,
  timestamp TIMESTAMP,
  user_id TEXT,
  action TEXT,
  resource TEXT,
  old_value TEXT,
  new_value TEXT,
  ip_address TEXT,
  status TEXT  -- 'success', 'failure'
);
```

### 5.4: Data Encryption (v3.0+)

```python
# encryption/aes_encryption.py
from cryptography.fernet import Fernet

# Encrypt sensitive fields in database
# Master key stored in HSM or environment
```

### 5.5: Backup Scheduling

```python
# backup/scheduler.py
Backup Strategies:
  - Daily incremental backup
  - Weekly full backup
  - Monthly archive to cold storage
  - Geo-redundancy option
```

---

## PHASE 6: GUI & WEB DASHBOARD (v3.1.0+)

### 6.1: Web Dashboard

```python
# ui/web_dashboard/
dashboard/
├── app.py              # Flask/FastAPI server
├── routes/
│   ├── auth.py
│   ├── export.py
│   ├── search.py
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── search.html
│   └── admin.html
└── static/
    ├── css/
    └── js/
```

### 6.2: Desktop GUI (Windows)

```python
# ui/desktop_gui/
gui/
├── app.py              # PyQt5 application
├── windows/
│   ├── main_window.py
│   ├── export_wizard.py
│   ├── search_window.py
│   └── settings_dialog.py
└── assets/
    ├── icons/
    └── themes/
```

### 6.3: Dashboard Features

- Real-time sync status
- Search interface with filters
- Export scheduling
- Analytics visualizations
- User management (admin)
- Audit logs (admin)

---

## PHASE 7: MOBILE & CROSS-PLATFORM (v4.0.0+)

### Out of Scope
- iOS/Android apps
- Cloud server infrastructure
- API rate limiting
- CDN caching
- Multi-region deployment

**Reason**: Desktop-first MVP. Mobile considered post v3.x.

---

## DEPENDENCY EVOLUTION ROADMAP

```
v1.0-v1.1 (Current)
├── python-docx, openpyxl, requests
├── PyInstaller (build only)
└── SQLite (bundled)

v2.0-v2.1 (Phase 3-4)
├── Add: transformers, faiss, plotly
├── Add: sector-specific packages (google-auth, openai, anthropic)
└── DB: PostgreSQL optional upgrade

v3.0-v3.1 (Phase 5-6)
├── Add: cryptography, Flask/FastAPI
├── Add: PyQt5 (desktop GUI)
├── Security: HSM integration
└── DB: Mandatory PostgreSQL for multi-user

v4.0+ (Phase 7)
├── Add: Django/FastAPI scaling
├── Add: Redis caching, Celery tasks
├── Add: Kubernetes orchestration
└── DB: Multi-region sharding
```

---

## TIMELINE & RESOURCE ESTIMATES

| Phase | Release | Effort | Team Size | Status |
|-------|---------|--------|-----------|--------|
| 1 | v1.0 | 2 weeks | 1 | ✓ COMPLETE |
| 2 | v1.1 | 1 week | 1 | 🔨 IN PROGRESS |
| 3 | v2.0 | 4 weeks | 2 | ⊘ PENDING |
| 4 | v2.1 | 6 weeks | 2-3 | ⊘ PENDING |
| 5 | v3.0 | 8 weeks | 3-4 | ⊘ PENDING |
| 6 | v3.1 | 10 weeks | 4-5 | ⊘ PENDING |
| 7 | v4.0 | 12+ weeks | 5+ | ⊘ FUTURE |

---

## CROSS-PHASE DEPENDENCIES

```
Phase 1 ✓
  ↓ (foundation)
Phase 2 🔨 (installer, search)
  ↓ (both stable)
Phase 3 ⊘ (multi-platform)
  ├→ Phase 4 ⊘ (analytics requires multi-sector data)
  ├→ Phase 5 ⊘ (enterprise requires stable multi-platform)
  └→ Phase 6 ⊘ (GUI requires enterprise features)
      └→ Phase 7 ⊘ (mobile requires cloud infra)
```

**Cannot skip phases**: Each phase depends on previous stability.

---

## DOCUMENT CONTROL

**Last Updated**: 2026-08-28
**Version**: 1.0 (Planning)
**Status**: OUT OF SCOPE for v1.0-v1.1 Build

**When to Review**:
- After Phase 2 (v1.1) release: Confirm Phase 3 priorities
- Before Phase 3 starts: Finalize multi-platform architecture
- Annually: Reassess roadmap based on user feedback

**Next Review Date**: After v1.1.0 release
