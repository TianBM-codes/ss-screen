import {
  ArrowDownToLine,
  Boxes,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  ClipboardCheck,
  Database,
  FileArchive,
  FileInput,
  FileOutput,
  FlaskConical,
  Gauge,
  GitBranch,
  Layers3,
  ListChecks,
  Microscope,
  Network,
  PlayCircle,
  RotateCcw,
  SlidersHorizontal,
  UploadCloud,
} from "lucide-react";

type StageStatus = "implemented" | "next" | "future" | "external";

type WorkflowStage = {
  id: string;
  title: string;
  command: string;
  status: StageStatus;
  purpose: string;
  userInputs: string[];
  outputs: string[];
  uiNotes: string[];
};

const statusText: Record<StageStatus, string> = {
  implemented: "已有 Web 切片",
  next: "优先接入",
  future: "后续阶段",
  external: "外部计算",
};

const stages: WorkflowStage[] = [
  {
    id: "01",
    title: "准备数据集",
    command: "ss-screen dataset mp / dataset wbm",
    status: "implemented",
    purpose: "把 Materials Project 或 WBM 数据整理成统一 DataFrame，作为后续筛选的权威输入。",
    userInputs: ["数据源", "Dataset 名称", "max_e_hull", "WBM 结构文件", "可选 summary"],
    outputs: ["mp.df / wbm.df", "dataset provenance", "Dataset 详情"],
    uiNotes: ["上传文件校验", "数据行数", "SHA-256", "来源与版本记录"],
  },
  {
    id: "02",
    title: "组成模板筛选",
    command: "ss-screen composition-screen",
    status: "implemented",
    purpose: "按二元/三元组成模板寻找可替换 X 位点的候选材料集合。",
    userInputs: ["Dataset", "二元/三元", "max_bandgap", "max_e_hull", "排除元素", "最小 X 元素数"],
    outputs: ["composition-candidates.csv", "composition provenance", "候选预览"],
    uiNotes: ["冻结输入身份", "候选表格", "零候选合法状态", "参数摘要"],
  },
  {
    id: "03",
    title: "结构凝聚",
    command: "ss-screen condense",
    status: "implemented",
    purpose: "调用 robocrys，把候选结构转换成可比较的局部环境 JSON 描述。",
    userInputs: ["Composition Run", "批大小", "是否允许单材料失败"],
    outputs: ["condensed-structures.zip", "index CSV", "failure CSV", "manifest"],
    uiNotes: ["批进度", "失败清单", "取消/重试", "断点续跑"],
  },
  {
    id: "04",
    title: "结构环境匹配",
    command: "ss-screen structure-match",
    status: "next",
    purpose: "把组成候选和 condensed 描述汇合，用 X 位点环境指纹得到真正同构的结构分组。",
    userInputs: ["Composition 候选", "Condensation archive", "min_x_elements"],
    outputs: ["structure-groups.json", "missing/invalid summary"],
    uiNotes: ["分组数量", "缺失描述", "损坏 JSON", "结构组成员预览"],
  },
  {
    id: "05",
    title: "导出高精度带隙任务",
    command: "ss-screen gap-export",
    status: "next",
    purpose: "为 VASP、ABACUS、AiiDA 等外部平台生成确定性任务 ID、结构文件和结果模板。",
    userInputs: ["Structure groups", "Dataset", "方法名称", "结构格式", "max_natoms"],
    outputs: ["gap_tasks.csv", "JSON/CIF/POSCAR", "results template", "method metadata"],
    uiNotes: ["任务包下载", "结构数量", "方法身份", "设置模板"],
  },
  {
    id: "06",
    title: "外部带隙计算",
    command: "VASP / ABACUS / AiiDA",
    status: "external",
    purpose: "用户或外部计算平台完成 HSE06、mBJ 等高精度带隙计算。",
    userInputs: ["任务包", "计算平台", "方法设置", "结果目录"],
    outputs: ["vasprun.xml", "gap result CSV", "计算日志"],
    uiNotes: ["平台外执行", "结果上传入口", "缺失任务提示", "方法 metadata 校验"],
  },
  {
    id: "07",
    title: "收集与校验 gap 结果",
    command: "ss-screen gap-collect-vasp / gap-validate",
    status: "next",
    purpose: "解析或上传外部 gap 结果，校验材料、结构、方法、设置和数值合法性。",
    userInputs: ["gap_tasks.csv", "结果目录或 CSV", "method metadata"],
    outputs: ["validated gaps", "rejected rows", "audit report"],
    uiNotes: ["成功/未收敛/失败/缺失", "拒绝原因", "覆盖率", "重复结果检查"],
  },
  {
    id: "08",
    title: "枚举材料对",
    command: "ss-screen pair",
    status: "next",
    purpose: "把高精度 gap 回填到结构组内，筛出可形成带隙可调固溶体的材料对。",
    userInputs: ["Structure groups", "Validated gaps", "gap 阈值", "方法选择"],
    outputs: ["final_pairs.csv", "coverage summary"],
    uiNotes: ["pair 结果表", "gap 覆盖率", "缺失材料", "方法对比"],
  },
  {
    id: "09",
    title: "SQS 合金结构",
    command: "ss-screen stability sqs-generate",
    status: "future",
    purpose: "针对候选材料对生成端元结构和不同组分的初步 SQS 合金结构。",
    userInputs: ["final pairs", "Dataset", "目标比例", "超胞", "SQS 后端"],
    outputs: ["SQS structures", "endpoint structures", "manifest"],
    uiNotes: ["结构下载", "比例设置", "端元去重", "manifest 审计"],
  },
  {
    id: "10",
    title: "稳定性证据",
    command: "relax / mixing-enthalpy / phonon / convex-hull",
    status: "future",
    purpose: "用同一 MLP 能量基准计算弛豫、混合焓、声子和竞争相凸包证据。",
    userInputs: ["模型 checkpoint", "设备", "精度", "声子超胞", "MP 来源"],
    outputs: ["relax results", "mixing enthalpy", "phonon summary", "hull results"],
    uiNotes: ["长任务队列", "失败恢复", "模型哈希", "证据兼容性"],
  },
  {
    id: "11",
    title: "综合推荐",
    command: "ss-screen recommend",
    status: "future",
    purpose: "汇总 gap、混合焓、声子、凸包和可选缺陷证据，输出可审计推荐结论。",
    userInputs: ["final pairs", "gap evidence", "稳定性证据", "推荐阈值", "可选缺陷表"],
    outputs: ["recommendations.csv", "Markdown report", "summary JSON"],
    uiNotes: ["promising / uncertain / low-priority", "L2-L6 证据等级", "原因解释", "下一步建议"],
  },
];

