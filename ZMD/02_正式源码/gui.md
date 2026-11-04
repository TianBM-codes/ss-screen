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
| [`detector_page.py`](../../src/ssscreen/gui/detector_page.py) | Stage 13固溶体候选评价：执行几何匹配CLI、显示端元晶格失配及前三衬底的薄膜面内主应变、读取材料证据和Markdown报告；[使用说明](../../docs/gui_stage13_detector.md) |
| [`appearance.py`](../../src/ssscreen/gui/appearance.py) | 字号范围、点数字体样式和随字号变化的控件/表格布局 |
| [`project_file.py`](../../src/ssscreen/gui/project_file.py) | `.ssproject` ZIP64 项目容器、SHA-256 清单、安全解包与原子保存 |
| [`visualization.py`](../../src/ssscreen/gui/visualization.py) | MatterViz 晶体、声子图表和竞争相/凸包结果页 |
| [`matterviz_dist/`](../../src/ssscreen/gui/matterviz_dist/) | 随 Python wheel 分发的 MatterViz 0.7.0 静态前端与第三方许可证 |

## 关键边界

- `ss-screen` 仍映射到 [`src/ssscreen/cli/app.py`](../../src/ssscreen/cli/app.py)，是科研行为的权威入口。
- `ss-screen-gui` 只启动 GUI；运行任务时调用真实 CLI。Windows 后端使用当前解释器，WSL 后端通过
  `wsl.exe bash -lc` 进入工程目录、激活 `.venv` 或 `.venv-mlp` 后执行 `ss-screen ...`。
- 右侧运行后端默认使用 WSL 自动选择：前中段和 SQS 使用 `.venv`，MACE relax、phonon 与
  phase-diagram 使用 `.venv-mlp`；误选 `.venv-mlp` 跑 SQS 时会自动回退到 `.venv`。
- `src/ssscreen/gui/app.py` 可被 PyCharm 直接运行；启动时会从脚本目录向上识别仓库根目录，
  避免 WSL 后端误在 `src/ssscreen/gui` 子目录中查找 `.venv`。
- GUI 发往 WSL 的相对路径会统一把 Windows 反斜杠转换为 `/`；组成筛选页只自动加入真实存在的
  `01_dataset/*.df`，避免不存在的 `mp.df/wbm.df` 被带入命令。
- Stage 13新增输入包驱动的端元晶格匹配和单代表SQS衬底主应变评价；主表最后一列显示前三种不同衬底及各自两个有符号薄膜面内主应变。已有材料性质只读，不显示或导出响应率、暗电流、NEP、D*、上升时间等器件性能字段。底层`src/ssscreen/detector.py`仍提供材料预览数据处理。
- GUI 专用页面会把旧的 `src/ssscreen/gui/...` 阶段路径归一化为工程根目录相对路径；例如
  `src/ssscreen/gui/03_condensed/local` 会显示并执行为 `03_condensed/local`。
- 数据源页支持 `dataset structures`，可把本地 POSCAR/CIF 文件夹导入为 Stage 1 DataFrame；结构归档页的
  “添加文件夹”会递归扫描子目录中的 POSCAR/CONTCAR。
- GUI 可以保存界面流程和用户输入体验，但不得引入 preview-only/mock CLI 替代正式命令。
- API key 等秘密只允许进入子进程环境，不写入命令、日志或项目文件。
- 2026-09-14 起，GUI 默认演示链路指向 `data/CaS_CaSe_CaTe_PBE_relaxed_CONTCAR`、
  `data/mace-mpa-0-medium.model`、`work/real-pbe-mace-20260914-run4/05_gap/vasp_by_task_id`
  和 MP API 后端；前中段默认输出目录为 `01_dataset` 至 `12_recommend`。
- Stage 11 API 后端可读取右侧 Properties 注入的 `MP_API_KEY` 环境变量，不需要在 GUI 控制台交互输入。
- 当前 GUI 为整套演示流程隐藏后段拆分调试命令：Stage 10 只显示 `phonon-run`，Stage 11 只显示
  `phase-diagram`；拆分命令仍保留在 CLI 中。
- Stage 12 使用专用结果报告页，内嵌 Markdown 报告预览，并合并推荐、pair、SQS、混合焓、声子和
  凸包关键字段展示候选材料的具体数值与结构文件路径。
- 工具栏显示运行状态和不确定进度条，用于提示当前后端任务仍在计算。
- Stage 08/10/11 分别提供晶体、声子和竞争相可视化；晶体视图由内嵌 Qt WebEngine 加载随包分发的
  MatterViz 前端，声子页显示状态/最低频率/band/DOS，竞争相页显示表格与三元组成图。
- MACE GUI 预设默认使用 `cpu`，仍允许用户手动输入 CUDA 设备；CLI 参数显示为“中文名称（英文参数）”。
- 工具栏可保存/打开 `.ssproject` 单文件；容器保存 Stage 01--13、用户命令配置和校验清单，不保存 MP API Key。
- SSH 目前仅实现只读验证按钮，检查认证、远端 Python、`ss-screen` 和可选工程目录，不提交远端计算。

