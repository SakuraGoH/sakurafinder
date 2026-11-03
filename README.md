English | [简体中文](README.zh-CN.md)

# SakuraFinder

> A cross-platform file indexer and instant search tool, inspired by [Everything](https://www.voidtools.com/). Built in Python, extensible by design.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#requirements)
[![Status](https://img.shields.io/badge/status-MVP-orange.svg)](#roadmap)

SakuraFinder indexes your files into a single portable SQLite database, watches the filesystem for changes in real time, and lets you search by name, path, extension, size, and modification time with sub-second latency.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Search Syntax](#search-syntax)
- [GUI Usage](#gui-usage)
- [Configuration](#configuration)
- [Python API](#python-api)
- [Command Line](#command-line)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

- **Fast substring search** over file names and paths
- **Real-time updates** via [`watchdog`](https://github.com/gorakhargosh/watchdog) (create / modify / delete / rename)
- **Portable index** — a single SQLite file you can back up, sync, or inspect
- **Boolean and filter syntax** — `AND`, `OR`, `NOT`, `ext:`, `size:`, `after:`, `before:`, `dir:`, `file:`, `re:`
- **Cross-platform** — Windows, macOS, Linux
- **Layered architecture** — daemon / storage / query API / UI are decoupled
- **CLI, GUI, and importable Python API**
- **System tray + global hotkey** for quick access
- **MIT licensed**

---

## Requirements

| Component | Version |
|---|---|
| Python | 3.10 or newer |
| OS | Windows 10/11, macOS 12+, modern Linux desktop |
| GUI | [`PySide6`](https://doc.qt.io/qtforpython/) (installed automatically) |

---

## Installation

```bash
git clone https://github.com/SakuraGoH/sakurafinder.git
cd sakurafinder
pip install -e .
```

For development (test dependencies):

```bash
pip install -e ".[dev]"
```

Verify the installation:

```bash
sakurafinder --help
sakurafinder-daemon --help
sakurafinder-ui --help
```

> If `sakurafinder` is not recognized, use the module form: `python -m sakurafinder.cli --help`.

---

## Quick Start

### 1. Create a configuration file

The config lives at `~/.sakurafinder/config.json` (`C:\Users\<you>\.sakurafinder\config.json` on Windows).

Generating it with Python avoids JSON escape pitfalls on Windows:

```python
import json, os

p = os.path.expanduser("~/.sakurafinder/config.json")
os.makedirs(os.path.dirname(p), exist_ok=True)

cfg = {
    "roots": [
        {
            "path": os.path.expanduser("~"),
            "enabled": True,
            "excludes": [
                "**/node_modules/**",
                "**/.git/**",
                "**/__pycache__/**",
                "**/AppData/Local/Temp/**",
            ],
        }
    ],
    "scan_workers": 8,
    "enable_content_index": False,
    "debounce_ms": 120,
    "page_size": 500,
}

with open(p, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print("wrote:", p)
```

Save as `write_cfg.py` and run:

```bash
python write_cfg.py
```

### 2. Build the initial index

```bash
python -m sakurafinder.daemon --scan --no-watch
```

Expected output:

```text
[scan] indexed 5000...
[scan] done: 123456 records in 45.3s
```

### 3. Search from the CLI

```bash
python -m sakurafinder.cli "report ext:pdf size:>1MB" --limit 20
python -m sakurafinder.cli "notes -old" --sort mtime --desc
```

### 4. Start real-time monitoring (optional, recommended)

Keep this running in a terminal:

```bash
python -m sakurafinder.daemon
```

Expected output:

```text
[daemon] watching... Ctrl+C to stop
```

### 5. Launch the GUI

In another terminal:

```bash
python -m sakurafinder.ui.app
```

---

## Search Syntax

| Example | Meaning |
|---|---|
| `report` | Substring match on name or path |
| `report draft` | Both must match (AND) |
| `report \| draft` | Either matches (OR) |
| `report -draft` | Contains `report`, excludes `draft` |
| `ext:py` | Filter by extension |
| `ext:py,js` | Multiple extensions |
| `size:>1MB` | Larger than 1 MB (`<`, `<=`, `=`, `>=` supported; units B, K, M, G, T) |
| `after:2024-01-01` | Modified after this date |
| `before:2024-12-31` | Modified before this date |
| `dir:` | Directories only |
| `file:` | Files only |
| `re:^report_.*\.pdf$` | Regular expression (applied to a candidate set) |
| `*report*` | Wildcards `*` and `?` supported |

Sorting and pagination are CLI options:

```bash
python -m sakurafinder.cli "log" --sort size --desc --limit 50 --offset 100
```

Sort keys: `name`, `path`, `size`, `mtime`.

---

## GUI Usage

| Action | Result |
|---|---|
| Type in the search box | Live results (120 ms debounce) |
| **Double-click** a row | Open with the default application |
| **Right-click → Open** | Same as double-click |
| **Right-click → Open containing folder** | File manager opens with the file selected |
| **Right-click → Copy path** | Copies path(s); multi-select yields one per line |
| **Right-click → Delete (to trash)** | Requires `send2trash`; refreshes the list afterwards |
| `Ctrl+L` | Focus the search box |
| Close window | Hides to system tray (app keeps running) |
| Tray → Show / Quit | Restore window / exit |

> The GUI only **reads** the SQLite index. To see live filesystem changes, the **daemon must be running**.

---

## Configuration

`~/.sakurafinder/config.json`:

| Field | Type | Default | Description |
|---|---|---|---|
| `roots` | list | `[]` | Index roots. Each item: `{path, enabled, excludes}` |
| `index_db` | string | `""` | Custom DB path; empty uses `~/.sakurafinder/index.db` |
| `enable_content_index` | bool | `false` | Enable FTS5 full-text content index (experimental) |
| `max_content_size` | int | `2097152` | Max bytes of file content to index (2 MB) |
| `scan_workers` | int | `4` | Threads used during full scan |
| `debounce_ms` | int | `120` | Search debounce in the GUI |
| `page_size` | int | `500` | Results per page |
| `hotkey` | string | `Ctrl+Alt+Space` | Global hotkey to focus the search box |

`excludes` uses `fnmatch` patterns with `/` separators (Windows paths are normalized internally).

---

## Python API

```python
from sakurafinder import load_config
from sakurafinder.api import SearchService

svc = SearchService(load_config())
res = svc.search("report ext:pdf", limit=50, sort_by="mtime", sort_desc=True)

print(f"{res.total} results in {res.elapsed_ms:.1f} ms")
for r in res.items:
    print(r.path, r.size, r.mtime)
```

The CLI, GUI, and any future HTTP server all go through this single entry point.

---

## Command Line

```text
sakurafinder [-h] [--limit N] [--offset N] [--sort {name,path,size,mtime}] [--desc] [query]
sakurafinder-daemon [-h] [--scan] [--no-watch]
sakurafinder-ui
```

| Flag | Description |
|---|---|
| `--scan` | Perform a full scan on startup |
| `--no-watch` | Do not start the filesystem watcher |
| `--limit N` | Max results (default 50) |
| `--offset N` | Skip N results (pagination) |
| `--sort` | `name`, `path`, `size`, `mtime` |
| `--desc` | Descending order |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `no roots configured` | `config.json` missing or `roots` empty | Recreate config (see Quick Start) |
| `ModuleNotFoundError: No module named 'sakurafinder'` | Stale editable install | `pip uninstall -y sakurafinder && pip install -e .` |
| `No module named 'sakurafinder.core.scanner'` | File named `scanners.py` | Rename to `scanner.py` |
| Search returns nothing | Index empty or daemon not run | Run `--scan`; check `SearchService.stats()` |
| New files don't appear | Daemon not running | Start `python -m sakurafinder.daemon` |
| Chinese filenames not found | Encoding issue | Save config as UTF-8; run `chcp 65001` |
| Deleted files still appear | Scan is upsert-only; no prune yet | Delete files while the daemon is running, or clear the DB and rescan |
| GUI shows nothing but CLI works | Different DB paths | Compare `load_config().resolved_db_path()` in both |

---

## Roadmap

- [x] MVP — scan, watch, SQLite index, CLI, GUI, filters
- [ ] FTS5 content index (opt-in)
- [ ] Relevance ranking (exact > prefix > substring)
- [ ] Tag / bookmark system
- [ ] Local HTTP / gRPC query API
- [ ] Content preview with match highlighting
- [ ] Periodic drift-check for incremental index robustness
- [ ] Windows USN Journal / MFT reader (optional, for parity with Everything)

---

## License

Released under the **MIT License**. See [LICENSE](LICENSE) for details.

```text
MIT License

Copyright (c) 2024 <your name>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgements

Inspired by [Everything](https://www.voidtools.com/) by voidtools. Built with [`watchdog`](https://github.com/gorakhargosh/watchdog), [`PySide6`](https://doc.qt.io/qtforpython/), and Python's standard `sqlite3`.
