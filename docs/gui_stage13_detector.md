# Stage 13｜探测器材料应用潜力评价（材料级）

本版本保留原工程树Stage 13入口，并将原器件演示指标表改成可追溯的六指标材料评价。详细计算和验收原则见[`lattice_substrate_matching_development.md`](lattice_substrate_matching_development.md)。

## 页面字段

主表直接展示六项指标及综合评价，各数值附中文状态。按用户2026-11-04最终确认，带隙项采用**端元带隙范围覆盖目标能量**：`min(EgA, EgB) ≤ 1.239841984 / λ(μm) ≤ max(EgA, EgB)`。覆盖即优先，未覆盖为次优，端元数据缺失为待补充；零带隙端元可作为有效边界。不要求直接合金带隙、两个合金构型或另设目标带隙区间。

主表带隙列显示端元范围、目标光子能量和覆盖状态；详情保留端元A/B数值与公式。用户修改目标波长或选择波段后立即重评，导出CSV使用当前波长。GUI执行几何命令时传入 `--target-wavelength-um`，CLI未传此选项时读取 `detector_context.target_wavelength_um`。范围覆盖是配对筛选条件，不插值生成合金带隙。

页面还展示：

- 晶格常数匹配（端元A/B的最大对称长度失配，%，须有可信晶轴/位点映射）；
- 声子（最低有效网格频率，THz，须结合QC）；
- 混合焓（meV/atom，读取Stage 9的有效计算）；
- 凸包上能（meV/atom，读取Stage 11的有效计算；从eV/atom×1000）；
- 前三推荐衬底及薄膜面内主应变（每个衬底单独一行，前三项分三行显示，表格行高随内容自动调整；单个所选代表SQS在各衬底下的两个有符号主应变，%，正值拉伸、负值压缩）；
- 候选等级（六维材料证据，不给器件级性能结论）。

“评价条件”页列出六项优先及复核条件。原 Stage 12 等级和模型来源仍可通过 Stage 12 查看；此页不计算器件性能。

## 两种使用模式

1. **已有Stage 12数据**：打开工程树Stage 13，读取`12_recommend/recommendations.csv`。页面合并同一`pair_index`+实际组分的构型，不据单条推荐ID断言双构型通过。没有几何文件时，几何指标为“—/待补充”；不自动给出零。
2. **真实几何评价**：按下面的结构清单准备`13_geometry/input/`和`13_geometry/config.json`，点击“计算几何指标”。GUI会同时传入当前Stage 12推荐CSV；程序按pair index、实际组分和结构ID将已有声子、混合焓及完整凸包结果绑定到Stage 13 SQS结构SHA，再从真实POSCAR/CIF生成几何结果和评价报告。端元范围评估可在缺少直接合金带隙时进行；直接合金带隙仍单独留空。GUI通过项目任务运行器调用所选的本地/WSL后端。

“加载内置演示数据”仅演示带隙显示，未提供任何虚构声子、混合焓、凸包或衬底结果。

## 输入清单：参照离线示例填写

当前仓库未包含可直接复制的完整示例输入包。必须准备自己的候选、结构、性质及衬底清单；本说明中的字段示例是格式说明，不是材料数据。

- `candidates.csv`：每个`candidate_id+实际组分+reference_set_id`一行，指定`pair_id`、`expected_structure_ids`（例如`real_s101;real_s202`）和允许替换的`replaceable_a/replaceable_b`；**`stage12_pair_index`用于与推荐表按pair_index+实际x精确关联，禁止按CSV行号关联**。
- `endmembers.csv`：同一参考集的端元A/B，结构路径、SHA256、方法、弛豫及QC状态。两端方法不同则待核验。
- `alloy_structures.csv`：明确构型标签/seed、实际组分、结构ID、参考集、SHA、QC；默认仅seed101计算衬底，不自动回退seed202。
- `properties.csv`：导入已有声子、混合焓、凸包结果，按`candidate_id+structure_id+structure_sha256`关联，覆盖清单指定的实际构型。统一状态/质检字段为`status=success,qc_status=pass`。`energy_above_hull_eV_per_atom`是**eV/atom**，程序转换为**meV/atom**。兼容读取的直接合金带隙仅作可选原始信息，缺失不影响本轮带隙判据；不启动合金带隙计算。
- 端元 `gap_a_eV/gap_b_eV` 从身份匹配的 Stage12 推荐表取得；CLI也支持在 `candidates.csv` 明确填写两值。来源冲突时待核验。端元数据与当前输入波长决定带隙项，无需 `gap_target_eV`。
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
  --recommendations 12_recommend/recommendations.csv \
  --target-wavelength-um 2.0
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
- `substrate_top_matches.csv`：最多三个不同衬底方案（旧配置即使设置为5也只输出前三项），不拼接不同方案的面积与应变；GUI衬底列列出前三衬底及各自两个有符号面内主应变。
- `structure_matches.csv`：各衬底四类代表匹配及唯一`match_id`。
- `match_details.jsonl.gz`：真实二维向量、整数变换、两个有符号主应变、SHA及搜索配置。
- `summary.json`：输入配置指纹与运行失败明细。
- `report.md`：第2节六维原样评价表及每候选结论。

