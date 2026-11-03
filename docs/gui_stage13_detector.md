# Stage 13｜探测器材料应用潜力评价（材料级）

本版本保留原工程树Stage 13入口，并将原器件演示指标表改成可追溯的六指标材料评价。详细计算和验收原则见[`lattice_substrate_matching_development.md`](lattice_substrate_matching_development.md)。

## 页面字段

带隙按端元范围进行配对级预估：将界面目标波长换算为目标光子能量`E_target = 1.239841984 / λ(μm)`，检查它是否落在端元A、端元B带隙形成的闭区间内。页面分别显示端元A、端元B带隙、目标光子能量和范围评估；不插值生成某一组分的合金带隙。若已有直接合金计算结果，则单独显示“合金带隙（实算）”及其等效波长。范围覆盖仅表示目标能量位于端元带隙之间，是固溶体探测潜力的初筛估计，不代表实测或已验证的合金带隙。

页面还展示：

- 晶格常数匹配（端元A/B的最大对称长度失配，%，须有可信晶轴/位点映射）；
- 声子（最低有效网格频率，THz，须结合QC）；
- 混合焓（meV/atom，读取Stage 9的有效计算）；
- 凸包上能（meV/atom，读取Stage 11的有效计算；从eV/atom×1000）；
- 前三推荐衬底及薄膜面内主应变（每个衬底单独一行，前三项分三行显示，表格行高随内容自动调整；单个所选代表SQS在各衬底下的两个有符号主应变，%，正值拉伸、负值压缩）；
- 候选等级（六维材料证据，不给器件级性能结论）。

删除旧稳定性推荐、响应率、暗电流、NEP、D*、上升时间六列。原Stage 12等级和模型来源不被删除，仍可通过Stage 12查看。

## 两种使用模式

1. **已有Stage 12数据**：打开工程树Stage 13，读取`12_recommend/recommendations.csv`。页面合并同一`pair_index`+实际组分的构型，不据单条推荐ID断言双构型通过。没有几何文件时，几何指标为“—/待补充”；不自动给出零。
2. **真实几何评价**：按下面的结构清单准备`13_geometry/input/`和`13_geometry/config.json`，点击“计算几何指标”。GUI会同时传入当前Stage 12推荐CSV；程序按pair index、实际组分和结构ID将已有声子、混合焓及完整凸包结果绑定到Stage 13 SQS结构SHA，再从真实POSCAR/CIF生成几何结果和评价报告。端元范围评估可在缺少直接合金带隙时进行；直接合金带隙仍单独留空。GUI通过项目任务运行器调用所选的本地/WSL后端。

“加载内置演示数据”仅演示带隙显示，未提供任何虚构声子、混合焓、凸包或衬底结果。

## 输入清单：参照离线示例填写

当前仓库未包含可直接复制的完整示例输入包。必须准备自己的候选、结构、性质及衬底清单；本说明中的字段示例是格式说明，不是材料数据。

- `candidates.csv`：每个`candidate_id+实际组分+reference_set_id`一行，指定`pair_id`、`expected_structure_ids`（例如`real_s101;real_s202`）和允许替换的`replaceable_a/replaceable_b`；**`stage12_pair_index`用于与推荐表按pair_index+实际x精确关联，禁止按CSV行号关联**。
- `endmembers.csv`：同一参考集的端元A/B，结构路径、SHA256、方法、弛豫及QC状态。两端方法不同则待核验。
- `alloy_structures.csv`：明确构型标签/seed、实际组分、结构ID、参考集、SHA、QC；默认仅seed101计算衬底，不自动回退seed202。
- `properties.csv`：只导入已经取得的两构型**真实合金**带隙、声子、混合焓、凸包结果，按`candidate_id+structure_id+structure_sha256`关联。统一状态/质检字段为`status=success,qc_status=pass`；如缺失，保留空表或缺项。GUI还会从Stage 12推荐CSV导入身份匹配的已有声子、混合焓和完整凸包性质。`band_gap_eV`是合金构型直接计算结果；端元A/B带隙独立保留，并用于目标光子能量的区间覆盖初筛，不据此插值合金带隙。`energy_above_hull_eV_per_atom`是**eV/atom**，程序转换为**meV/atom**。
- `substrates.json`：本地衬底结构路径、晶相和SHA，不在搜索期间自动联网。匹配按每种衬底的最佳方案排序，默认展示前三种不同衬底；列表可包含Si、Ge、GaAs等，但每个条目都必须提供实际结构文件及来源。

