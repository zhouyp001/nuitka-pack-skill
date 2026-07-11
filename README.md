# nuitka-pack

> A Claude Code skill for packaging PySide6/PyQt applications into standalone Windows executables with Nuitka.

[中文版](README_CN.md)

## What it does

`nuitka-pack` is a [Claude Code](https://claude.ai/code) skill that automates the end-to-end process of compiling Python GUI applications into standalone `.exe` files using [Nuitka](https://nuitka.net/). It encodes hard-won operational knowledge — the flags that are easy to miss, the error messages that are cryptic, and the progress-tracking tricks for builds that take over an hour.

When you invoke this skill, Claude Code will:

1. Run through a **pre-compilation checklist** — log file configuration, Qt plugin detection, vendored dependencies, resource path fallbacks
2. Generate the correct **Nuitka command** with all necessary flags
3. Help **monitor progress** during long compilations (up to 90 minutes with PyTorch)
4. **Verify the output** — exe size, bundled resources, log file location, console mode
5. **Troubleshoot** common failures with a built-in lookup table

## Installation

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [Claude Code](https://claude.ai/code) | Latest | The AI assistant that loads this skill |
| [Nuitka](https://nuitka.net/) | 2.x+ | Tested with 4.1.3 |
| Python | 3.8+ | |
| PySide6 or PyQt | 6.x | Tested with PySide6 6.6.3.1 |
| Windows | 10/11 | The skill targets Windows standalone builds |
| C compiler | MSVC or MinGW | Required by Nuitka for C compilation |

### Install via Claude Code

```bash
# Install the skill directly
claude skill install https://github.com/zhouyp001/nuitka-pack-skill
```

### Manual installation

```bash
# Clone into your Claude Code skills directory
git clone https://github.com/zhouyp001/nuitka-pack-skill.git ~/.claude/skills/nuitka-pack
```

## Usage

Invoke the skill in Claude Code by mentioning any of these phrases:

- "用 Nuitka 打包我的 PySide6 应用"
- "compile this Python GUI to an exe"
- "package my PyQt app into a standalone executable"
- "Nuitka 编译报错 No QtMultimedia backends found"

Claude Code will recognize the intent and load the skill automatically.

## What the skill covers

### Pre-compilation checklist

Before running the compiler, the skill verifies:

- **File logging** — Apps using `--windows-disable-console` must write logs to disk (e.g., `RotatingFileHandler` → `%LOCALAPPDATA%`), otherwise crashes leave no trace.
- **Qt plugins** — Detects whether `--include-qt-plugins=multimedia` or `--include-qt-plugins=qml` is needed based on your imports.
- **Dependencies** — Maps `--include-package` and `--include-data-files` flags for vendored libraries, local modules, and model/config/DLL files.
- **Resource paths** — Ensures `__compiled__` / `sys.frozen` / `__file__` three-way fallback is in place so resources work both in development and after compilation.

### Compilation command

The skill assembles a `python -m nuitka --standalone` command with:

| Flag | Purpose |
|------|---------|
| `--enable-plugin=pyside6` | Qt bindings support |
| `--include-qt-plugins=multimedia` | QMediaPlayer / QVideoWidget / QCamera |
| `--include-qt-plugins=qml` | QML-based UIs |
| `--include-package=...` | Vendored / local packages |
| `--include-data-files=src=dst` | Model, config, and DLL files |
| `--module-parameter=torch-disable-jit=yes` | PyTorch compatibility |
| `--windows-console-mode=disable` | Hide console for GUI apps |
| `--jobs=N` | Parallel C compilation |
| `--output-dir=dist` | Output directory |

### Build time estimates

| Scenario | Duration |
|----------|----------|
| First build (with PyTorch) | ~90 min |
| Incremental (logic changes only) | ~45 min |
| Incremental (import changes) | ~75 min |
| PySide6 only (no PyTorch) | ~10 min |

### Progress monitoring

Nuitka builds with large dependencies can run silently for an hour — output buffering means the log file may show 0 lines even though the process is working. The skill provides two strategies:

**Strategy 1: Phase detection from output**

| Output pattern | Phase | Remaining |
|---------------|-------|-----------|
| `PASS 1: Optimizing module 'xxx', NNN more modules to go` | Python → C translation | ~60 min |
| `Nuitka: Generating source code for C backend compiler` | C code generation | ~5 min |
| `<clcache> /Fomodule.xxx.obj /c module.xxx.c` | C compilation (`--jobs` active) | ~25 min |
| `Backend C linking with NNN files` | Linking | ~3 min |
| 0 lines output, process memory growing | Early PASS 1 (buffered) | ~50 min |

**Strategy 2: CPU monitor**

The included `scripts/monitor_cpu.py` polls CPU usage and beeps when it drops below a threshold — the build is finished:

```bash
python scripts/monitor_cpu.py --threshold 50 --interval 60
```

### Post-compilation verification

- [ ] `.exe` file exists with reasonable size
- [ ] All resource files present alongside the exe
- [ ] App launches and core features work
- [ ] Log files generated in the expected location
- [ ] No console window pops up unexpectedly

### Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `No QtMultimedia backends found` | Missing Qt6 multimedia plugin | Add `--include-qt-plugins=multimedia` |
| "Access denied" during build | Old exe process still running | Kill the process and retry |
| Resources not found at runtime | `__file__` points inside the exe | Use `sys.executable` fallback for compiled mode |
| QMediaPlayer playback broken | Qt6 renamed `mediaservice` → `multimedia` | Add `--include-qt-plugins=multimedia` |
| Incremental build not faster | Import graph changed | Changing imports triggers full re-analysis |

## File structure

```
nuitka-pack-skill/
├── SKILL.md              # Skill definition loaded by Claude Code
├── scripts/
│   └── monitor_cpu.py    # CPU/memory monitor with beep alert on completion
├── LICENSE               # MIT License
├── README.md             # This file (English)
└── README_CN.md          # Chinese version
```

## License

MIT — see [LICENSE](LICENSE).