## 验证建议

- 核心 CLI 回归测试仍以 [`tests/test_cli.py`](../../tests/test_cli.py) 为准。
- GUI 冒烟测试应在安装 `[gui]` extra 后验证 `ss-screen-gui --help` 或 launcher import。
- Windows/WSL 联动可用 headless Qt 实例化 `MainWindow` 后触发一次 `ss-screen --version` 或
  `dataset structures` QProcess smoke，确认日志和输出文件。
- 在无显示服务器的 Linux CI 中，GUI 视觉/交互测试应显式跳过或使用合适的 headless Qt 配置。

## 最近同步

- 2026-11-04：用户最终要求仅使用端元范围覆盖目标波长能量；主表带隙列显示范围、目标能量和覆盖状态，移除双构型缺项展示，波长改动立即重评并传入CLI。真实工程2 μm覆盖、六项证据完整、综合仍降低优先级；停止合金带隙准备，原衬底及科学数值不变。
- 2026-11-04：Stage 13 主表改为材料、合金带隙、晶格匹配、声子谱、混合焓、凸包上能、前三衬底、综合评价八列；增加“评价条件”页，详情保留端元预估。风险与缺失并列，真实候选显示降低优先级/部分缺失；三次刷新、CSV导出、演示不可评级及实际窗口验证见最新日志。
- 2026-11-04：本机 Stage 13 已接入十种指定衬底的真实结果：晶格失配 7.3693%，前三 Ge/MgO/GaP；末列改名“带隙范围优先级”，详情展示稳定性数值与独立综合证据状态，修复重复刷新后的详情空白。Qt 核验、可见截图及 WSL 检查通过；外部最新工程包为 `_Stage13.ssproject`，详见日志。
- 2026-11-04：只读诊断本机 Stage 13 空值，真实 Qt 页面核验通过：当前 PBE 工程没有几何输入/输出和衬底库，两项几何列为空；已有声子、混合焓、凸包正常读入，但九列主表不展示数值。末列“优先”仅按端元带隙范围判定，Stage 12 仍为低优先级。未修改程序或重跑科学计算，详见项目日志。
- 2026-11-04：Stage 12 推荐表的 17 个表头、分类统计、状态/来源、风险和下一步建议中文化；原始 CSV、数值与结构标识保留。真实 Qt 页面核验及可见窗口截图通过，已重新打开中文综合推荐页，详见最新项目日志。
- 2026-11-04：按用户要求实际打开最新综合推荐窗口；截图确认 1 条 low-priority/L5 与混合焓、虚频、凸包数值，窗口可见且 WSL 版本检查退出码 0。旧窗口保留，未重跑材料计算；详见最新项目日志。
- 2026-11-04：同一本机工程新增竞争相/凸包和综合推荐，保存 `_API.ssproject`（248 项）；原窗口可刷新读取，新启动脚本默认进入综合推荐页。GUI 固定目录的竞争结构副本与权威输出逐文件 SHA 一致；参数已存但 API key 未落盘。未改 GUI 源码或重启现有窗口。
- 2026-11-03：本机 PBE 工程新增真实弛豫、混合焓和声子产物，另存 `_MLP.ssproject`（133 项产物）；本地启动设置改为 WSL 自动选择并保存当前模型和收敛参数。原窗口保持打开，可刷新声子结果页；当前实例未热更新设置，未改 GUI 源码。
- 2026-11-03：本机新建 `.venv-gui` 并打开实际 PBE 结果工程；结构组表 1 行、3 个材料，GUI→WSL `.venv` 版本检查退出码 0。运行目录 `ss-screen-local-results/CaS_CaSe_CaTe_PBE_20261103` 中保存前端截图、启动脚本及 `.ssproject`；本地 Python 3.11 editable 路径通过 ASCII 转义 `.pth` 兼容中文目录。
- 2026-11-03：PyCharm重启GUI复核Stage 13：CaSe/CaTe端元带隙0.7877/0.0064 eV，2.0 μm目标能量0.61992 eV，范围覆盖；候选综合等级仍“待补充”。页面几何表路径仍是默认路径，真实几何CSV尚未在本次界面读取，详见项目日志。
- 2026-11-03：Stage 13“候选等级（带隙）”按端元带隙范围设置为“优先/次优”；范围未覆盖及带隙缺失的Stage 12候选仍显示在表格，不要求直接合金带隙。
- 2026-11-03：Stage 13主表按用户指定精简为材料、端元带隙、目标波长/能量、带隙候选判断、晶格失配、前三衬底应变和候选等级优先；几何数据读取几何评价CSV及同目录衬底匹配CSV。
- 2026-11-03：Stage 13前三衬底启用多行显示，每个衬底一行；表格行高按内容自动调整，避免应变结果挤在一行。
- 2026-11-03：Stage 13将端元A/B带隙分列显示；目标波长换算为光子能量后，按端元带隙闭区间判断覆盖情况，不插值生成合金带隙。直接合金带隙仍单独展示，详见Stage 13使用说明。
- 2026-11-03：重启PyCharm GUI后从Stage 13实际运行WSL CLI，命令包含`--recommendations`，exit code 0；表格验证声子/混合焓/凸包和前三衬底回填，候选等级显示“待补充”。
- 2026-11-03：Stage 13 GUI计算同时传入Stage 12推荐表；CLI按pair index、实际组分和structure ID关联已有性质，并由SQS清单SHA校验身份；端元带隙不作为合金带隙。
- 2026-11-03：PyCharm启动的Windows GUI通过任务运行器调用WSL `geometry-evaluate`成功，exit code 0；Stage 13真实CaSe–CaTe候选已加载端元晶格匹配和前三衬底主应变，输出位于忽略目录`work/stage13_real_CaSe_CaTe_2026-11-03/output/`。
- 2026-11-03：PyCharm启动Windows GUI并打开真实CaSe–CaTe Stage 13；页面显示Stage 12已有性质，几何评价因缺少Stage 13输入包未提交计算，前三衬底列为空。
- 2026-11-03：合并PR #7的Stage 13几何评价，并由主窗口任务运行器调用`geometry-evaluate`，展示材料证据及几何结果；运行验证待执行。