实际数据文件相对路径均相对于各自输入清单文件所在目录。可用`sha256sum`核对结构SHA。示例中Na/K/Cl和Mg/O均为*人工结构*，不是实际可外延材料推荐。

## 建议运行方法（WSL Ubuntu）

在工程目录内，使用符合上一节清单格式的输入文件：

```bash
source .venv/bin/activate
python -m pip install -e '.[gui]'
python -m pytest tests/test_detector.py tests/test_geometry_core.py tests/test_geometry_pipeline.py -q

ss-screen geometry-evaluate \
  --input 13_geometry/input \
  --config 13_geometry/config.json \
  --output 13_geometry \
  --recommendations 12_recommend/recommendations.csv
```

首次执行请务必替换所有示例材料及模拟性质数据。命令也可使用：

```bash
python -m ssscreen.geometry_cli \
  --input 13_geometry/input \
  --config 13_geometry/config.json \
  --output 13_geometry
```

没有本地`pymatgen`或真实结构时，相应候选将标为计算失败/待补充，**不得解释为已做完衬底搜索**。

## 输出

- `candidate_evaluation.csv`：每体系＋实际组分主表，包含六项证据、分级、来源状态。
- `lattice_matches.csv`：映射/晶格失配/角差和核验状态。
- `substrate_top_matches.csv`：最多三个不同衬底方案（旧配置即使设置为5也只输出前三项），不拼接不同方案的面积与应变；GUI主表最后一列列出前三衬底及各自两个有符号面内主应变。
- `structure_matches.csv`：各衬底四类代表匹配及唯一`match_id`。
- `match_details.jsonl.gz`：真实二维向量、整数变换、两个有符号主应变、SHA及搜索配置。
- `summary.json`：输入配置指纹与运行失败明细。
- `report.md`：第2节六维原样评价表及每候选结论。

## 分级与科学边界

Stage 13的“候选等级（带隙）”依据端元带隙范围与目标光子能量判断：覆盖目标记为“优先”，未覆盖或端元带隙缺失记为“次优”。所有Stage 12候选都会保留在表格中，不因带隙条件未满足而隐藏。该规则不要求直接计算合金带隙；合金实算带隙仍可作为独立参考字段显示。该等级仅表示带隙范围初筛优先级，不代表材料稳定性或器件性能已验证。

主表精简为候选材料、端元A/B带隙、目标波长、目标能量、带隙候选判断、晶格失配、推荐衬底及薄膜面内主应变、候选等级优先。端元范围覆盖时“带隙候选判断”显示“满足带隙候选”，最后一列显示“优先”；其他候选保留并标记“次优”。几何列需读取Stage 13 `candidate_evaluation.csv` 和同目录的 `substrate_top_matches.csv` 才有真实值。

这里只计算几何/带隙/既有能量与声子证据，不计算器件响应率、暗电流、噪声、D*、器件上升时间或外延界面能；不会据此声称材料已经实现器件性能或成功外延。

## 当前实现限制（应在科研使用前补齐）

1. 端元的可信晶轴/位点映射第一版支持**等原子计量晶胞的右手有符号晶轴置换**和指定可替换位点；不同原胞/常规胞或非等价超胞若不能确立映射，返回“待核验”，不强行比较。正式应用需补充经验证的变胞/超胞位点映射适配层。
2. 并行和断点缓存没有启动，暂固定单进程；修改输入/参数重算，不混用旧缓存。
3. Python源包使用官方`pymatgen.analysis.interfaces.zsl.ZSLGenerator`接口搜索。安装版本可能引入API差异，请在WSL实际安装版本执行离线解析测试和微型结构搜索后才用于真实科研。
4. Stage 12推荐CSV不含结构SHA，不能单独证明结构身份。适配器只有在pair index、实际组分和structure ID与Stage 13清单一致时，才利用`alloy_structures.csv`中的结构SHA导入成功性质；缺少或不匹配的记录仍标为待补充。端元带隙区间覆盖是筛选估计，可能受合金带隙弯曲（bowing）、相变及非单调变化影响；需要高精度合金计算验证。
5. 默认目标波长仅作为界面展示例子，不等于配置的光谱目标区间；如未设置`gap_target_eV`，综合等级将保持“待补充”。
