\# SakuraFinder



A cross-platform file indexer and instant search tool, inspired by \[Everything](https://www.voidtools.com/) — built in Python, extensible by design.



SakuraFinder indexes your files into a single portable SQLite database, watches the filesystem for changes in real time, and lets you search by name, path, extension, size, and modification time with sub-second latency.



\---



\## Features



\- \*\*Fast substring search\*\* over file names and paths

\- \*\*Real-time updates\*\* via `watchdog` (create / modify / delete / rename)

\- \*\*Portable index\*\*: a single SQLite file you can back up, sync, or inspect

\- \*\*Boolean + filter syntax\*\*: `AND`, `OR`, `NOT`, `ext:`, `size:`, `after:`, `before:`, `dir:`, `file:`, `re:`

\- \*\*Cross-platform\*\*: Windows, macOS, Linux

\- \*\*Layered architecture\*\*: daemon / storage / query API / UI are decoupled

\- \*\*CLI, GUI, and importable Python API\*\*

\- \*\*Tray + global hotkey\*\* for quick access

\- \*\*MIT licensed\*\*



\---



\## Requirements



\- Python \*\*3.10+\*\*

\- Windows 10/11, macOS 12+, or a modern Linux desktop

\- For the GUI: `PySide6` (installed automatically with the package)



\---



\## Installation



```bash

git clone https://github.com/<your-name>/sakurafinder.git

cd sakurafinder

pip install -e .

```



For development (test dependencies):



```bash

pip install -e ".\[dev]"

```



Verify:



```bash

sakurafinder --help

sakurafinder-daemon --help

sakurafinder-ui --help

```



> If `sakurafinder` is not recognized, use the module form:

> `python -m sakurafinder.cli --help`



\---



\## Project Layout



```

sakurafinder/

├── pyproject.toml

└── sakurafinder/

&#x20;   ├── \_\_init\_\_.py

&#x20;   ├── config.py            # Config load/save

&#x20;   ├── models.py            # Dataclasses: FileRecord, SearchQuery, SearchResult

&#x20;   ├── daemon.py            # Index daemon: scanner + watcher + writer

&#x20;   ├── cli.py               # Command-line search

&#x20;   ├── core/

&#x20;   │   ├── scanner.py       # os.scandir multi-threaded scan

&#x20;   │   ├── watcher.py       # watchdog → event queue

&#x20;   │   ├── indexer.py       # Batch consumer → SQLite

&#x20;   │   └── utils.py         # Path normalization, exclude rules

&#x20;   ├── storage/

&#x20;   │   ├── db.py            # SQLite schema, connection

&#x20;   │   └── repo.py          # File record read/write

&#x20;   ├── search/

&#x20;   │   ├── parser.py        # Query syntax → SearchQuery

&#x20;   │   └── engine.py        # SearchQuery → SQL

&#x20;   ├── api/

&#x20;   │   └── service.py       # Unified SearchService

&#x20;   └── ui/

&#x20;       ├── app.py           # Qt app entry, system tray

&#x20;       ├── main\_window.py   # Search box + results table

&#x20;       └── result\_model.py  # QAbstractTableModel

```



\---



\## Quick Start



\### 1. Create a configuration file



Config lives at `\~/.sakurafinder/config.json` (`C:\\Users\\<you>\\.sakurafinder\\config.json` on Windows).



Generate a minimal one with Python to avoid JSON escape pitfalls on Windows:



```python

import json, os

p = os.path.expanduser("\~/.sakurafinder/config.json")

os.makedirs(os.path.dirname(p), exist\_ok=True)

cfg = {

&#x20;   "roots": \[

&#x20;       {

&#x20;           "path": os.path.expanduser("\~"),

&#x20;           "enabled": True,

&#x20;           "excludes": \[

&#x20;               "\*\*/node\_modules/\*\*",

&#x20;               "\*\*/.git/\*\*",

&#x20;               "\*\*/\_\_pycache\_\_/\*\*",

&#x20;               "\*\*/AppData/Local/Temp/\*\*"

&#x20;           ]

&#x20;       }

&#x20;   ],

&#x20;   "scan\_workers": 8,

&#x20;   "enable\_content\_index": False,

&#x20;   "debounce\_ms": 120,

&#x20;   "page\_size": 500

}

with open(p, "w", encoding="utf-8") as f:

&#x20;   json.dump(cfg, f, ensure\_ascii=False, indent=2)

```



Save as `write\_cfg.py` and run:



```bash

python write\_cfg.py

```



\### 2. Build the initial index



```bash

python -m sakurafinder.daemon --scan --no-watch

```



You will see progress like:



```

\[scan] indexed 5000...

\[scan] done: 123456 records in 45.3s

```



\### 3. Search from the CLI



```bash

python -m sakurafinder.cli "report ext:pdf size:>1MB" --limit 20

python -m sakurafinder.cli "notes -old" --sort mtime --desc

```



\### 4. Start real-time monitoring (optional)



Keep this running in a terminal:



```bash

python -m sakurafinder.daemon

```



Output: `\[daemon] watching... Ctrl+C to stop`



\### 5. Launch the GUI



In another terminal:



```bash

python -m sakurafinder.ui.app

```



\---



\## Search Syntax



| Example | Meaning |

|---|---|

| `report` | Substring match on name or path |

| `report draft` | Both must match (AND) |

| `report \\| draft` | Either matches (OR) |

| `report -draft` | Contains `report`, excludes `draft` |

| `ext:py` | Extension filter |

| `ext:py,js` | Multiple extensions |

| `size:>1MB` | Size greater than 1 MB (`<`, `<=`, `=`, `>=` also supported; units: B, K, M, G, T) |

| `after:2024-01-01` | Modified after this date |

| `before:2024-12-31` | Modified before this date |

| `dir:` | Directories only |

| `file:` | Files only |

| `re:^report\_.\*\\.pdf$` | Regular expression (applied to a candidate set) |

| `\*report\*` | Wildcards `\*` and `?` supported |



Sort and pagination are CLI options:



```bash

python -m sakurafinder.cli "log" --sort size --desc --limit 50 --offset 100

```



Sort keys: `name`, `path`, `size`, `mtime`.



\---



\## GUI Usage



| Action | Result |

|---|---|

| Type in the search box | Live results (120 ms debounce) |

| \*\*Double-click\*\* a row | Open the file with the default application |

| \*\*Right-click → Open\*\* | Same as double-click |

| \*\*Right-click → Open containing folder\*\* | Explorer/Finder opens with the file selected |

| \*\*Right-click → Copy path\*\* | Copies path(s); multi-select yields multiple lines |

| \*\*Right-click → Delete (to trash)\*\* | Requires `send2trash`; refreshes the list afterwards |

| `Ctrl+L` | Focus the search box |

| Close window | Hides to system tray (app keeps running) |

| Tray → Show / Quit | Restore window / exit |



> The GUI only \*\*reads\*\* the SQLite index. To see live filesystem changes, the \*\*daemon must be running\*\*.



\---



\## Configuration Reference



`\~/.sakurafinder/config.json`:



| Field | Type | Default | Description |

|---|---|---|---|

| `roots` | list | `\[]` | Index roots. Each item: `{path, enabled, excludes}` |

| `index\_db` | string | `""` | Custom DB path; empty uses `\~/.sakurafinder/index.db` |

| `enable\_content\_index` | bool | `false` | Enable FTS5 full-text content index (experimental) |

| `max\_content\_size` | int | `2097152` | Max bytes of file content to index (2 MB) |

| `scan\_workers` | int | `4` | Threads used during full scan |

| `debounce\_ms` | int | `120` | Search debounce in the GUI |

| `page\_size` | int | `500` | Results per page |

| `hotkey` | string | `Ctrl+Alt+Space` | Global hotkey to focus the search box |



`excludes` uses `fnmatch` patterns with `/` separators (Windows paths are normalized internally).



\---



\## Python API



```python

from sakurafinder import load\_config

from sakurafinder.api import SearchService



svc = SearchService(load\_config())

res = svc.search("report ext:pdf", limit=50, sort\_by="mtime", sort\_desc=True)



print(res.total, "results in", f"{res.elapsed\_ms:.1f} ms")

for r in res.items:

&#x20;   print(r.path, r.size, r.mtime)

```



This is the same entry point used by the CLI, GUI, and any future HTTP server.



\---



\## Command-Line Reference



\### `sakurafinder` (search)



```

usage: sakurafinder \[-h] \[--limit N] \[--offset N]

&#x20;                   \[--sort {name,path,size,mtime}] \[--desc] \[query]

```



\### `sakurafinder-daemon` (index)



```

usage: sakurafinder-daemon \[-h] \[--scan] \[--no-watch]



&#x20; --scan      Perform a full scan on startup

&#x20; --no-watch  Do not start the filesystem watcher

```



\### `sakurafinder-ui` (GUI)



```

usage: sakurafinder-ui

```



\---



\## Running in the Background (Windows)



To keep the daemon running without a console window, register a Scheduled Task:



```powershell

$pyw = (Get-Command pythonw.exe).Source

$proj = "C:\\path\\to\\sakurafinder"

$action  = New-ScheduledTaskAction -Execute $pyw -Argument "-m sakurafinder.daemon" -WorkingDirectory $proj

$trigger = New-ScheduledTaskTrigger -AtLogOn

Register-ScheduledTask -TaskName "SakuraFinderDaemon" -Action $action -Trigger $trigger

```



Manage with `Start-ScheduledTask` / `Stop-ScheduledTask` / `Unregister-ScheduledTask`.



On macOS/Linux, use `launchd` or `systemd --user` with the equivalent command.



\---



\## Troubleshooting



| Symptom | Cause | Fix |

|---|---|---|

| `未配置索引根目录` / `no roots configured` | `config.json` missing or `roots` empty | Recreate config (see Quick Start) |

| `ModuleNotFoundError: No module named 'sakurafinder'` | Stale editable install | `pip uninstall -y sakurafinder \&\& pip install -e .` |

| `No module named 'sakurafinder.core.scanner'` | File named `scanners.py` | Rename to `scanner.py` |

| Search returns nothing | Index empty or daemon not run | Run `--scan`; check `SearchService.stats()` |

| New files don't appear | Daemon not running | Start `python -m sakurafinder.daemon` |

| Chinese filenames not found | Encoding issue | Ensure config saved as UTF-8; run `chcp 65001` |

| Deleted files still appear | Scan is upsert-only; no prune yet | Delete files while daemon is running, or clear DB and rescan |

| GUI shows nothing but CLI works | Different DB paths | Compare `load\_config().resolved\_db\_path()` in both |



\---



\## Roadmap



\- \[x] MVP: scan, watch, SQLite index, CLI, GUI, filters

\- \[ ] FTS5 content index (opt-in)

\- \[ ] Relevance ranking (exact > prefix > substring)

\- \[ ] Tag / bookmark system

\- \[ ] Local HTTP / gRPC query API

\- \[ ] Content preview with match highlighting

\- \[ ] Periodic drift-check for incremental index robustness

\- \[ ] Windows USN Journal / MFT reader (optional, for parity with Everything)



\---



\## License



Released under the \*\*MIT License\*\*. See \[LICENSE](LICENSE).



```

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



\---



\## Acknowledgements



Inspired by \[Everything](https://www.voidtools.com/) by voidtools. Built with \[watchdog](https://github.com/gorakhargosh/watchdog), \[PySide6](https://doc.qt.io/qtforpython/), and Python's standard `sqlite3`.

