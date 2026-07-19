# MDC Hub

[中文](README.md) | English

**Knowledge Base Management & Visualization Tool** — Transform code, documents, and data into interactive knowledge graphs.

## Features

- **MCP Server** — 6 tools, directly callable by AI
- **5 Built-in Skills** — code/table/document/media/directory scanning, ready to use
- **Method-Level Knowledge Graph** — each Java/Python/TS method as an independent node, call relationships visualized
- **Web Dashboard** — drag nodes, Markdown rendering, category filtering
- **Dark/Light Theme** — full day/night mode support
- **Mermaid Diagrams** — automatic Mermaid chart rendering in documents

## Quick Start

### One-Line Install

```bash
pip install "mdc-hub[mcp] @ git+https://github.com/GodShelvis/mdc-hub.git"
mdc-hub install
```

`mdc-hub install` automatically detects installed AI tools, writes MCP configs, and installs 5 built-in Skills to their directories (supports Claude Desktop, Cursor, VS Code, Trae, and more — 9 platforms).

After installation, simply use in any AI tool:

> "Scan this project and generate a knowledge graph"

The AI will automatically invoke the `mdc-directory-scanner` Skill and complete scanning and archiving in 7 steps.

### Launch Web Dashboard

```bash
mdc-hub serve --port 8000
```

Open `http://localhost:8000` in your browser to view all MDC nodes in the interactive graph panel.

## CLI Reference

`mdc-hub` provides the following subcommands:

### install — Install Configuration

Auto-detects AI tools, writes MCP configs, installs Skills.

```bash
mdc-hub install              # Auto-detect and install
mdc-hub install --dry-run    # Preview only, no writes
```

Supported platforms: Trae, Claude Code, OpenCode, Cursor, Codex CLI, WorkBuddy, CodeBuddy, Windsurf, JetBrains.

### serve — Launch Web UI

One command to start backend API + frontend static files.

```bash
mdc-hub serve                  # Default port 8000
mdc-hub serve --port 3000      # Custom port
mdc-hub serve --dev            # Dev mode (auto-reload)
```

### graph list — List Nodes

List all MDC knowledge graph nodes in a directory.

```bash
mdc-hub graph list ./my-project
mdc-hub graph list ./my-project --json   # JSON output
```

Example output (`--json`):

```json
[
  {"id": "user-service", "title": "UserService", "category": "Tech/Backend/Service", "tags": ["java", "service"]},
  {"id": "user-service.findById", "title": "UserService.findById()", "category": "Tech/Backend/Service/UserService", "tags": ["java", "method"]}
]
```

### graph neighbors — Neighbor Traversal

Traverse N-layer neighbor nodes from a given node, with direction control.

```bash
mdc-hub graph neighbors user-service ./my-project
mdc-hub graph neighbors user-service ./my-project -d 2          # 2-level depth
mdc-hub graph neighbors user-service ./my-project -r down       # Downstream only
mdc-hub graph neighbors user-service ./my-project -r up         # Upstream only
mdc-hub graph neighbors user-service ./my-project -r both       # Both directions (default)
```

Parameters:

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--depth` | `-d` | Traversal depth | 2 |
| `--direction` | `-r` | Direction: `up` / `down` / `both` | `both` |

Example output:

```
  ★ React Hooks Deep Dive [react-hooks-deep-dive]
    Category: Tech/Frontend/React
    Direction: both, Depth: 2
    Connected nodes: 8

  ── Level 1 ──
    component-design — Component Design Principles (foundation, architecture)
    state-management — State Management Selection (depended by, depended by)
    ...

  ── Level 2 ──
    mdc-spec — MDC File Format Spec (tool scenario)
    pinia-best-practices — Pinia Best Practices (use together, comparison)
```

### graph path — Shortest Path

Find the shortest call path between two nodes.

```bash
mdc-hub graph path user-controller email-service ./my-project
mdc-hub graph path user-controller email-service ./my-project -d 5   # Max depth
```

Parameters:

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--max-depth` | `-d` | Max search depth | 5 |

Example output:

```
  Path (2 steps):

  Component Design Principles [component-design]
  ↓ React Hooks Deep Dive [react-hooks-deep-dive]
  ↓ Next.js App Router [nextjs-app-router]
```

## MCP Tools

These tools are exposed by the MCP Server and can be called by AI after loading a Skill:

| Tool | Description |
|------|-------------|
| `scan_directory` | Scan directory by file type, with type filtering |
| `read_files` | Batch read file contents |
| `write_mdc_document` | Write archived documents to `.mdc-hub/docs/` |
| `list_archived_documents` | List archived documents |
| `get_workspace_info` | Get workspace root and config |
| `open_dashboard` | Get Web UI access URL |

## Architecture

```
mdc-hub/
├── skills/                  # AI Skills (copied to .trae/skills/)
│   ├── mdc-directory-scanner/   # Orchestrator (7-step workflow)
│   ├── mdc-code-scanner/        # Code → method-level nodes
│   ├── mdc-excel-scanner/       # Tables → table/sheet-level nodes
│   ├── mdc-doc-scanner/         # Documents → chapter-level nodes
│   └── mdc-media-scanner/       # Media → resource-level nodes
├── backend/                 # Python Backend
│   ├── mcp_server.py            # MCP Server (stdio)
│   ├── archiver.py              # .mdc-hub/ archive management
│   ├── main.py                  # FastAPI HTTP API
│   ├── scanner.py               # MDC file parser
│   └── ai_service.py            # AI summary service
├── frontend/                # Vue 3 Frontend
│   └── src/
│       ├── components/          # Graph, file tree, category filter
│       ├── stores/              # Pinia state management
│       └── utils/               # Colors, Mermaid rendering
├── examples/                # Example MDC documents
├── install.sh               # One-click install
├── mcp-config.json          # MCP config template
└── scripts/
    └── mcp-entry.sh         # MCP Server entry point
```

## Document Format (MDC)

```yaml
---
id: "user-service"
title: "UserService"
category: "Tech/Backend/Service"
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
