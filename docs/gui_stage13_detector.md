# Stage 13｜探测器材料应用潜力评价（材料级）

本版本保留原工程树Stage 13入口，并将原器件演示指标表改成可追溯的六指标材料评价。详细计算和验收原则见[`lattice_substrate_matching_development.md`](lattice_substrate_matching_development.md)。

## 页面字段

保留候选ID、端元A/B、组分x、带隙、带隙等效波长（不再称为实测截止波长）和目标波段；新增：

- 晶格常数匹配（端元A/B的最大对称长度失配，%，须有可信晶轴/位点映射）；
- 声子（最低有效网格频率，THz，须结合QC）；
- 混合焓（meV/atom，读取Stage 9的有效计算）；
- 凸包上能（meV/atom，读取Stage 11的有效计算；从eV/atom×1000）；
- 衬底主应变（单个所选代表SQS的最大绝对面内工程主应变，%）；
- 候选等级（六维材料证据，不给器件级性能结论）。

删除旧稳定性推荐、响应率、暗电流、NEP、D*、上升时间六列。原Stage 12等级和模型来源不被删除，仍可通过Stage 12查看。

## 两种使用模式

1. **已有Stage 12数据**：打开工程树Stage 13，读取`12_recommend/recommendations.csv`。页面合并同一`pair_index`+实际组分的构型，不据单条推荐ID断言双构型通过。没有几何文件时，几何指标为“—/待补充”；不自动给出零。
2. **真实几何评价**：按下面的结构清单填好`13_detector/geometry/input/`，将示例`config.json`复制到`13_detector/geometry/config.json`并修改真实条件，点击“计算几何指标”。本操作从真实POSCAR/CIF结构离线生成评价CSV和可追溯明细；GUI为避免阻塞使用子进程运行。若GUI的Python与WSL工程环境不同，请先在WSL CLI运行，再点击“读取工程结果”。

“加载内置演示数据”仅演示带隙显示，未提供任何虚构声子、混合焓、凸包或衬底结果。

## 输入清单：参照离线示例填写

模板位置：`tests/data/stage13_geometry/input/`（**文件内全部材料、性能和结构为人工测试数据，禁止当作实际科研结论**）。

- `candidates.csv`：每个`candidate_id+实际组分+reference_set_id`一行，指定`pair_id`、`expected_structure_ids`（例如`real_s101;real_s202`）和允许替换的`replaceable_a/replaceable_b`；**`stage12_pair_index`用于与推荐表按pair_index+实际x精确关联，禁止按CSV行号关联**。
- `endmembers.csv`：同一参考集的端元A/B，结构路径、SHA256、方法、弛豫及QC状态。两端方法不同则待核验。
- `alloy_structures.csv`：明确构型标签/seed、实际组分、结构ID、参考集、SHA、QC；默认仅seed101计算衬底，不自动回退seed202。
- `properties.csv`：只导入已经取得的两构型**真实合金**带隙、声子、混合焓、凸包结果，按`candidate_id+structure_id+structure_sha256`关联。统一状态/质检字段为`status=success,qc_status=pass`；如缺失，保留空表或缺项。`band_gap_eV`是合金构型计算结果，不是端元插值。`energy_above_hull_eV_per_atom`是**eV/atom**，程序转换为**meV/atom**。
- `substrates.json`：本地衬底结构路径、晶相和SHA，不在搜索期间自动联网。

实际数据文件相对路径均相对于各自输入清单文件所在目录。可用`sha256sum`核对结构SHA。示例中Na/K/Cl和Mg/O均为*人工结构*，不是实际可外延材料推荐。

## 建议运行方法（WSL Ubuntu）

在`ss-screen-latest`工程目录内：

```bash
source .venv/bin/activate
python -m pip install -e '.[gui]'
python -m pytest tests/test_detector.py tests/test_geometry_core.py tests/test_geometry_pipeline.py -q

mkdir -p 13_detector/geometry
cp -r tests/data/stage13_geometry/input 13_detector/geometry/input
cp tests/data/stage13_geometry/config.json 13_detector/geometry/config.json

ss-screen geometry-evaluate \
  --input 13_detector/geometry/input \
  --config 13_detector/geometry/config.json \
  --output 13_detector/geometry/output
```

首次执行请务必替换所有示例材料及模拟性质数据。命令也可使用：

```bash
python -m ssscreen.geometry_cli \
  --input 13_detector/geometry/input \
  --config 13_detector/geometry/config.json \
  --output 13_detector/geometry/output
```

没有本地`pymatgen`或真实结构时，相应候选将标为计算失败/待补充，**不得解释为已做完衬底搜索**。

## 输出

- `candidate_evaluation.csv`：每体系＋实际组分主表，包含六项证据、分级、来源状态。
- `lattice_matches.csv`：映射/晶格失配/角差和核验状态。
- `substrate_top_matches.csv`：前N个不同衬底方案，不拼接不同方案的面积与应变。
- `structure_matches.csv`：各衬底四类代表匹配及唯一`match_id`。
- `match_details.jsonl.gz`：真实二维向量、整数变换、两个有符号主应变、SHA及搜索配置。
- `summary.json`：输入配置指纹与运行失败明细。
- `report.md`：第2节六维原样评价表及每候选结论。

## 分级与科学边界

目标带隙范围由`gap_target_eV`显式配置。只要缺少关键有效数据或目标未设定，“候选等级”就不能自动上升为优先。声子阈值−0.1THz、混合焓25/50meV/atom、凸包25/100meV/atom、晶格3/5%、衬底1/3%，均按任务书作初始可配置门槛，不是普适材料定律。

这里只计算几何/带隙/既有能量与声子证据，不计算器件响应率、暗电流、噪声、D*、器件上升时间或外延界面能；不会据此声称材料已经实现器件性能或成功外延。

## 当前实现限制（应在科研使用前补齐）

1. 端元的可信晶轴/位点映射第一版支持**等原子计量晶胞的右手有符号晶轴置换**和指定可替换位点；不同原胞/常规胞或非等价超胞若不能确立映射，返回“待核验”，不强行比较。正式应用需补充经验证的变胞/超胞位点映射适配层。
2. 并行和断点缓存没有启动，暂固定单进程；修改输入/参数重算，不混用旧缓存。
3. Python源包使用官方`pymatgen.analysis.interfaces.zsl.ZSLGenerator`接口搜索。安装版本可能引入API差异，请在WSL实际安装版本执行离线解析测试和微型结构搜索后才用于真实科研。
4. 现有推荐CSV通常不携带完整合金结构SHA/QC，因此它只能支持展示，不能替代本功能的`alloy_structures.csv`和`properties.csv`中的身份/有效性证据。两类数据需按实际工程记录显式关联。
5. 默认目标波长仅作为界面展示例子，不等于配置的光谱目标区间；如未设置`gap_target_eV`，综合等级将保持“待补充”。
