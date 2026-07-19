# MDC Hub

[中文](README.md) | English

**Knowledge Base Management & Visualization Tool** — Transform project code into interactive knowledge graphs, powered by AI.

## Features

- **Offline-Ready Wheel** — Frontend, Skills, and presets all bundled, one `pip install` and you're set
- **AI Deep Scanning** — Point-by-point code analysis, generating 200-500 word detailed knowledge docs
- **Batch Merging Strategy** — Bottom-up + cross-directory merging for maximum AI efficiency; Pass 2 auto-split into small batches
- **Web Dashboard** — Interactive knowledge graph, Markdown rendering, category/tag filtering
- **Dark/Light Theme** — Full day/night mode support
- **Built-in Skills** — 5 professional Skills (code/table/document/media/directory scanning)

## Quick Start

### Install

```bash
# Option 1: Offline wheel from GitHub Release
pip install mdc_hub-0.3.0-py3-none-any.whl

# Option 2: From source
pip install "mdc-hub @ git+https://github.com/GodShelvis/mdc-hub.git"
```

### Setup

```bash
mdc-hub install       # Choose AI tools (Claude Code / OpenCode) for MCP config + Skills
mdc-hub provider setup  # Configure AI provider
```

### Scan & Generate Knowledge Graph

```bash
mdc-hub scan src --dry-run  # Preview scan plan
mdc-hub scan src            # Run AI deep scan
```

### Launch Web Dashboard

```bash
mdc-hub serve
```

Open `http://localhost:8000` — the frontend auto-loads scanned knowledge docs.

## CLI Reference

| Command | Description |
|---------|-------------|
| `mdc-hub install` | Choose AI tools, install MCP config + Skills |
| `mdc-hub serve` | Start backend API + frontend static files |
| `mdc-hub scan <dir>` | AI deep scan, generate knowledge graph docs |
| `mdc-hub mcp` | Start MCP Server (stdio mode) |
| `mdc-hub provider setup` | Interactive AI provider configuration |
| `mdc-hub graph list` | List knowledge nodes |
| `mdc-hub graph neighbors` | Traverse N-layer neighbors |
| `mdc-hub graph path` | Find shortest path between nodes |

### scan — AI Smart Scanning

```bash
mdc-hub scan                     # Scan current directory
mdc-hub scan ./src               # Scan specific directory
mdc-hub scan --dry-run           # Preview plan (no AI calls)
mdc-hub scan -e .py -e .java     # Filter by extension
```

Strategy: bottom-up → batch merge Pass 1 → Pass 2 small-batch MDC generation → Pass 3 directory summary. Default 10,000 lines/chunk, supports 29 file formats.

### serve — Launch Web UI

```bash
mdc-hub serve                  # Default port 8000
mdc-hub serve --port 3000      # Custom port
mdc-hub serve -p ./my-project  # Specify project directory
```

Auto-initializes `.mdc-hub/`, hosts both backend API and frontend.

### provider setup — Configure AI Provider

```bash
mdc-hub provider setup
```

Choose from presets (OpenAI/DeepSeek/Zhipu/Tongyi etc.) or custom → enter API key → auto-fetch model list.

### graph — Graph Queries

```bash
mdc-hub graph list ./docs              # List nodes
mdc-hub graph neighbors user-svc ./docs -d 2  # 2-layer neighbors
mdc-hub graph path a b ./docs          # Shortest path
```

## Development Status

### Completed

- [x] CLI tools: `install` / `serve` / `scan` / `provider` / `graph` / `mcp`
- [x] AI deep scan engine (Pass 1 → Pass 2 → Pass 3)
- [x] Batch merging + bottom-up analysis
- [x] Offline wheel packaging (frontend + Skills + presets bundled)
- [x] Web dashboard (node drag, Markdown rendering, filtering)
- [x] 5 built-in Skills
- [x] Claude Code / OpenCode MCP config + Skills installation
- [x] Cross-platform (Windows/macOS/Linux) pure-Python wheel
- [x] Dark/light theme

### In Progress

- [ ] MCP Server — framework ready (`mdc-hub mcp` launches), tool-skill integration WIP
- [ ] Web-based Markdown document editing
- [ ] AI-powered content adjustment (partial rewrite / full optimization)

### Planned

- [ ] Document parsers: Word (.docx) / Excel (.xlsx) / PowerPoint (.pptx)
- [ ] Create new documents within workspace via Web UI
- [ ] More AI tool MCP integrations (Codex, Cursor, etc.)
- [ ] Incremental scanning (changed files only)

## Architecture

```
mdc-hub/
├── skills/                  # 5 Built-in Skills
│   ├── mdc-directory-scanner/   # Orchestrator
│   ├── mdc-code-scanner/        # Code → method-level nodes
│   ├── mdc-excel-scanner/       # Spreadsheet analysis
│   ├── mdc-doc-scanner/         # Document analysis
│   └── mdc-media-scanner/       # Media analysis
├── backend/                 # Python Backend
│   ├── mcp_server.py            # MCP Server (stdio)
│   ├── archiver.py              # .mdc-hub/ archive management
│   ├── main.py                  # FastAPI HTTP API
│   ├── scanner.py               # MDC file parser
│   ├── ai_service.py            # AI interface + prompts
│   ├── scan_engine.py           # Scan engine
│   └── web_dist/                # Frontend static files (bundled in wheel)
├── cli/                     # CLI
│   └── main.py                  # install / serve / scan / provider / graph / mcp
├── frontend/                # Vue 3 Frontend
├── config/                  # Presets (providers/tags/categories)
└── .github/workflows/       # CI/CD (Release auto-builds wheel)
```

## License

MIT
