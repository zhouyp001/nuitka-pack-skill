---
name: nuitka-pack
description: 用 Nuitka 将 PySide6/PyQt 应用打包为 Windows 独立可执行文件。当用户需要打包 Python GUI 应用、编译为 exe、或 Nuitka 编译遇到问题时使用此 skill。
metadata:
  generatedBy: "1.0"
  verifiedOn: "2026-07-12"
  verifiedWith: "Nuitka 4.1.3, PySide6 6.6.3.1, torch 2.x, Python 3.8"
---

用 Nuitka 将 Python 应用编译为 standalone 可执行文件。

## 编译前准备（必须逐项确认）

### 1. 文件日志
如果用了 `--windows-disable-console`，确认日志能写入文件（RotatingFileHandler → `%LOCALAPPDATA%/`），否则出了问题看不到错误。

### 2. Qt 插件
检查代码中是否使用了这些模块：

| 用了什么 | 必须加的参数 |
|---------|------------|
| QMediaPlayer / QVideoWidget / QCamera | `--include-qt-plugins=multimedia` |
| QML 界面 | `--include-qt-plugins=qml` |
| SVG 图标 | 默认已包含 |

**multimedia 最容易漏**——Qt6 把插件名从 `mediaservice` 改为 `multimedia`，Nuitka 默认列表没跟上。缺了的症状是 `No QtMultimedia backends found`。

### 3. 依赖和资源
- vendored 目录 → `--include-package=xxx`
- 本地模块 → `--include-package=processor --include-package=gui`
- 模型/配置/DLL 文件 → `--include-data-files=src=dst`
- torch 项目 → `--module-parameter=torch-disable-jit=yes`

### 4. 路径适配
确认代码中有 `__compiled__` / `sys.frozen` / `__file__` 三段式 fallback 来定位资源文件。

### 5. 性能
`--jobs=N` 设为 CPU 核数。

## 编译命令模板

```bash
python -m nuitka --standalone \
    --jobs=8 \
    --windows-console-mode=disable \
    --show-progress --show-scons \
    --enable-plugin=pyside6 \
    --include-qt-plugins=multimedia \
    --include-package=... \
    --include-data-files="..." \
    --output-dir=dist \
    main.py
```

## 编译耗时预估

| 场景 | 耗时 |
|------|------|
| 首次编译（含 torch） | ~90 min |
| 增量（只改内部逻辑） | ~45 min |
| 增量（改了 import） | ~75 min |
| 仅 PySide6（无 torch） | ~10 min |

输出缓冲不刷新时，通过进程内存变化判断进度（PASS 1 从 ~200MB 涨到 ~2.6GB）。

## 长时间编译的进度反馈

Nuitka 编译 torch 等大型项目需要 1~1.5 小时，期间输出缓冲可能不刷新（输出文件 0 行），用户需要知道进度。

### 后台执行

编译始终用后台任务启动，避免阻塞当前会话：

```bash
# run_in_background=true，timeout 设足够大（600000ms=10min，实际会更长）
```

系统会在任务完成时自动发送通知，无需轮询。

### 定时检查进度

对长时间编译，用 CronCreate 设置定时检查（每 15 分钟），自动报告当前阶段：

```
CronCreate cron="7-57/15 * * * *" recurring=true
```

定时任务逻辑：
1. 用 `TaskOutput` 检查后台任务是否完成
2. 未完成 → 读取输出文件的最后几行，判断当前阶段（PASS 1 / C 编译 / 链接）并报告
3. 已完成 → 报告结果，用 `CronDelete` 删除定时任务

### 判断编译阶段的技巧

| 输出特征 | 当前阶段 | 剩余时间 |
|---------|---------|---------|
| `PASS 1: Optimizing module 'xxx', NNN more modules to go` | Python→C 翻译 | ~60 min |
| `Nuitka: Generating source code for C backend compiler` | C 代码生成 | ~5 min |
| `<clcache> /Fomodule.xxx.obj /c module.xxx.c` | C 编译（--jobs 生效） | ~25 min |
| `Backend C linking with NNN files` | 链接 | ~3 min |
| 输出文件 0 行但进程内存持续增长 | PASS 1 初期（输出缓冲） | ~50 min |

### 蜂鸣监控（推荐）

对于 Nuitka 编译这种长时间高 CPU 任务，最轻量的反馈方式是**监控 CPU 占用**——编译结束后 CPU 会从满载骤降。用 `scripts/monitor_cpu.py` 每分钟检查一次，CPU 低于阈值时蜂鸣提醒：

```bash
# 在编译机器上另开一个终端运行
python .claude/skills/nuitka-pack/scripts/monitor_cpu.py --threshold 50 --interval 60
```

相比 cc-connect 等远程方案，本地蜂鸣**零网络开销、零额外进程占用**，不影响编译性能。

### 完成通知

编译完成后，编译工具的结果摘要中会包含 exit code 和产物路径。如果用户有 cc-connect 等远程通道，可以告知用户随时通过远程通道主动查询状态，但由于 cc-connect 是单向的（用户→Agent），无法从 Agent 主动推送消息到微信。

## 编译后验证

- [ ] exe 文件存在且大小合理
- [ ] 所有资源文件在 exe 同级目录
- [ ] 运行测试核心功能
- [ ] 日志文件生成在预期位置
- [ ] 无控制台窗口弹出

## 常见问题速查

| 问题 | 处理 |
|------|------|
| `No QtMultimedia backends found` | 加 `--include-qt-plugins=multimedia` |
| 编译失败"拒绝访问" | kill 旧 exe 进程后重试 |
| 路径找不到资源文件 | 检查 `__file__` → `sys.executable` fallback |
| QMediaPlayer 播放异常 | 确认 `--include-qt-plugins=multimedia` 已加 |
| 增量编译速度没提升 | 检查是否改了 import 导致全量重分析 |

## 备份策略

编译成功后备份整个 dist 目录，方便后续增量编译或回退：
```bash
cp -r dist dist_backup
```
