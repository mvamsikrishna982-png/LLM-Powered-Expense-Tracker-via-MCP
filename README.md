# LLM-Powered Expense Tracker via MCP Server

A production-deployed **Model Context Protocol (MCP) server** that enables AI assistants like Claude to manage and track expenses through natural language — accessible across Claude Desktop, Claude Web, and Claude iOS/Android.

---

## Live Deployment

This server is deployed on **FastMCP Cloud** and accessible at:

```
https://splendid-gold-dingo.fastmcp.app/mcp
```

No local setup required to connect — just point your MCP client to the URL above.

---

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard developed by Anthropic that allows AI models to securely interact with external tools and data sources. This project implements a **remote MCP server** that exposes expense-tracking capabilities as tools that any MCP-compatible AI client can discover and invoke.

---

## Features

- **Add Expenses** — Log expenses with date, amount, category, subcategory, and notes
- **List Expenses** — Retrieve all expenses within a date range
- **Summarize Expenses** — Get category-wise spending breakdowns for any period
- **Categories Resource** — Expose predefined expense categories to MCP clients
- **Async SQLite** — Non-blocking database operations using `aiosqlite` with WAL journal mode
- **Cross-platform Access** — Works on Claude Desktop, Claude Web, and Claude Mobile

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| MCP Framework | [FastMCP](https://github.com/jlowin/fastmcp) |
| Language | Python 3.11+ |
| Database | SQLite (via `aiosqlite`) |
| Transport | Streamable HTTP (cloud) + STDIO (local proxy) |
| Deployment | FastMCP Cloud |

---

## Project Structure

```
├── main.py          # MCP server with expense tracking tools
├── proxy.py         # Local STDIO proxy → FastMCP Cloud bridge
├── categories.json  # Default expense categories
└── pyproject.toml   # Project dependencies
```

---

## MCP Tools Exposed

### `add_expense`
Add a new expense entry to the database.
```
Parameters: date, amount, category, subcategory (optional), note (optional)
```

### `list_expenses`
List all expenses within an inclusive date range.
```
Parameters: start_date, end_date
```

### `summarize`
Get a category-wise summary of expenses for a date range.
```
Parameters: start_date, end_date, category (optional)
```

### Resource: `expense:///categories`
Returns a JSON list of available expense categories.

---

## Connecting to This Server

### Option 1: Claude Web / Claude Mobile
1. Go to [claude.ai](https://claude.ai) → **Settings → Connectors → Add Custom Connector**
2. Enter the server URL: `https://splendid-gold-dingo.fastmcp.app/mcp`
3. Settings automatically sync to Claude iOS and Android apps

### Option 2: Claude Desktop (via local proxy)
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "python",
      "args": ["path/to/proxy.py"]
    }
  }
}
```

### Option 3: Run the Server Locally
```bash
# Clone the repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# Install dependencies
pip install fastmcp aiosqlite

# Run the server locally
python main.py
```

---

## Dependencies

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "aiosqlite>=0.21.0",
    "fastmcp>=2.12.4",
]
```

---

## Architecture

```
Claude Desktop / Web / Mobile
         │
         ▼
   MCP Client Request
         │
         ├──(STDIO)──► proxy.py ──► FastMCP Cloud (Streamable HTTP)
         │                                    │
         └──(HTTP direct)────────────────────►│
                                              ▼
                                         main.py (MCP Server)
                                              │
                                              ▼
                                       SQLite Database
```

---

## References

- [Model Context Protocol Docs](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Claude MCP Connectors](https://support.anthropic.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers)

---

## Author

Built as part of a GenAI engineering learning project exploring **agentic tool deployment** and **MCP server architecture**.