const groups = [
  { title: "当前已经有页面基础", value: "Stage 1-2", detail: "Dataset、composition、condensation 已有 Web 垂直切片" },
  { title: "建议先补齐", value: "Stage 3-5", detail: "结构匹配、gap 任务交换、最终 pair 枚举" },
  { title: "后续再接重计算", value: "Stage 6-11", detail: "SQS、MACE、phonon、convex hull、recommend" },
];

const implementationSteps = [
  "先把 Stage 3-5 做成静态表单和结果页，再接后端 API。",
  "每个阶段都冻结上一步 Artifact 的 ID 和 SHA，页面只展示逻辑身份。",
  "重计算阶段先支持导入已有结果，后台资源确认后再接 Worker。",
  "最终用一个总览页串联所有 Run，让用户顺着流程继续下一步。",
];

function StatusPill({ status }: { status: StageStatus }) {
  return <span className={`prototype-status prototype-status-${status}`}>{statusText[status]}</span>;
}

function ChipList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="prototype-chip-block">
      <span>{title}</span>
      <div>
        {items.map((item) => (
          <small key={item}>{item}</small>
        ))}
      </div>
    </div>
  );
}

export function WorkflowPrototypePage() {
  const activeStage = stages.find((stage) => stage.status === "next") ?? stages[0];

  return (
    <section className="page workflow-prototype-page">
      <header className="page-header workflow-prototype-header">
        <div>
          <p className="eyebrow">INTERFACE PROTOTYPE</p>
          <h1>SS-Screen 分析流程界面草图</h1>
          <p>纯前端说明页，用来和后台同事确认流程、输入项、产物和阶段边界。</p>
        </div>
        <div className="prototype-header-actions" aria-label="原型状态">
          <span><CircleDot aria-hidden="true" />不连接后端</span>
          <span><PlayCircle aria-hidden="true" />可逐步接入 CLI</span>
        </div>
      </header>

      <div className="prototype-summary-band" aria-label="建设范围摘要">
        {groups.map((item) => (
          <div key={item.title}>
            <span>{item.title}</span>
            <strong>{item.value}</strong>
            <small>{item.detail}</small>
          </div>
        ))}
      </div>

      <div className="prototype-layout">
        <section className="prototype-flow" aria-labelledby="prototype-flow-title">
          <div className="section-heading">
            <div>
              <h2 id="prototype-flow-title">完整分析流程</h2>
              <p>每一段对应一个 CLI 能力，未来可以变成一个 Run 或一个 StageRunner。</p>
            </div>
          </div>
          <ol className="stage-timeline">
            {stages.map((stage) => (
              <li key={stage.id} className={`stage-timeline-item stage-${stage.status}`}>
                <div className="stage-index">{stage.id}</div>
                <div className="stage-content">
                  <div className="stage-title-row">
                    <h3>{stage.title}</h3>
                    <StatusPill status={stage.status} />
                  </div>
                  <p>{stage.purpose}</p>
                  <code>{stage.command}</code>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <aside className="prototype-panel" aria-labelledby="prototype-panel-title">
          <div className="prototype-panel-heading">
            <Network aria-hidden="true" />
            <div>
              <span>建议下一步</span>
              <h2 id="prototype-panel-title">{activeStage.title}</h2>
            </div>
          </div>
          <p>{activeStage.purpose}</p>
          <ChipList title="用户输入" items={activeStage.userInputs} />
          <ChipList title="阶段产物" items={activeStage.outputs} />
          <ChipList title="界面要点" items={activeStage.uiNotes} />
        </aside>
      </div>

      <section className="prototype-workbench" aria-labelledby="prototype-workbench-title">
        <div className="section-heading">
          <div>
            <h2 id="prototype-workbench-title">页面组成建议</h2>
            <p>先做成静态工作台，后续把按钮、表单和结果表接到真实 API。</p>
          </div>
        </div>

        <div className="prototype-surfaces">
          <div>
            <Database aria-hidden="true" />
            <h3>数据入口</h3>
            <p>选择 MP 离线快照、上传 WBM 文件，显示行数、来源、SHA 和 provenance。</p>
          </div>
          <div>
            <SlidersHorizontal aria-hidden="true" />
            <h3>参数表单</h3>
            <p>把 CLI option 变成表单控件，常用参数直接展示，高级阈值折叠。</p>
          </div>
          <div>
            <Gauge aria-hidden="true" />
            <h3>任务状态</h3>
            <p>显示排队、运行、完成、失败、取消和重试，长任务展示批次进度。</p>
          </div>
          <div>
            <FileOutput aria-hidden="true" />
            <h3>结果浏览</h3>
            <p>对候选、结构组、pair 和推荐结果提供表格预览、筛选和下载。</p>
          </div>
        </div>
      </section>

      <section className="prototype-command-map" aria-labelledby="prototype-command-title">
        <div className="section-heading">
          <div>
            <h2 id="prototype-command-title">CLI 到界面的映射</h2>
            <p>后台可按这张表决定每个按钮最终调用哪个命令或函数。</p>
          </div>
        </div>
        <div className="table-wrap prototype-table">
          <table>
            <thead>
              <tr>
                <th>阶段</th>
                <th>CLI 能力</th>
                <th>页面输入</th>
                <th>页面输出</th>
                <th>接入顺序</th>
              </tr>
            </thead>
            <tbody>
              {stages.map((stage) => (
                <tr key={stage.id}>
                  <td><strong>{stage.id}. {stage.title}</strong></td>
                  <td><code>{stage.command}</code></td>
                  <td>{stage.userInputs.join("、")}</td>
                  <td>{stage.outputs.join("、")}</td>
                  <td><StatusPill status={stage.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="prototype-implementation" aria-labelledby="prototype-implementation-title">
        <div className="prototype-implementation-main">
          <ClipboardCheck aria-hidden="true" />
          <div>
            <p className="eyebrow">IMPLEMENTATION ORDER</p>
            <h2 id="prototype-implementation-title">推荐落地顺序</h2>
          </div>
        </div>
        <ol>
          {implementationSteps.map((step) => (
            <li key={step}>
              <CheckCircle2 aria-hidden="true" />
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="prototype-artifact-flow" aria-label="制品流转">
        <FileInput aria-hidden="true" />
        <span>用户输入</span>
        <ChevronRight aria-hidden="true" />
        <Layers3 aria-hidden="true" />
        <span>Run / Task / Attempt</span>
        <ChevronRight aria-hidden="true" />
        <FileArchive aria-hidden="true" />
        <span>ArtifactStore</span>
        <ChevronRight aria-hidden="true" />
        <ListChecks aria-hidden="true" />
        <span>结果审计</span>
        <ChevronRight aria-hidden="true" />
        <ArrowDownToLine aria-hidden="true" />
        <span>下载报告</span>
      </section>
    </section>
  );
}
