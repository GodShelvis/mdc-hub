# MDC Hub

[中文](README.md) | English

**Knowledge Base Management & Visualization Tool** — Transform your project code, documents, and data into interactive knowledge graphs, powered by AI.

## Features

- **MCP Server** — 6 tools, directly callable by AI via stdio
- **5 Built-in Skills** — code/table/document/media/directory scanning, ready out of the box
- **AI-Powered Scanning** — scan entire codebases with any OpenAI-compatible provider, auto-generate structured documentation
- **Method-Level Knowledge Graph** — each Java/Python/TS method as an independent node, with visualized call relationships
- **Web Dashboard** — drag-and-drop nodes, Markdown rendering, category/tag filtering
- **Dark/Light Theme** — full day/night mode support
- **Mermaid Diagrams** — automatic chart rendering in documents

## Quick Start

```bash
pip install "mdc-hub[mcp] @ git+https://github.com/GodShelvis/mdc-hub.git"
mdc-hub install
```

`mdc-hub install` auto-detects installed AI tools (Trae, Claude Code, OpenCode, Cursor, Codex, Windsurf, etc. — 9 platforms), writes MCP configs, and installs all 5 Skills. During install, you can optionally configure an AI provider for smart scanning.

After installation, just say in any AI tool:

> "Scan this project and generate a knowledge graph"

## CLI Reference

### install — Setup

```bash
mdc-hub install              # Auto-detect and install
mdc-hub install --dry-run    # Preview only
```

### provider setup — Configure AI Provider

```bash
mdc-hub provider setup
```

Interactive flow: choose a preset provider (OpenAI / Anthropic / Zhipu GLM / Tongyi Qwen / DeepSeek / MiniMax) or custom → enter API key → auto-fetch model list → save to `.mdc-hub/config/settings.yaml`.

### scan — AI Smart Scanning

```bash
mdc-hub scan                  # Scan current directory
mdc-hub scan ./src            # Scan specific directory
mdc-hub scan --dry-run        # Preview plan (no AI calls)
mdc-hub scan -e .py -e .java  # Filter by extension
```

Bottom-up strategy: source files first → directory summaries. Large files auto-chunked (1000 lines). Two passes per file (structure → document generation). Directory-level docs summarize children without re-scanning.

### serve — Launch Web UI

```bash
mdc-hub serve                  # Default port 8000
mdc-hub serve --port 3000      # Custom port
mdc-hub serve --dev            # Dev mode
```

### graph list — List Nodes

```bash
mdc-hub graph list ./my-project
mdc-hub graph list ./my-project --json
```

### graph neighbors — Traverse Neighbors

```bash
mdc-hub graph neighbors <node-id> <dir>
mdc-hub graph neighbors <node-id> <dir> -d 2    # Depth 2
mdc-hub graph neighbors <node-id> <dir> -r up   # Upstream only
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--depth` | `-d` | Traversal depth | 1 |
| `--relation` | `-r` | `up` / `down` / `both` | `both` |

### graph path — Shortest Path

```bash
mdc-hub graph path <from> <to> <dir>
mdc-hub graph path <from> <to> <dir> -d 5   # Max depth
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `scan_directory` | Scan directory by file type |
| `read_files` | Batch read file contents |
| `write_mdc_document` | Write to `.mdc-hub/docs/` |
| `list_archived_documents` | List archived documents |
| `get_workspace_info` | Get workspace root and config |
| `open_dashboard` | Get Web UI URL |

## Architecture

```
mdc-hub/
├── skills/                  # AI Skills (5 built-in)
│   ├── mdc-directory-scanner/   # Orchestrator (7-step workflow)
│   ├── mdc-code-scanner/        # Code → method-level nodes
│   ├── mdc-excel-scanner/       # Tables → sheet-level nodes
│   ├── mdc-doc-scanner/         # Documents → chapter-level nodes
│   └── mdc-media-scanner/       # Media → resource-level nodes
├── backend/                 # Python Backend
│   ├── mcp_server.py            # MCP Server (stdio)
│   ├── archiver.py              # .mdc-hub/ archive management
│   ├── main.py                  # FastAPI HTTP API
│   ├── scanner.py               # MDC file parser
│   ├── ai_service.py            # Universal AI (OpenAI-compatible)
│   └── scan_engine.py           # Bottom-up scan engine
├── cli/                     # CLI
│   └── main.py                  # install / serve / provider / scan / graph
├── frontend/                # Vue 3 Frontend
├── examples/                # Example MDC docs
└── scripts/
    └── mcp-entry.sh         # MCP Server entry point
```

## Document Format (MDC)

```yaml
---
id: "user-service"
title: "UserService — User Service"
category: "backend-core"
tags: [java, service, user]
connections:
  - target: "user-dao"
    relation: "depends-on"
---

# Markdown Body
...
```

See `examples/tooling/mdc-spec.md` for details.

## License

MIT
