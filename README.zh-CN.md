[English](README.md) | 简体中文

# SakuraFinder

> 一款跨平台的文件索引与即时搜索工具，灵感来自 [Everything](https://www.voidtools.com/)。使用 Python 编写，架构可扩展。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#环境要求)
[![Status](https://img.shields.io/badge/status-MVP-orange.svg)](#路线图)

SakuraFinder 把文件元数据索引到**单个可移植的 SQLite 文件**中，通过 [`watchdog`](https://github.com/gorakhargosh/watchdog) 实时感知文件系统变化，支持按文件名、路径、扩展名、大小、修改时间进行**亚秒级**搜索。

---

## 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装](#安装)
- [快速开始](#快速开始)
- [查询语法](#查询语法)
- [GUI 使用](#gui-使用)
- [配置项](#配置项)
- [Python API](#python-api)
- [命令行](#命令行)
- [常见问题](#常见问题)
- [路线图](#路线图)
- [开源协议](#开源协议)

---

## 功能特性

- **文件名 / 路径子串搜索**，毫秒级响应
- **实时增量更新**：借助 `watchdog` 捕获新建 / 修改 / 删除 / 重命名
- **索引可移植**：就是一个 SQLite 文件，可备份、可同步、可被其他程序读取
- **布尔与过滤语法**：`AND`、`OR`、`NOT`、`ext:`、`size:`、`after:`、`before:`、`dir:`、`file:`、`re:`
- **跨平台**：Windows、macOS、Linux
- **分层架构**：索引守护进程 / 存储 / 查询 API / UI 相互解耦，任一层可独立替换
- **CLI、GUI 与可 import 的 Python API**
- **托盘常驻 + 全局快捷键**
- **MIT 协议开源**

---

## 环境要求

| 组件 | 版本 / 说明 |
|---|---|
| Python | 3.10 或更高 |
| 操作系统 | Windows 10/11、macOS 12+、现代 Linux 桌面 |
| 图形界面 | [`PySide6`](https://doc.qt.io/qtforpython/)（随包自动安装） |

---

## 安装

```bash
git clone https://github.com/SakuraGoH/sakurafinder.git
cd sakurafinder
pip install -e .
```

开发环境（含测试依赖）：

```bash
pip install -e ".[dev]"
```

验证安装：

```bash
sakurafinder --help
sakurafinder-daemon --help
sakurafinder-ui --help
```

> 如果 `sakurafinder` 命令无法识别，可用模块方式：`python -m sakurafinder.cli --help`。

---

## 快速开始

### 1. 生成配置文件

配置默认位于 `~/.sakurafinder/config.json`（Windows 上是 `C:\Users\<你的用户名>\.sakurafinder\config.json`）。

**推荐用 Python 生成**，可以避免 Windows 上手写 JSON 的 `\` 转义坑：

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

print("已写入：", p)
```

保存为 `write_cfg.py` 后执行：

```bash
python write_cfg.py
```

### 2. 建立初始索引

```bash
python -m sakurafinder.daemon --scan --no-watch
```

预期输出：

```text
[scan] indexed 5000...
[scan] done: 123456 records in 45.3s
```

### 3. 命令行搜索

```bash
python -m sakurafinder.cli "报告 ext:pdf size:>1MB" --limit 20
python -m sakurafinder.cli "notes -old" --sort mtime --desc
```

### 4. 启动实时监控（可选，推荐）

保持在一个终端窗口常驻：

```bash
python -m sakurafinder.daemon
```

预期输出：

```text
[daemon] watching... Ctrl+C to stop
```

### 5. 打开图形界面

另开一个终端：

```bash
python -m sakurafinder.ui.app
```

---

## 查询语法

| 示例 | 含义 |
|---|---|
| `报告` | 文件名或路径包含「报告」 |
| `报告 draft` | 同时包含（AND） |
| `报告 \| draft` | 任一包含（OR） |
| `报告 -draft` | 含「报告」，排除含 `draft` |
| `ext:py` | 扩展名过滤 |
| `ext:py,js` | 多个扩展名 |
| `size:>1MB` | 大小大于 1 MB（还支持 `<`、`<=`、`=`、`>=`，单位 B/K/M/G/T） |
| `after:2024-01-01` | 修改时间晚于该日期 |
| `before:2024-12-31` | 修改时间早于该日期 |
| `dir:` | 只搜目录 |
| `file:` | 只搜文件 |
| `re:^report_.*\.pdf$` | 正则（在候选集上后过滤） |
| `*报告*` | 支持 `*`、`?` 通配符 |

排序与分页通过命令行参数传入：

```bash
python -m sakurafinder.cli "日志" --sort size --desc --limit 50 --offset 100
```

排序键：`name`、`path`、`size`、`mtime`。

---

## GUI 使用

| 操作 | 效果 |
|---|---|
| 在搜索框输入 | 边输入边出结果（120 ms 防抖） |
| **双击**结果行 | 用系统默认程序打开 |
| **右键 → 打开** | 同双击 |
| **右键 → 打开所在目录** | 资源管理器 / Finder 定位并选中该文件 |
| **右键 → 复制路径** | 复制路径；多选时每行一个 |
| **右键 → 删除（进回收站）** | 需安装 `send2trash`；删完自动刷新 |
| `Ctrl+L` | 焦点回到搜索框 |
| 关闭窗口 | 缩到系统托盘（应用继续运行） |
| 托盘 → 显示 / 退出 | 恢复窗口 / 退出应用 |

> **注意**：GUI 只**读** SQLite 索引。想实时看到新文件，**守护进程必须正在运行**。

---

## 配置项

`~/.sakurafinder/config.json`：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `roots` | list | `[]` | 索引根目录，每项格式 `{path, enabled, excludes}` |
| `index_db` | string | `""` | 自定义数据库路径；为空则用 `~/.sakurafinder/index.db` |
| `enable_content_index` | bool | `false` | 启用 FTS5 全文内容索引（实验性） |
| `max_content_size` | int | `2097152` | 内容索引的最大文件大小（2 MB） |
| `scan_workers` | int | `4` | 全量扫描线程数 |
| `debounce_ms` | int | `120` | GUI 搜索防抖时间（毫秒） |
| `page_size` | int | `500` | 每页结果条数 |
| `hotkey` | string | `Ctrl+Alt+Space` | 唤起搜索框的全局快捷键 |

`excludes` 使用 `fnmatch` 通配符，路径分隔符统一用 `/`（Windows 的 `\` 会在内部被规范化）。

---

## Python API

```python
from sakurafinder import load_config
from sakurafinder.api import SearchService

svc = SearchService(load_config())
res = svc.search("报告 ext:pdf", limit=50, sort_by="mtime", sort_desc=True)

print(f"{res.total} 条结果，用时 {res.elapsed_ms:.1f} ms")
for r in res.items:
    print(r.path, r.size, r.mtime)
```

CLI、GUI 以及未来可能的 HTTP 服务共用这一入口。

---

## 命令行

```text
sakurafinder [-h] [--limit N] [--offset N] [--sort {name,path,size,mtime}] [--desc] [query]
sakurafinder-daemon [-h] [--scan] [--no-watch]
sakurafinder-ui
```

| 参数 | 说明 |
|---|---|
| `--scan` | 启动时执行一次全量扫描 |
| `--no-watch` | 不启动实时监控 |
| `--limit N` | 最大结果数（默认 50） |
| `--offset N` | 跳过前 N 条（分页） |
| `--sort` | `name`、`path`、`size`、`mtime` |
| `--desc` | 降序 |

---

## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `未配置索引根目录` | `config.json` 不存在或 `roots` 为空 | 按「快速开始」重新生成配置 |
| `ModuleNotFoundError: No module named 'sakurafinder'` | editable 安装残留 | `pip uninstall -y sakurafinder && pip install -e .` |
| `No module named 'sakurafinder.core.scanner'` | 文件名是 `scanners.py` | 重命名为 `scanner.py` |
| 搜什么都空 | 索引没建 / 守护进程没跑 | 执行 `--scan`；检查 `SearchService.stats()` |
| 新建文件搜不到 | 守护进程没启动 | 启动 `python -m sakurafinder.daemon` |
| 中文文件名搜不到 | 编码问题 | 配置存 UTF-8；终端 `chcp 65001` |
| 删除的文件还能搜到 | 扫描是 upsert，暂不清理失效记录 | 守护进程开着时删除，或清库重扫 |
| GUI 空但 CLI 能搜到 | 两者使用了不同 DB | 分别打印 `load_config().resolved_db_path()` 对比 |

---

## 路线图

- [x] MVP — 扫描、监控、SQLite 索引、CLI、GUI、过滤
- [ ] FTS5 内容全文索引（可选开启）
- [ ] 相关性排序（精确 > 前缀 > 子串）
- [ ] 标签 / 收藏系统
- [ ] 本地 HTTP / gRPC 查询接口
- [ ] 内容预览与匹配高亮
- [ ] 周期性校验，减少增量索引「漂移」
- [ ] Windows USN Journal / MFT 直读（可选，对标 Everything）

---

## 开源协议

使用 **MIT 协议**。详见 [LICENSE](LICENSE)。

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

## 致谢

灵感来自 voidtools 的 [Everything](https://www.voidtools.com/)。实现依赖 [`watchdog`](https://github.com/gorakhargosh/watchdog)、[`PySide6`](https://doc.qt.io/qtforpython/) 以及 Python 标准库 `sqlite3`。