## 分级与科学边界

主表末列是六项证据的**综合评价**，由 GUI 与 CLI 共用 `material_assessment.py` 的汇总规则。只有六项有效证据均达优先条件才为“优先进一步验证”；显著虚频、高混合焓或高凸包上能给出“降低优先级”，同时另列缺失项；其余证据不完整为“待补充”，中间区间为“备选/需复核”。几何结果好不会抵消已有稳定性风险。

默认阈值：晶格最大长度失配≤3%且角度检查通过为优先，3%–5%备选，>5%较大失配风险；声子最低频率≥−0.1 THz且QC通过；混合焓≤25/25–50/>50 meV/atom分别为优先/备选/高风险；凸包上能≤25/25–100/>100 meV/atom分别为优先/备选/高风险。实际判定读取工程配置。缺失、未收敛、采样不足或明确不完整的竞争集不能变成通过。

主表八列为：候选材料、端元带隙范围、晶格常数匹配、声子谱、混合焓、凸包上能、推荐衬底及主应变、综合评价。几何列读取 `candidate_evaluation.csv` 和同目录 `substrate_top_matches.csv`；衬底设置保持原有规则。所有候选都保留，不因条件未满足而隐藏。

导出CSV包含端元上下界、目标波长/能量、`band_match`、`gap_target_status` 和明确的 `gap_rule=endpoint_range_covers_photon_energy`。`candidate_assessment.csv` 的 `candidate_grade` 保留端元范围优先级语义，`material_grade` 为六项综合评价；几何主表的 `candidate_grade` 表示综合分级。兼容保留的合金带隙字段不参与当前判定。

几何搜索分别枚举薄膜原弛豫晶格和衬底常规晶格的对称不等价晶面；使用 pymatgen 的 Zur–McGill ZSL 搜索二维整数超晶格，不要求两侧晶面相同或原始晶轴直接对齐。默认两侧指数绝对值不超过 1、面积上限 800 Å²、长度相对容差 3%、角度相对容差 1%（不是 1°）。衬底固定，两个有符号面内主工程应变均由薄膜承担。每个组合按最大绝对主应变最小选解，同应变优先小面积；再保留前三种不同衬底。匹配记录保存应变约定和晶面枚举方式，算法标记为 `ssscreen_geometry_v2_distinct_planes`。当前不计算双方共同松弛或弹性应变能。

这里只计算几何/带隙/既有能量与声子证据，不计算器件响应率、暗电流、噪声、D*、器件上升时间或外延界面能；不会据此声称材料已经实现器件性能或成功外延。

## 当前实现限制（应在科研使用前补齐）

1. 端元的可信晶轴/位点映射第一版支持**等原子计量晶胞的右手有符号晶轴置换**和指定可替换位点；不同原胞/常规胞或非等价超胞若不能确立映射，返回“待核验”，不强行比较。正式应用需补充经验证的变胞/超胞位点映射适配层。
2. 并行和断点缓存没有启动，暂固定单进程；修改输入/参数重算，不混用旧缓存。
3. Python源包使用官方`pymatgen.analysis.interfaces.zsl.ZSLGenerator`接口搜索。安装版本可能引入API差异，请在WSL实际安装版本执行离线解析测试和微型结构搜索后才用于真实科研。
4. Stage 12推荐CSV不含结构SHA，不能单独证明结构身份。适配器只有在pair index、实际组分和structure ID与Stage 13清单一致时，才利用`alloy_structures.csv`中的结构SHA导入成功性质；缺少或不匹配的记录仍标为待补充。端元带隙区间覆盖是筛选估计，可能受合金带隙弯曲（bowing）、相变及非单调变化影响；需要高精度合金计算验证。
5. 默认波长2 μm可由用户更改；CLI若未设置波长则待补充。旧 `gap_target_eV` 保留配置兼容，但不参与当前端元范围判据。证据“完整”表示所需六项已有结果，不代表结果有利、材料稳定或器件性能已验证。
