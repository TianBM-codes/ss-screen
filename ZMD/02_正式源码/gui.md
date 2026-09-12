# GUI 导航

真实目录：[`src/ssscreen/gui/`](../../src/ssscreen/gui/)

设计说明：[`docs/gui_integration_notes.md`](../../docs/gui_integration_notes.md)

桌面 GUI 是可选 PySide6 前端。它负责呈现工程树、阶段流程、参数输入、任务日志和结果文件浏览；科学计算仍由真实 Click CLI 执行。

## 文件清单

| 文件 | 职责 |
|---|---|
| [`__init__.py`](../../src/ssscreen/gui/__init__.py) | 延迟导出 `run_gui`，避免未安装 PySide6 时影响核心包导入 |
| [`app.py`](../../src/ssscreen/gui/app.py) | PySide6 主窗口、工程树、专用阶段页面、命令日志和 `QProcess` 子进程执行；支持 IDE 直接按脚本启动、Windows GUI 调 WSL 后端、递归导入本地 POSCAR 文件夹 |
| [`launcher.py`](../../src/ssscreen/gui/launcher.py) | `ss-screen-gui` 控制台入口 |
| [`metadata.py`](../../src/ssscreen/gui/metadata.py) | 阶段标题、命令展示顺序和工程内默认路径预设 |

## 关键边界

- `ss-screen` 仍映射到 [`src/ssscreen/cli/app.py`](../../src/ssscreen/cli/app.py)，是科研行为的权威入口。
- `ss-screen-gui` 只启动 GUI；运行任务时调用真实 CLI。Windows 后端使用当前解释器，WSL 后端通过
  `wsl.exe bash -lc` 进入工程目录、激活 `.venv` 或 `.venv-mlp` 后执行 `ss-screen ...`。
- `src/ssscreen/gui/app.py` 可被 PyCharm 直接运行；此兼容入口只修正导入路径，不改变 GUI 调用 CLI 的行为。
- 数据源页支持 `dataset structures`，可把本地 POSCAR/CIF 文件夹导入为 Stage 1 DataFrame；结构归档页的
  “添加文件夹”会递归扫描子目录中的 POSCAR/CONTCAR。
- GUI 可以保存界面流程和用户输入体验，但不得引入 preview-only/mock CLI 替代正式命令。
- API key 等秘密只允许进入子进程环境，不写入命令、日志或项目文件。

## 验证建议

- 核心 CLI 回归测试仍以 [`tests/test_cli.py`](../../tests/test_cli.py) 为准。
- GUI 冒烟测试应在安装 `[gui]` extra 后验证 `ss-screen-gui --help` 或 launcher import。
- Windows/WSL 联动可用 headless Qt 实例化 `MainWindow` 后触发一次 `ss-screen --version` 或
  `dataset structures` QProcess smoke，确认日志和输出文件。
- 在无显示服务器的 Linux CI 中，GUI 视觉/交互测试应显式跳过或使用合适的 headless Qt 配置。

## 最近同步

- 2026-09-11：GUI 右侧连接设置新增 Windows/WSL `.venv`/WSL `.venv-mlp` 后端选择；数据源页新增
  本地 POSCAR 结构导入；结构归档页递归扫描子目录 POSCAR；已用 headless Qt 验证 GUI 调 WSL CLI 成功。
