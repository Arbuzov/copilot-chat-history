# Universal Content Export & Analysis Framework
## Directory Structure (Post-Installation)

```
ContentExportFramework/
├── README.md
├── LICENSE
├── setup.py
├── build_exe.py                    # Builds self-installing .exe
│
├── core/                           # Core framework (sector-agnostic)
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   ├── logger.py                   # Centralized logging
│   ├── exceptions.py               # Custom exceptions
│   └── utils.py                    # Shared utilities
│
├── processes/                      # 5-Process Pipeline (modular)
│   ├── __init__.py
│   ├── process_1_login_detector.py
│   ├── process_2_auth_handler.py
│   ├── process_3_downloader.py
│   ├── process_4_exporter.py
│   └── process_5_analyzer.py
│
├── search/                         # Word Search Engine
│   ├── __init__.py
│   ├── indexer.py                  # Build full-text indexes
│   ├── searcher.py                 # Execute searches
│   └── filters.py                  # Search filters & operators
│
├── sectors/                        # Cross-sector implementations
│   ├── __init__.py
│   ├── copilot/                    # Copilot (Microsoft)
│   │   ├── __init__.py
│   │   ├── config.json
│   │   ├── process_1.py            # Platform-specific login
│   │   ├── process_2.py            # Platform-specific auth
│   │   └── ...
│   ├── gemini/                     # Google Gemini
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── ...
│   ├── chatgpt/                    # OpenAI ChatGPT
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── ...
│   ├── claude/                     # Anthropic Claude
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── ...
│   └── custom_sector/              # Template for new sectors
│       ├── __init__.py
│       ├── config.json
│       └── ...
│
├── ui/                             # User Interface (CLI + future GUI)
│   ├── __init__.py
│   ├── cli.py                      # Command-line interface
│   └── gui/                        # Future web/desktop GUI
│       └── dashboard.py
│
├── tests/                          # Unit tests per module
│   ├── test_processes.py
│   ├── test_search.py
│   ├── test_sectors.py
│   └── fixtures/
│
├── data/                           # Working directories (NOT in .exe)
│   ├── .gitkeep
│   ├── raw-exports/
│   │   ├── copilot/
│   │   ├── gemini/
│   │   ├── chatgpt/
│   │   └── claude/
│   ├── formatted-exports/
│   │   ├── Copilot/
│   │   ├── Google Gemini/
│   │   ├── ChatGPT/
│   │   └── Claude/
│   ├── analysis/
│   │   ├── word-frequency/
│   │   └── search-indexes/
│   └── logs/
│       ├── process-1/
│       ├── process-2/
│       ├── process-3/
│       ├── process-4/
│       ├── process-5/
│       └── search/
│
├── config/                         # Configuration files
│   ├── default-config.json         # Default settings
│   ├── sectors.json                # Registered sectors
│   └── search-config.json          # Search engine config
│
└── requirements.txt                # Python dependencies
```

## Installation Structure

**After running installer:**
- `C:\Program Files\ContentExportFramework\` - Application code (.exe + Python runtime)
- `%APPDATA%\ContentExportFramework\` - User config + working data directory
- `C:\Users\[User]\Documents\ContentExportFramework\` - User exports (symlinked from appdata)

## Key Principles

1. **Modular**: Each process independent, can be called separately
2. **Sector-Agnostic**: Core framework applies to ANY platform (email, calendar, CMS, etc.)
3. **Hierarchical**: Data organized by sector → user → export date
4. **Persistent**: Working directories separate from executable
5. **Searchable**: Full-text indexing across all exported content
