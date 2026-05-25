# DocMemory

Local search memory for Markdown document folders.

DocMemory builds a SQLite index inside a target documentation folder. It supports:

- SQLite FTS keyword search
- optional local vector search with FastEmbed
- hybrid keyword + vector search
- experimental DirectML and OpenVINO/NPU vector builds
- a read-only MCP server for agents

## Token Efficiency

DocMemory is designed for agent workflows where loading an entire documentation folder into context is too expensive.

Instead of reading hundreds of Markdown files, an agent can call `docmemory_search` and receive only the most relevant snippets:

```text
large doc folder -> ranked snippets -> smaller prompt
```

This usually saves tokens in three ways:

- the agent avoids scanning unrelated files
- search results include only focused chunks and line ranges
- repeated questions reuse the local SQLite/vector index instead of re-reading raw docs

For best results, keep search limits small:

```powershell
uv run --extra vector docmemory search <DOC_DIR> "background worker retry behavior" --hybrid -n 5
```

For agents, prefer MCP search first, then open the original Markdown file only when the snippet is relevant.

## Workflow

1. Convert or drop documents into a Markdown folder.
2. Initialize the folder once.
3. Rebuild the index when Markdown files change.
4. Search from the CLI, or let an agent search through MCP.

```text
Markdown docs -> .docmemory/docmemory.sqlite -> CLI / MCP search
```

## Quick Start

Initialize an index inside a document folder:

```powershell
uv run docmemory init -i <DOC_DIR>
```

Build keyword + vector indexes:

```powershell
uv run --extra vector docmemory sync <DOC_DIR> --vector
```

Search:

```powershell
uv run --extra vector docmemory search <DOC_DIR> "payment retry design" --hybrid -n 5
```

Check status:

```powershell
uv run docmemory status <DOC_DIR>
```

## Search Modes

Keyword search uses SQLite FTS:

```powershell
uv run docmemory search <DOC_DIR> "API-REFERENCE"
```

Vector-only search is useful when the query has few exact words:

```powershell
uv run --extra vector docmemory search <DOC_DIR> "which document explains the background worker architecture" --vector -n 5
```

Hybrid search combines keyword and vector results:

```powershell
uv run --extra vector docmemory search <DOC_DIR> "payment retry timeout design" --hybrid -n 5
```

## Vector Models

Default model:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

FastEmbed stores model files under:

```text
.models/
```

Override the model cache if needed:

```powershell
$env:DOCMEMORY_MODEL_DIR = "D:\models\docmemory"
```

Use the model name in commands, not the local cache folder name.

## DirectML / GPU

The DirectML command is separate from the stable CPU command:

```powershell
uv run --extra directml docmemory-dml sync <DOC_DIR> --vector --model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Defaults:

```text
model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
batch: 32
```

The first embedding batch may pause while ONNX Runtime compiles the graph. Later batches print timing.

Probe DirectML before a long rebuild:

```powershell
uv run --extra directml python scripts\probe_directml_fastembed.py
```

## OpenVINO / NPU

The NPU path uses a separate Python environment at `.venv-npu` because `onnxruntime-openvino` may conflict with other ONNX Runtime builds.

Defaults:

```text
model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
batch: 32
device: NPU
precision: FP16
parallel: 2
max chars: 600
```

Useful NPU knobs:

```powershell
$env:DOCMEMORY_NPU_BATCH_SIZE = "32"
$env:DOCMEMORY_NPU_PARALLEL = "2"
$env:DOCMEMORY_NPU_MAX_CHARS = "600"
$env:DOCMEMORY_NPU_PRECISION = "FP16"
```

`DOCMEMORY_NPU_MAX_CHARS` trims long chunks before embedding to reduce wasted tokenization and inference work. The full text still stays in the SQLite text index.

NPU cache:

```text
.models/openvino-cache/
```

Probe NPU:

```powershell
<DOCMEMORY_DIR>\.venv-npu\Scripts\python.exe scripts\probe_npu_fastembed.py
```

## Windows Launchers

Optional `.bat` launchers can be placed beside a document folder for one-click rebuilds.

Recommended launcher behavior:

- rebuild vectors for the folder containing the `.bat`
- keep the database inside that folder at `.docmemory/docmemory.sqlite`
- use MiniLM for daily sync
- keep NPU/GPU launchers separate from the stable CPU launcher

## MCP Server

DocMemory includes a read-only MCP server for agents.

Tools:

```text
docmemory_status
docmemory_search
```

Example Codex config:

```toml
[mcp_servers.docmemory]
command = "uv"
args = ["run", "--directory", "<DOCMEMORY_DIR>", "--extra", "mcp", "docmemory-mcp"]
enabled = true

[mcp_servers.docmemory.env]
DOCMEMORY_TARGET = "<DOC_DIR>"
```

Use CLI or `.bat` files to rebuild vectors. Use MCP for agent search.

## Ignore Folders

Ignored by default:

```text
.docmemory
_history
.git
.svn
__pycache__
node_modules
```

Add more ignored folders during init:

```powershell
uv run docmemory init -i <DOC_DIR> --ignore old --ignore backup
```

## Storage Layout

The database is stored inside the target folder:

```text
<DOC_DIR>/.docmemory/docmemory.sqlite
```

Model files are stored inside the DocMemory project by default:

```text
<DOCMEMORY_DIR>/.models/
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=kuchris/DocMemory&type=Date)](https://www.star-history.com/#kuchris/DocMemory&Date)
