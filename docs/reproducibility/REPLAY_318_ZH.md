# 重现318个材料配对

交付分为 GitHub 代码和一个独立数据压缩包。无需 MP 原数据库、mp_offline、
MP API 密钥、MACE 模型、VASP 或 AiiDA。这里只重新校验已有 mBJ 结果并运行配对。

## 1. 获取代码与数据

从 `https://github.com/TianBM-codes/ss-screen` 获取已合并版本，或按数据包
`DELIVERY.json` 中记录的 PR/head commit 检出待审阅版本。PR 创建不等于合并。

独立数据交付包为 `ss-screen-318-pairs-data-20261104.zip`。解压到仓库外，
其中 `mp-2944-mbj-results-20261104/` 是原始冻结结果目录。顶层中文说明和
`DELIVERY.json` 记录代码版本、来源 ZIP SHA 和预期计数；冻结目录里的原件不改。
数据包未包含 MP 原库或模型权重。原始计算 XML 也不是本次回放的必需项。

## 2. 建立环境

以下命令在 Linux/WSL、Python 3.11 下执行。按接收者机器替换路径。
已有项目环境请直接激活，不要覆盖环境；新安装使用一个新 checkout。

```bash
cd /path/to/ss-screen
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements/reproduction-20261104/screen-wsl-py311.constraints.txt -e .
python -m pip check
python -c "import ssscreen; print(ssscreen.__file__)"
```

这里只安装核心依赖，不需要复制另一台机器的 `.venv`。安装需要软件包下载渠道；
数据 ZIP 不是完整的离线安装包。约束文件记录本次实测版本，非跨平台保证。

## 3. 回放

```bash
cd /path/to/ss-screen
source .venv/bin/activate
python scripts/replay_mbj_results.py \
  --bundle /path/to/extracted/mp-2944-mbj-results-20261104 \
  --output /path/to/new-replay-output
```

输出目录必须尚不存在，且在数据包之外。入口先校验逐文件 SHA、任务/结构身份和
六批方法/QC，再运行严格接收、回填和配对；任一校验失败会报错。冻结输入不改动。

## 4. 验收

查看输出 `replay_summary.json`：`passed=true`，2944条记录、0缺失、
1999成功、620未收敛、325失败；二元79对、三元239对，共318唯一配对、317端元。
只用成功带隙，不把失败/未收敛当作0 eV，不用数据库值补齐。

- `pairs_unique.csv`：318个配对。
- `candidate_materials.csv`：317个端元。
- `excluded_gap_results.csv`：945条未收敛/失败记录。
- `validation/`：六批严格验证报告。
- `environment_this_replay.json`：接收者实际运行环境。

此入口不启动电子结构、SQS、MACE或声子计算，也不改写既有 pending 任务身份。
完整方法、输入来源、选择规则和阈值保存在冻结目录 README、snapshot、provenance 中。
