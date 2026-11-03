\# SakuraFinder



一款跨平台的文件索引与即时搜索工具，灵感来自 \[Everything](https://www.voidtools.com/)。使用 Python 编写，架构可扩展。



SakuraFinder 把文件元数据索引到\*\*单个可移植的 SQLite 文件\*\*中，通过 `watchdog` 实时感知文件系统变化，并支持按文件名、路径、扩展名、大小、修改时间进行\*\*亚秒级\*\*搜索。



\---



\## 功能特性



\- \*\*文件名 / 路径子串搜索\*\*，毫秒级响应

\- \*\*实时增量更新\*\*：借助 `watchdog` 捕获新建 / 修改 / 删除 / 重命名

\- \*\*索引可移植\*\*：就是一个 SQLite 文件，可备份、可同步、可被其他程序读取

\- \*\*布尔与过滤语法\*\*：`AND`、`OR`、`NOT`、`ext:`、`size:`、`after:`、`before:`、`dir:`、`file:`、`re:`

\- \*\*跨平台\*\*：Windows、macOS、Linux

\- \*\*分层架构\*\*：索引守护进程 / 存储 / 查询 API / UI 相互解耦，任一层可独立替换

\- \*\*CLI、GUI 与可 import 的 Python API\*\*

\- \*\*托盘常驻 + 全局快捷键\*\*

\- \*\*MIT 协议开源\*\*



\---



\## 环境要求



\- Python \*\*3.10+\*\*

\- Windows 10/11、macOS 12+，或现代 Linux 桌面

\- GUI 依赖 `PySide6`（随包自动安装）



\---



\## 安装



```bash

git clone https://github.com/<your-name>/sakurafinder.git

cd sakurafinder

pip install -e .

```



开发环境（含测试依赖）：



```bash

pip install -e ".\[dev]"

```



验证安装：



```bash

sakurafinder --help

sakurafinder-daemon --help

sakurafinder-ui --help

```



> 如果 `sakurafinder` 命令无法识别，可用模块方式：

> `python -m sakurafinder.cli --help`



\---



\## 目录结构



```

sakurafinder/

├── pyproject.toml

└── sakurafinder/

&#x20;   ├── \_\_init\_\_.py

&#x20;   ├── config.py            # 配置读写

&#x20;   ├── models.py            # 数据类：FileRecord、SearchQuery、SearchResult

&#x20;   ├── daemon.py            # 索引守护进程：扫描 + 监控 + 写库

&#x20;   ├── cli.py               # 命令行搜索

&#x20;   ├── core/

&#x20;   │   ├── scanner.py       # os.scandir 多线程扫描

&#x20;   │   ├── watcher.py       # watchdog → 事件队列

&#x20;   │   ├── indexer.py       # 批量消费事件 → SQLite

&#x20;   │   └── utils.py         # 路径规范化、排除规则

&#x20;   ├── storage/

&#x20;   │   ├── db.py            # SQLite 建表与连接

&#x20;   │   └── repo.py          # 文件记录读写

&#x20;   ├── search/

&#x20;   │   ├── parser.py        # 查询语法 → SearchQuery

&#x20;   │   └── engine.py        # SearchQuery → SQL

&#x20;   ├── api/

&#x20;   │   └── service.py       # 统一查询服务 SearchService

&#x20;   └── ui/

&#x20;       ├── app.py           # Qt 应用入口、系统托盘

&#x20;       ├── main\_window.py   # 搜索框 + 结果表

&#x20;       └── result\_model.py  # QAbstractTableModel

```



\---



\## 快速开始



\### 1. 生成配置文件



配置默认位于 `\~/.sakurafinder/config.json`（Windows 上是 `C:\\Users\\<你的用户名>\\.sakurafinder\\config.json`）。



\*\*推荐用 Python 生成\*\*，可以避免 Windows 上手写 JSON 的 `\\` 转义坑：



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



保存为 `write\_cfg.py` 后执行：



```bash

python write\_cfg.py

```



\### 2. 建立初始索引



```bash

python -m sakurafinder.daemon --scan --no-watch

```



会看到类似进度输出：



```

\[scan] indexed 5000...

\[scan] done: 123456 records in 45.3s

```



\### 3. 命令行搜索



```bash

python -m sakurafinder.cli "报告 ext:pdf size:>1MB" --limit 20

python -m sakurafinder.cli "notes -old" --sort mtime --desc

```



\### 4. 启动实时监控（可选，但推荐）



保持在一个终端窗口常驻：



```bash

python -m sakurafinder.daemon

```



输出：`\[daemon] watching... Ctrl+C to stop`



\### 5. 打开图形界面



另开一个终端：



```bash

python -m sakurafinder.ui.app

```



\---



\## 查询语法



| 示例 | 含义 |

|---|---|

| `报告` | 文件名或路径包含"报告" |

| `报告 draft` | 同时包含（AND） |

| `报告 \\| draft` | 任一包含（OR） |

| `报告 -draft` | 含"报告"，排除含"draft" |

| `ext:py` | 扩展名过滤 |

| `ext:py,js` | 多个扩展名 |

| `size:>1MB` | 大小大于 1 MB（还支持 `<`、`<=`、`=`、`>=`，单位 B/K/M/G/T） |

| `after:2024-01-01` | 修改时间晚于该日期 |

| `before:2024-12-31` | 修改时间早于该日期 |

| `dir:` | 只搜目录 |

| `file:` | 只搜文件 |

| `re:^report\_.\*\\.pdf$` | 正则（在候选集上后过滤） |

| `\*报告\*` | 支持 `\*`、`?` 通配符 |



排序与分页通过命令行参数传入：



```bash

python -m sakurafinder.cli "日志" --sort size --desc --limit 50 --offset 100

```



排序键：`name`、`path`、`size`、`mtime`。



\---



\## GUI 使用



| 操作 | 效果 |

|---|---|

| 在搜索框输入 | 边输入边出结果（120ms 防抖） |

| \*\*双击\*\*结果行 | 用系统默认程序打开 |

| \*\*右键 → 打开\*\* | 同双击 |

| \*\*右键 → 打开所在目录\*\* | 资源管理器 / Finder 定位并选中该文件 |

| \*\*右键 → 复制路径\*\* | 复制路径；多选时每行一个 |

| \*\*右键 → 删除（进回收站）\*\* | 需安装 `send2trash`；删完自动刷新 |

| `Ctrl+L` | 焦点回到搜索框 |

| 关闭窗口 | 缩到系统托盘（应用继续运行） |

| 托盘 → 显示 / 退出 | 恢复窗口 / 退出应用 |



> \*\*注意\*\*：GUI 只\*\*读\*\* SQLite 索引。想实时看到新文件，\*\*守护进程必须正在运行\*\*。



\---



\## 配置项



`\~/.sakurafinder/config.json`：



| 字段 | 类型 | 默认 | 说明 |

|---|---|---|---|

| `roots` | list | `\[]` | 索引根目录，每项格式 `{path, enabled, excludes}` |

| `index\_db` | string | `""` | 自定义数据库路径；为空则用 `\~/.sakurafinder/index.db` |

| `enable\_content\_index` | bool | `false` | 启用 FTS5 全文内容索引（实验性） |

| `max\_content\_size` | int | `2097152` | 内容索引的最大文件大小（2 MB） |

| `scan\_workers` | int | `4` | 全量扫描线程数 |

| `debounce\_ms` | int | `120` | GUI 搜索防抖时间（毫秒） |

| `page\_size` | int | `500` | 每页结果条数 |

| `hotkey` | string | `Ctrl+Alt+Space` | 唤起搜索框的全局快捷键 |



`excludes` 使用 `fnmatch` 通配符，路径分隔符统一用 `/`（Windows 的 `\\` 会在内部被规范化）。



\---



\## Python API



```python

from sakurafinder import load\_config

from sakurafinder.api import SearchService



svc = SearchService(load\_config())

res = svc.search("报告 ext:pdf", limit=50, sort\_by="mtime", sort\_desc=True)



print(res.total, "条结果，用时", f"{res.elapsed\_ms:.1f} ms")

for r in res.items:

&#x20;   print(r.path, r.size, r.mtime)

```



CLI、GUI 以及未来可能的 HTTP 服务共用这一入口。



\---



\## 命令参考



\### `sakurafinder`（搜索）



```

usage: sakurafinder \[-h] \[--limit N] \[--offset N]

&#x20;                   \[--sort {name,path,size,mtime}] \[--desc] \[query]

```



\### `sakurafinder-daemon`（索引）



```

usage: sakurafinder-daemon \[-h] \[--scan] \[--no-watch]



&#x20; --scan      启动时执行一次全量扫描

&#x20; --no-watch  不启动实时监控

```



\### `sakurafinder-ui`（图形界面）



```

usage: sakurafinder-ui

```



\---



\## 后台常驻（Windows）



希望守护进程开机自启、无黑窗口运行，可以用计划任务：



```powershell

$pyw = (Get-Command pythonw.exe).Source

$proj = "C:\\path\\to\\sakurafinder"

$action  = New-ScheduledTaskAction -Execute $pyw -Argument "-m sakurafinder.daemon" -WorkingDirectory $proj

$trigger = New-ScheduledTaskTrigger -AtLogOn

Register-ScheduledTask -TaskName "SakuraFinderDaemon" -Action $action -Trigger $trigger

```



用 `Start-ScheduledTask` / `Stop-ScheduledTask` / `Unregister-ScheduledTask` 管理。



macOS / Linux 上可用 `launchd` 或 `systemd --user` 实现同等效果。



\---



\## 常见问题



| 现象 | 原因 | 解决 |

|---|---|---|

| `未配置索引根目录` / `no roots configured` | `config.json` 不存在或 `roots` 为空 | 按"快速开始"重新生成配置 |

| `ModuleNotFoundError: No module named 'sakurafinder'` | editable 安装残留 | `pip uninstall -y sakurafinder \&\& pip install -e .` |

| `No module named 'sakurafinder.core.scanner'` | 文件名是 `scanners.py` | 重命名为 `scanner.py` |

| 搜什么都空 | 索引没建 / 守护进程没跑 | 执行 `--scan`；检查 `SearchService.stats()` |

| 新建文件搜不到 | 守护进程没启动 | 启动 `python -m sakurafinder.daemon` |

| 中文文件名搜不到 | 编码问题 | 配置存 UTF-8；终端 `chcp 65001` |

| 删除的文件还能搜到 | 扫描是 upsert，暂不清理失效记录 | 守护进程开着时删除，或清库重扫 |

| GUI 空但 CLI 能搜到 | 两者使用了不同 DB | 分别打印 `load\_config().resolved\_db\_path()` 对比 |



\---



\## 路线图



\- \[x] MVP：扫描、监控、SQLite 索引、CLI、GUI、过滤

\- \[ ] FTS5 内容全文索引（可选开启）

\- \[ ] 相关性排序（精确 > 前缀 > 子串）

\- \[ ] 标签 / 收藏系统

\- \[ ] 本地 HTTP / gRPC 查询接口

\- \[ ] 内容预览与匹配高亮

\- \[ ] 周期性校验，减少增量索引"漂移"

\- \[ ] Windows USN Journal / MFT 直读（可选，对标 Everything）



\---



\## 开源协议



使用 \*\*MIT 协议\*\*。见 \[LICENSE](LICENSE)。



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



\## 致谢



灵感来自 voidtools 的 \[Everything](https://www.voidtools.com/)。实现依赖 \[watchdog](https://github.com/gorakhargosh/watchdog)、\[PySide6](https://doc.qt.io/qtforpython/) 以及 Python 标准库 `sqlite3`。

