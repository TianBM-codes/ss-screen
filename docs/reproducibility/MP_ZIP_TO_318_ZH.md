# 从原始 mp.zip 重现318个配对

本入口从 MP 原始数据库重新筛选、描述、分组和导出端元，再接收已完成的 mBJ
带隙结果，用**本次重新生成的分组**枚举配对。预期得到二元79对、三元239对，
共318个唯一配对、317个端元。历史分组只用于验收对照。

这需要 **mp.zip + mBJ计算结果 + 代码和依赖**。单独的 MP 数据库不包含本次
外部 mBJ 计算结果；用库内带隙替代 mBJ 值不能视为重现这318对。
之前约10.76 MiB的包仅够回放既有分组，不含 MP 原库。

## 交付文件

从 PR #8 对应提交获取代码，安装依赖；数据单独交付为
`ss-screen-mp-to-318-data-20261104.zip`，解压到仓库外。布局：

```text
mp.zip                                      # 原始MP ZIP，340465876字节
mp-2944-mbj-results-20261104/                 # 原样保留的冻结mBJ结果和来源
mp-offline-dependencies-20261103/             # 离线库读取器及补充wheel
mp_descriptors_4944_verified_20261104.zip     # 可选描述缓存；使用时必须显式指定
README_MP_TO_318_ZH.md
DELIVERY.json                               # 代码提交、文件SHA与验证范围
```

PR尚未合并时，不能直接把默认分支当作交付版本。可先获取PR提交，再检出
`DELIVERY.json` 中的 `code_revision`：

```bash
git clone https://github.com/TianBM-codes/ss-screen.git
cd ss-screen
git fetch origin pull/8/head
git checkout <DELIVERY.json里的code_revision>
```

原始 `mp.zip` SHA256：
`1bd05b742cf797ce01b8630c23c0c5bcf7949cf72a148f37510ffe96e88ad503`。
其中 `mp/default.db` 为2220736512字节，SHA256：
`d54bca48d1e00bdfd8db7c1e5a7b5844ccb755b948335930f09fe85444a7ebb8`。

这是固定快照的复现实验入口，不承诺任意另一个 `mp.zip` 都产生318对。
输入SHA、候选身份或最终配对证据不符会停止并保留失败阶段。

## 建立环境

在 Linux/WSL x86_64、Python 3.11 项目环境中运行；无需 GUI、MP API密钥、
VASP、MACE或声子环境。已有环境只需激活；以下创建命令用于新 checkout：

```bash
cd /path/to/ss-screen
python3.11 -m venv .venv
source .venv/bin/activate
ASSETS=/path/to/extracted-full-data
python -m pip install \
  -c requirements/reproduction-20261104/screen-wsl-py311.constraints.txt \
  -e '.[condense]'
python -m pip install \
  -c requirements/reproduction-20261104/screen-wsl-py311.constraints.txt \
  "$ASSETS/mp-offline-dependencies-20261103/wheels/mp_offline-0.1.0-py2.py3-none-any.whl"
python -m pip check
ss-screen mp-reproduce --help
```

约束文件是已运行环境的版本记录，不是完整离线安装包；安装其余科学依赖需要
软件包下载渠道。勿将 NumPy 1.x 的 MACE 环境与本筛选环境混用。
为解压数据库和保存各阶段产物预留至少10 GiB可用空间。

## 从头运行

本机 Windows 路径 `C:\Users\19756\Desktop\mp.zip` 在WSL对应
`/mnt/c/Users/19756/Desktop/mp.zip`。进入项目、激活环境后：

```bash
ss-screen mp-reproduce \
  --mp-zip /mnt/c/Users/19756/Desktop/mp.zip \
  --mbj-bundle "$ASSETS/mp-2944-mbj-results-20261104" \
  --output-dir /path/to/new-mp-to-318-run \
  --workers 4
```

