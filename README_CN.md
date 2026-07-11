# nuitka-pack

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0-green.svg)](https://github.com/zhouyp001/nuitka-pack-skill/releases/tag/v1.0)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

> 一个用 Nuitka 将 PySide6/PyQt 应用打包为 Windows 独立可执行文件的 Claude Code 技能。

[English](README.md)

## 能做什么

`nuitka-pack` 是一个 [Claude Code](https://claude.ai/code) 技能，用 [Nuitka](https://nuitka.net/) 将 Python GUI 应用编译成独立的 `.exe` 文件。它编码了大量实战经验——容易遗漏的编译参数、晦涩的报错信息、以及一小时以上编译的进度追踪技巧。

当你触发这个技能时，Claude Code 会：

1. 逐项确认**编译前检查清单**——日志配置、Qt 插件、依赖包、资源路径回退
2. 生成带有所有必要参数的**完整编译命令**
3. 在长时间编译过程中**监控进度**（含 PyTorch 时最长 90 分钟）
4. **验证产物**——exe 大小、资源文件、日志位置、控制台模式
5. 通过内置速查表**诊断常见错误**

## 安装

### 环境要求

| 工具 | 版本 | 说明 |
|------|------|------|
| [Claude Code](https://claude.ai/code) | 最新版 | 加载此技能的 AI 助手 |
| [Nuitka](https://nuitka.net/) | 2.x+ | 实测 4.1.3 可用 |
| Python | 3.8+ | |
| PySide6 或 PyQt | 6.x | 实测 PySide6 6.6.3.1 可用 |
| Windows | 10/11 | 此技能面向 Windows 平台 |
| C 编译器 | MSVC 或 MinGW | Nuitka 编译 C 代码所需 |

### 通过 Claude Code 安装

```bash
# 直接安装技能
claude skill install https://github.com/zhouyp001/nuitka-pack-skill
```

### 手动安装

```bash
# 克隆到 Claude Code 的 skills 目录
git clone https://github.com/zhouyp001/nuitka-pack-skill.git ~/.claude/skills/nuitka-pack
```

## 使用方式

在 Claude Code 中提到以下任何短语即可触发技能：

- "用 Nuitka 打包我的 PySide6 应用"
- "把这个 Python GUI 编译成 exe"
- "package my PyQt app into a standalone executable"
- "Nuitka 编译报错 No QtMultimedia backends found"

Claude Code 会自动识别意图并加载技能。

## 技能覆盖的内容

### 编译前检查清单

运行编译器之前，技能会验证：

- **文件日志** — 使用了 `--windows-disable-console` 的应用必须将日志写到磁盘（例如 `RotatingFileHandler` → `%LOCALAPPDATA%`），否则崩溃时看不到任何错误信息。
- **Qt 插件** — 根据代码中的 import 检测是否需要 `--include-qt-plugins=multimedia` 或 `--include-qt-plugins=qml`。
- **依赖和资源** — 为 vendored 库、本地模块、模型/配置/DLL 文件映射相应的 `--include-package` 和 `--include-data-files` 参数。
- **资源路径** — 确保代码中有 `__compiled__` / `sys.frozen` / `__file__` 三段式回退，让资源在开发环境和编译后都能正常访问。

### 编译命令

技能组装出完整的 `python -m nuitka --standalone` 命令，包含：

| 参数 | 用途 |
|------|------|
| `--enable-plugin=pyside6` | Qt 绑定支持 |
| `--include-qt-plugins=multimedia` | QMediaPlayer / QVideoWidget / QCamera |
| `--include-qt-plugins=qml` | QML 界面 |
| `--include-package=...` | 第三方/本地包 |
| `--include-data-files=src=dst` | 模型、配置和 DLL 文件 |
| `--module-parameter=torch-disable-jit=yes` | PyTorch 兼容性 |
| `--windows-console-mode=disable` | GUI 应用隐藏控制台 |
| `--jobs=N` | 并行 C 编译 |
| `--output-dir=dist` | 输出目录 |

### 编译耗时预估

| 场景 | 耗时 |
|------|------|
| 首次编译（含 PyTorch） | ~90 分钟 |
| 增量编译（仅改内部逻辑） | ~45 分钟 |
| 增量编译（改了 import） | ~75 分钟 |
| 仅 PySide6（无 PyTorch） | ~10 分钟 |

### 进度监控

带有大型依赖的 Nuitka 编译可能静默运行一小时——输出缓冲会导致日志文件显示 0 行，但进程实际正在运行。技能提供两种监控策略：

**策略一：从输出判断阶段**

| 输出特征 | 当前阶段 | 剩余时间 |
|---------|---------|---------|
| `PASS 1: Optimizing module 'xxx', NNN more modules to go` | Python → C 翻译 | ~60 分钟 |
| `Nuitka: Generating source code for C backend compiler` | C 代码生成 | ~5 分钟 |
| `<clcache> /Fomodule.xxx.obj /c module.xxx.c` | C 编译（`--jobs` 生效） | ~25 分钟 |
| `Backend C linking with NNN files` | 链接 | ~3 分钟 |
| 输出 0 行，进程内存持续增长 | PASS 1 初期（输出缓冲） | ~50 分钟 |

**策略二：CPU 监控脚本**

项目自带的 `scripts/monitor_cpu.py` 会定期采样 CPU 占用，编译结束后 CPU 骤降时蜂鸣提醒：

```bash
python scripts/monitor_cpu.py --threshold 50 --interval 60
```

### 编译后验证清单

- [ ] `.exe` 文件存在且大小合理
- [ ] 所有资源文件在 exe 同级目录
- [ ] 应用能正常启动且核心功能可用
- [ ] 日志文件生成在预期位置
- [ ] 没有意外弹出控制台窗口

### 常见问题速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `No QtMultimedia backends found` | 缺少 Qt6 multimedia 插件 | 添加 `--include-qt-plugins=multimedia` |
| 编译时报"拒绝访问" | 旧 exe 进程仍在运行 | 结束进程后重试 |
| 运行时找不到资源文件 | `__file__` 指向 exe 内部 | 编译模式使用 `sys.executable` 回退 |
| QMediaPlayer 播放异常 | Qt6 把 `mediaservice` 改名为 `multimedia` | 添加 `--include-qt-plugins=multimedia` |
| 增量编译速度没提升 | import 依赖图发生了变化 | 修改 import 会触发全量重新分析 |

## 目录结构

```
nuitka-pack-skill/
├── SKILL.md              # 技能定义文件（Claude Code 加载）
├── scripts/
│   └── monitor_cpu.py    # CPU/内存监控脚本，编译完成后蜂鸣提醒
├── LICENSE               # MIT 许可证
├── README.md             # 英文说明
└── README_CN.md          # 本文件（中文说明）
```

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