- 2026-10-15：按后续反馈，“视图”下拉入口改为与“新建工程”同一工具栏，不再单独占顶层菜单栏；字号子菜单保留。
- 2026-10-15：字号入口移到“视图 → 界面字号”菜单，9--18 pt单选并提供恢复默认；移除标题条上的字号
  输入框和恢复图标，保留历史已有的`SS-SCREEN`产品标识。字号记忆与布局联动继续生效。
- 2026-10-14：顶部新增字号设置（9--18 pt，默认10 pt）及恢复按钮，Qt 设置自动记忆；工具栏支持溢出菜单，
  属性区与工作区可滚动，表格/预览随字号调整，MatterViz 同步缩放。新增可选 Qt 字体回归测试。
- 2026-09-28：修正结果可视化布局；Stage 11 竞争相表格显示条目数量、中文角色/目标值和格式化凸包距离，
  列宽填满可视区域；Stage 10/11 的 MatterViz 改为完整标签页并使用扩展尺寸策略。
- 2026-09-27：新增 `.ssproject` 单文件项目、MatterViz 晶体视图、声子与竞争相可视化、CPU 默认设备、
  CLI 参数中文标签和 SSH 只读连通性探测；MatterViz 高级控制面板因上游 `svelte-widgets` 兼容问题暂时关闭。
- 2026-09-18：声子一步式运行的 `--max-input-force` 默认值由 `0.01` 调整为 `0.02 eV/Angstrom`，
  并将该页面的 `--include-endmembers` 设为默认勾选。
- 2026-09-17：简化 GUI 后段流程显示，隐藏 Stage 10/11 拆分命令；`--include-endmembers` 默认勾选并只
  显示正向选项；新增 Stage 12 Markdown 报告/候选证据表页和运行状态进度条。
- 2026-09-16：GUI 路径显示/解析新增旧子目录残留归一化；结构匹配页的归档默认和旧路径追加场景均会
  落到 `03_condensed/local`，左侧工程树 Stage 03/04 也会统计 `03_condensed/local`。
- 2026-09-16：运行后端新增 WSL 自动选择，避免 SQS 用 `.venv-mlp` 读取 NumPy 2 生成的
  `local_structures.df` 时触发 `numpy._core.numeric` pickle 兼容错误。
- 2026-09-12：修复 PyCharm 直接运行 `app.py` 时默认工程落在 `src/ssscreen/gui` 的问题；GUI 现在会
  自动识别仓库根目录，WSL 后端留空工程路径时会进入仓库根再激活 `.venv` 或 `.venv-mlp`。
- 2026-09-12：修复组成筛选页残留旧子目录 DataFrame 路径、默认带入缺失 `mp.df/wbm.df` 和 WSL
  相对路径反斜杠问题；日志中 WSL localhost/NAT 启动警告会压缩成英文提示。
- 2026-09-14：默认参数切换为 CaS/CaSe/CaTe 真实 VASP + MACE + MP API 演示链路；CLI 的 MP API Key
  读取改为优先使用 GUI 注入的 `MP_API_KEY` 环境变量，避免 Stage 11 在 GUI 子进程中等待交互提示。
- 2026-09-11：GUI 右侧连接设置新增 Windows/WSL `.venv`/WSL `.venv-mlp` 后端选择；数据源页新增
  本地 POSCAR 结构导入；结构归档页递归扫描子目录 POSCAR；已用 headless Qt 验证 GUI 调 WSL CLI 成功。

- 2026-11-01：新增Stage 13“探测器性能评估”GUI页面（`detector_page.py`）与纯Python指标逻辑（`src/ssscreen/detector.py`）。从Stage 12读取推荐表，展示名义截止波长、目标波长适配、原稳定性证据，并按需读取器件实测字段；虚构演示数据明确标注。详见`docs/gui_stage13_detector.md`，回归测试`tests/test_detector.py`。