接收者使用交付包内的 `"$ASSETS/mp.zip"` 替换 `--mp-zip` 即可。
输出目录必须尚不存在，并在冻结mBJ目录之外。
默认**重新计算4944份robocrys描述**，并行数由 `--workers` 控制；耗时取决于
CPU与文件系统。单材料先限时300秒，失败后重试一次、限时1800秒。
此入口不会重新计算带隙或启动DFT/SQS/MACE。

固定规则包括：稳定性预筛0.01 eV/atom；组成候选带隙上限1 eV、hull上限0；
历史排除 `mp-1205290, mp-1208530, mp-568220, mp-574458`；
端元原胞二元至多30原子、三元至多45原子。四项排除不是运行失败时自动删数据。
配对使用冻结mBJ包中的方法、QC和阈值，未知或失败带隙不补0、不用MP值补空。

## 可选：复用已核验的描述，仍从原库重新筛选与分组

使用显式缓存参数，并指定另一个尚不存在的输出目录：

```bash
ss-screen mp-reproduce \
  --mp-zip "$ASSETS/mp.zip" \
  --mbj-bundle "$ASSETS/mp-2944-mbj-results-20261104" \
  --output-dir /path/to/new-mp-to-318-cached-run \
  --descriptor-cache "$ASSETS/mp_descriptors_4944_verified_20261104.zip"
```

缓存来自同一MP快照此前已完成的本地描述计算。程序校验数据库SHA、4944个材料
成员、**本次数据库读取所得的每份输入结构SHA**、每份描述字节SHA和大小；不一致
则停止。缓存不提供最终分组或配对，组成筛选、分组、任务导出、几何对应与最终
配对仍重新执行。输出会明确记录 `descriptor_cache_used=true`、
`fresh_descriptor_count=0`；不能把该模式称为此次重新计算了全部描述。

## 验收和进度

`pipeline_state.json` 记录当前阶段与失败原因；正常结束为 `state=finished`。
入口暂不支持中途续跑；失败后先查看原因，修正后使用新的输出目录。

| 阶段 | 预期 |
|---|---|
| 原库稳定性预筛 | 46675条（该快照原始155361条） |
| 组成候选 | 二元1759、三元3189，共4948材料 |
| 扣除四项历史排除后的有效描述 | 4944 |
| 本地结构分组 | 二元491；三元曾实测1358，历史1354 |
| 端元任务 | 二元949、三元1995，共2944 |
| mBJ全状态覆盖 | 1999成功、620未收敛、325失败，0缺失 |
| 最终 | 79+239=318唯一配对，317端元 |

最终查看：

- `summary.json`：`passed=true`、`groups_recomputed_from_mp=true`及缓存使用状态。
- `07_pairs_from_mp/pairs_unique.csv`：本次生成的318配对。
- `07_pairs_from_mp/candidate_materials.csv`：317端元。
- `07_pairs_from_mp/identity_mapping_audit.csv`：新pending任务与真实mBJ任务的独立映射。
- `06_mbj_replay/validation/`：六批严格接收报告；`excluded_gap_results.csv`保留945条非成功记录。
- `03_condensation/source.json`：描述计算/缓存来源；从头模式另有逐项日志。

正式任务身份不相互替换。映射先比较主要结构字段，不同时按严格周期几何匹配，
允许换基、周期平移、位点映射和正交变换（含反射），同时检查物种与位点属性。
不把该匹配表述为原始JSON或SHA完全相同。
本次分组与历史分组按成员及对应A/X规范比较配对证据，带隙容差1e-12 eV。
三元中间组的历史差异不会被硬改成1354；最终身份/配对必须通过独立验收。

代码固定提交、实际验证模式及数据包SHA以随包 `DELIVERY.json` 和校验文件为准。
该入口的实现位于 `src/ssscreen/mp_reproduction.py`，缓存/路径/几何拒绝条件见
`tests/test_mp_reproduction.py`。源代码中的规范化指纹排序来自已审计历史规则，
无需运行额外的猴子补丁脚本。
