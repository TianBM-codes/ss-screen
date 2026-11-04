# 正式源码导航

真实目录：[`src/ssscreen/`](../../src/ssscreen/)

这里的代码是项目当前权威实现。`references/` 中的 notebook 和旧源码只用于追溯来源，不能覆盖 `src/` 的行为结论。

## 模块地图

| 导航页 | 真实目录/文件 | 职责 |
|---|---|---|
| [data.md](data.md) | [`src/ssscreen/data/`](../../src/ssscreen/data/) | MP/WBM 数据标准化、robocrys condensation、文件 I/O |
| [pair.md](pair.md) | [`src/ssscreen/pair/`](../../src/ssscreen/pair/) | 组成模板、环境匹配、过滤、带隙反馈和材料对枚举 |
| [stability.md](stability.md) | [`src/ssscreen/stability/`](../../src/ssscreen/stability/) | SQS、MACE 弛豫/混合焓、有限位移声子谱、MP 竞争相凸包与综合推荐 |
| [几何评价说明](../../docs/lattice_substrate_matching_development.md) | [`src/ssscreen/geometry_pipeline.py`](../../src/ssscreen/geometry_pipeline.py)、[`geometry_core.py`](../../src/ssscreen/geometry_core.py) | Stage 13端元晶格对应、衬底ZSL匹配、面内主应变与审计输出 |
| [六指标候选评价](../../docs/gui_stage13_detector.md) | [`material_assessment.py`](../../src/ssscreen/material_assessment.py)、[`detector.py`](../../src/ssscreen/detector.py) | GUI/CLI 共用逐项证据汇总，风险与缺失分别保留；[边界与QC测试](../../tests/test_material_assessment.py) |
| [cli.md](cli.md) | [`src/ssscreen/cli/`](../../src/ssscreen/cli/) | Click 命令、参数校验和阶段编排 |
| [gui.md](gui.md) | [`src/ssscreen/gui/`](../../src/ssscreen/gui/) | 可选 PySide6 桌面工作台、工程树、参数页和 CLI 子进程调用 |
| 配置 | [`src/ssscreen/config.py`](../../src/ssscreen/config.py) | 所有筛选/推荐阈值、元素排除集合和组成排列 |
| 包入口 | [`src/ssscreen/__init__.py`](../../src/ssscreen/__init__.py) | 包说明与 `__version__` |

## 依赖方向

```text
config.py
   ↓
data/ ─────→ pair/
               ↓
          stability/
               ↑
cli/app.py ─────┴── 编排所有阶段
   ↑
gui/app.py 作为可选前端调用真实 CLI
```

`pair/` 不依赖 AiiDA。`stability/` 的 SQS 核心不加载重型后端；只有显式运行 MACE 弛豫或声子力时才延迟加载 `[mlp]` 中的 MACE/Torch，默认 CI 仍不需要 GPU。

## 推荐阅读顺序

1. [`config.py`](../../src/ssscreen/config.py)
2. [data.md](data.md)
3. [pair.md](pair.md)
4. [cli.md](cli.md)
5. [gui.md](gui.md)
6. [stability.md](stability.md)
7. [几何评价说明](../../docs/lattice_substrate_matching_development.md)
8. [测试导航](../03_测试与测试数据/README.md)

## 最近同步

- 2026-11-04（原库到318对）：新增 [`mp_reproduction.py`](../../src/ssscreen/mp_reproduction.py) 从原始MP ZIP重建组成候选/分组/端元并结合外部mBJ结果验收318对；[`mbj_replay.py`](../../src/ssscreen/mbj_replay.py) 提供共用严格接收与历史参照回放。缓存显式选择、绑定输入结构SHA，默认重新计算描述。

- 2026-11-04（最终带隙规则）：按用户纠正，六指标带隙项改为端元闭区间覆盖 `1.239841984/λ(μm)`，不再要求合金带隙或双构型。共享函数负责零带隙/缺失/边界判断，GUI随波长立即重评；CLI新增当前波长覆盖参数。42项聚焦测试通过，之前双合金带隙规则已被本条替代。
- 2026-11-04：新增 `material_assessment.py` 共享六指标规则和条件说明；合金带隙至少两个有效构型、完整预期覆盖且均入目标区间。性质聚合排除结构 QC 失败和明确不完整的竞争集；主表综合评价与端元带隙预估分别导出，31 项聚焦回归通过。
- 2026-11-04：Stage 13 改为两侧独立对称不等价晶面枚举，记录固定衬底/薄膜变形约定，算法标记 v2；十种指定衬底真实计算和 2556 个匹配独立核验完成。原 `geometry.md` 链接无目标，已改指现有设计文档，未恢复缺失文件。
- 2026-09-07：新增可选 `src/ssscreen/gui/` 桌面工作台；`ss-screen-gui` 调用真实 CLI，
  不替代 `ss-screen` 命令行入口。
- 2026-08-03：新增 Stage 11 `stability/recommendation.py`；当前共有 25 个正式 Python 源文件。
- 2026-07-31：新增 Stage 10 MP 竞争相与同 MACE 能量基准凸包；当前共有 24 个正式 Python 源文件。
- 2026-07-31：新增 Stage 9 Phonopy/MACE 声子谱；当时共有 23 个正式 Python 源文件。
- 2026-07-30：新增 Stage 8 混合焓计算与严格能量来源核验；当前共有 22 个正式 Python 源文件。
- 2026-07-30：新增 Stage 7 MACE 后端和可恢复弛豫结果编排。
- 2026-07-22：依据当前 19 个 Python 源文件建立初始模块索引。
