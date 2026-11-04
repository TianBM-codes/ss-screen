"""Stage 13 material-level detector suitability page and optional geometry runner."""
from __future__ import annotations

import ast
import html
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,QComboBox,QDoubleSpinBox,QFileDialog,QFormLayout,QGroupBox,
    QHBoxLayout,QHeaderView,QLabel,QLineEdit,QMessageBox,QPushButton,QTableWidget,
    QTableWidgetItem,QTabWidget,QTextBrowser,QVBoxLayout,QWidget,
)

from ..detector import (
    BAND_PRESETS_UM, DEFAULT_TARGET_UM, DEMO_ROWS, assess_rows, export_rows,
    index_geometry, read_csv,
)
from ..material_assessment import EVALUATION_TABLE_MD


class DetectorAssessmentPage(QWidget):
    """Evidence is read by identity; expensive geometry runs in a QProcess."""

    run_requested = Signal(list, str)

    COLUMNS=(
        ('candidate_material','候选材料'),('endpoint_gap_range_eV','端元带隙范围'),
        ('lattice_mismatch_pct','晶格常数匹配'),
        ('phonon_min_THz','声子谱'),
        ('mixing_enthalpy_meV_atom','混合焓'),
        ('energy_above_hull_meV_atom','凸包上能'),
        ('substrate_recommendations','推荐衬底及薄膜面内主应变'),
        ('material_grade','综合评价'),
    )

    def __init__(self, project_provider, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_provider=project_provider
        self._results: list[dict[str,object]]=[]
        self._source_rows: list[dict[str,str]]=[]
        self._demo_mode=False
        self._setup();self.refresh()

    def _setup(self) -> None:
        root=QVBoxLayout(self);root.setContentsMargins(12,10,12,10);root.setSpacing(9)
        title=QHBoxLayout()
        heading=QLabel('探测器材料应用潜力评价');heading.setObjectName('pageTitle')
        title.addWidget(heading);title.addStretch(1)
        badge=QLabel('STAGE 13 · 材料级预筛');badge.setObjectName('stateBadge');title.addWidget(badge)
        root.addLayout(title)
        controls=QGroupBox('评估输入 / 参数');form=QFormLayout(controls)
        self.recommend_path=QLineEdit('12_recommend/recommendations.csv')
        form.addRow('Stage12推荐表',self.recommend_path)
        self.geometry_path=QLineEdit('13_geometry/candidate_evaluation.csv')
        form.addRow('几何评价表',self.geometry_path)
        self.geometry_input=QLineEdit('13_geometry/input')
        form.addRow('几何输入目录',self.geometry_input)
        self.geometry_config=QLineEdit('13_geometry/config.json')
        form.addRow('几何配置文件',self.geometry_config)
        wavelength=QHBoxLayout()
        self.band=QComboBox();self.band.addItems(BAND_PRESETS_UM);self.band.setCurrentIndex(1)
        self.target=QDoubleSpinBox();self.target.setDecimals(2);self.target.setRange(.01,100.0)
        self.target.setSuffix(' μm');self.target.setValue(DEFAULT_TARGET_UM)
        self.band.currentTextChanged.connect(self._preset_changed)
        wavelength.addWidget(self.band,1);wavelength.addWidget(self.target)
        form.addRow('用户目标波长',wavelength);root.addWidget(controls)
        actions=QHBoxLayout()
        for label,func in (
            ('读取工程结果',self.refresh),('加载内置演示数据',self.load_demo),
            ('计算几何指标',self.compute_geometry),('重新评估',self.recompute),
            ('导出评估CSV',self.export),
        ):
            button=QPushButton(label);button.clicked.connect(func)
            if label=='计算几何指标': self.geometry_button=button
            actions.addWidget(button)
        actions.addStretch();root.addLayout(actions)
        self.summary=QLabel('-');self.summary.setStyleSheet('font-weight:600;padding:5px 0')
        root.addWidget(self.summary)
        self.table=QTableWidget(0,len(self.COLUMNS))
        # Keep units in the header and evidence status beside each value.
        wrapped_headers={
            'endpoint_gap_range_eV': '端元带隙范围\n(eV)',
            'lattice_mismatch_pct': '晶格常数匹配\n(%)',
            'phonon_min_THz': '声子谱最低频率\n(THz)',
            'mixing_enthalpy_meV_atom': '混合焓\n(meV/atom)',
            'energy_above_hull_meV_atom': '凸包上能\n(meV/atom)',
            'substrate_recommendations': '推荐衬底及薄膜主应变\n(%)',
        }
        self.table.setHorizontalHeaderLabels([
            wrapped_headers.get(key,title) for key,title in self.COLUMNS
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)

        # Never squeeze all columns into the viewport: preserve readable
        # column widths and let Qt show a horizontal scrollbar when necessary.
        header=self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(80)
        header.setSectionsMovable(False)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFixedHeight(max(48,header.fontMetrics().height()*2+12))
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        minimum_widths=(125,155,120,145,120,120,280,130)
        metrics=header.fontMetrics()
        for index,((key,title),minimum) in enumerate(zip(self.COLUMNS,minimum_widths)):
            shown=wrapped_headers.get(key,title)
            needed=max(metrics.horizontalAdvance(line) for line in shown.split('\n'))+28
            self.table.setColumnWidth(index,max(minimum,needed))
            self.table.horizontalHeaderItem(index).setToolTip(title)

        self.table.itemSelectionChanged.connect(self._detail)
        self.tabs=QTabWidget()
        self.tabs.addTab(self.table,'候选评价')
        self.criteria=QTextBrowser();self.criteria.setOpenExternalLinks(False)
        self.criteria.setMarkdown(EVALUATION_TABLE_MD)
        self.tabs.addTab(self.criteria,'评价条件')
        root.addWidget(self.tabs,3)
        self.details=QTextBrowser();self.details.setMaximumHeight(220)
        self.details.setOpenExternalLinks(False);root.addWidget(self.details,1)
        self.target.valueChanged.connect(self.recompute)

    def _root(self) -> Path:
        return Path(self.project_provider()).expanduser().resolve()

    def _resolve(self, text: str) -> Path:
        p=Path(text.strip()).expanduser()
        return p if p.is_absolute() else self._root()/p

    def _preset_changed(self,label: str) -> None:
        if label in BAND_PRESETS_UM:self.target.setValue(BAND_PRESETS_UM[label])

    def refresh(self) -> None:
        self._demo_mode=False
        path=self._resolve(self.recommend_path.text())
        try: self._source_rows=read_csv(path) if path.is_file() else []
        except (OSError,UnicodeError,ValueError) as exc:
            self._source_rows=[];QMessageBox.warning(self,'推荐表读取失败',str(exc))
        self.recompute()

    def load_demo(self) -> None:
        self._demo_mode=True
        self._source_rows=[dict(r) for r in DEMO_ROWS]
        self.recompute()

    def compute_geometry(self) -> None:
        path=self._resolve(self.geometry_input.text())
        config=self._resolve(self.geometry_config.text())
        if not (path/'candidates.csv').exists() or not config.is_file():
            QMessageBox.warning(self,'几何输入不完整',
                '请先按模板准备几何输入（candidates.csv、endmembers.csv、alloy_structures.csv、substrates.json）及config.json。\n'
                '缺失数据不会自动填零或从演示行生成。')
            return
        out=self._resolve(self.geometry_path.text()).parent
        argv=['geometry-evaluate','--input',str(path),'--config',str(config),'--output',str(out),
              '--target-wavelength-um',str(self.target.value())]
        recommendations=self._resolve(self.recommend_path.text())
        if recommendations.is_file():
            argv.extend(['--recommendations',str(recommendations)])
        self.run_requested.emit(argv,'晶格常数匹配与衬底主应变评价')

    def recompute(self) -> None:
        geo={}
        if not self._demo_mode:
            file=self._resolve(self.geometry_path.text())
            if file.is_file():
                try: geo=index_geometry(read_csv(file))
                except (OSError,UnicodeError,ValueError) as exc:
                    QMessageBox.warning(self,'几何数据读取失败',str(exc))
        try:
            self._results=assess_rows(self._source_rows,self.target.value(),geo,
                data_origin='内置演示（非真实材料）' if self._demo_mode else '工程结果')
        except ValueError as exc:
            QMessageBox.warning(self,'候选身份核验失败',str(exc));self._results=[]
        top_matches_by_candidate: dict[str,list[dict[str,str]]] = {}
        if not self._demo_mode:
            top_path=self._resolve(self.geometry_path.text()).parent/'substrate_top_matches.csv'
            if top_path.is_file():
                try:
                    for match in read_csv(top_path):
                        top_matches_by_candidate.setdefault(
                            str(match.get('candidate_id') or '').strip(),[]
                        ).append(match)
                except (OSError,UnicodeError,ValueError) as exc:
                    QMessageBox.warning(self,'衬底推荐读取失败',str(exc))
        for row in self._results:
            comp_a=str(row.get('comp_a') or '')
            comp_b=str(row.get('comp_b') or '')
            x=row.get('fraction_b')
            subscript=str.maketrans('0123456789.-','₀₁₂₃₄₅₆₇₈₉.₋')
            if comp_a and comp_b and x is not None:
                prefix=os.path.commonprefix([comp_a,comp_b])
                xa=f'{1-float(x):g}'.translate(subscript)
                xb=f'{float(x):g}'.translate(subscript)
                row['candidate_material']=f'{prefix}{comp_a[len(prefix):]}{xa}{comp_b[len(prefix):]}{xb}'
            else:
                row['candidate_material']=str(row.get('candidate_id') or '未命名候选')
            row['gap_candidate_status']=(
                '满足带隙候选' if row.get('band_match')=='端元范围覆盖' else '次优'
            )
            matches=top_matches_by_candidate.get(str(row.get('candidate_id') or ''),[])[:3]
            formatted=[]
            for rank,match in enumerate(matches,1):
                substrate=match.get('substrate_id') or '未命名衬底'
                try:
                    strains=ast.literal_eval(match.get('principal_strains') or '[]')
                    strain_text=' / '.join(f'{float(value)*100:+.4f}' for value in strains)
                except (ValueError,TypeError,SyntaxError):
                    try:
                        strain_text='±'+f"{float(match.get('max_abs_principal_strain'))*100:.2f}"
                    except (ValueError,TypeError):
                        strain_text='应变缺失'
                formatted.append(f'{rank}. {substrate}：{strain_text}%')
            row['substrate_recommendations']='\n'.join(formatted) if formatted else '—'
        covered=sum(r['band_match']=='端元范围覆盖' for r in self._results)
        priority=sum(r['material_grade']=='优先进一步验证' for r in self._results)
        lower=sum(r['material_grade']=='降低优先级' for r in self._results)
        self.summary.setText(f"数据来源：{'虚构演示' if self._demo_mode else '工程文件'}  |  候选 {len(self._results)}  |  综合优先 {priority}  |  降低优先级 {lower}  |  端元范围覆盖目标 {covered}")
        status_keys={
            'endpoint_gap_range_eV':'gap_target_status','lattice_mismatch_pct':'lattice_status',
            'phonon_min_THz':'phonon_status','mixing_enthalpy_meV_atom':'mixing_status',
            'energy_above_hull_meV_atom':'hull_status',
        }
        self.table.setRowCount(len(self._results))
        for i,row in enumerate(self._results):
            for j,(key,_) in enumerate(self.COLUMNS):
                v=row.get(key)
                if v is None or v=='':
                    shown='—'
                elif key in status_keys and key!='endpoint_gap_range_eV':
                    shown=f'{float(v):.4f}'
                elif isinstance(v,float):
                    shown=f'{v:.5g}'
                else:
                    shown=str(v)
                status=str(row.get(status_keys.get(key,'')) or '')
                if key=='endpoint_gap_range_eV':
                    shown+=f"\n目标 {float(row['target_gap_eV']):.4f}\n{row['band_match']}"
                elif key in status_keys:
                    shown+='\n'+status
                elif key=='material_grade':
                    status=str(v)
                    shown+='\n'+str(row.get('evidence_completeness') or '')
                item=QTableWidgetItem(shown)
                item.setToolTip(shown)
                if status in ('显著虚频','高风险','降低优先级','较大失配风险'):
                    item.setForeground(Qt.darkRed)
                elif status in ('优先','通过','优先进一步验证'):
                    item.setForeground(Qt.darkGreen)
                elif status:
                    item.setForeground(Qt.darkYellow)
                if key=='material_grade':
                    item.setToolTip(str(row.get('material_reason') or shown))
                self.table.setItem(i,j,item)
        self.details.setHtml('<p>选中候选，查看几何、稳定性证据、match ID及数据来源。</p>')
        if self._results:
            self.table.selectRow(0)
            # Refresh may retain the same selection without emitting a signal.
            self._detail()

    def _detail(self) -> None:
        selected=self.table.selectedItems()
        if not selected:return
        index=selected[0].row()
        if index >= len(self._results):return
        row=self._results[index]
        def safe(key: str) -> str:
            val=row.get(key)
            return html.escape(str(val if val not in (None,'') else '—'))
        def number(key: str) -> str:
            val=row.get(key)
            return f'{float(val):.4f}' if val not in (None,'') else '—'
        self.details.setHtml(
            '<p><b>端元A带隙：</b>'+safe('gap_a_eV')+' eV　<b>端元B带隙：</b>'+safe('gap_b_eV')+
            ' eV　<b>端元带隙范围：</b>'+safe('endpoint_gap_min_eV')+'–'+safe('endpoint_gap_max_eV')+
            ' eV　<b>目标光子能量：</b>'+safe('target_gap_eV')+' eV　<b>范围评估：</b>'+safe('band_match')+'</p>'
            '<p><b>带隙候选判断：</b>'+safe('gap_candidate_status')+'　<b>带隙范围优先级：</b>'+safe('candidate_grade')+
            '　<b>来源：</b>'+safe('endpoint_gap_origin')+
            '　<b>数据：</b>'+safe('data_origin')+'</p>'
            '<p><b>晶格：</b>'+safe('lattice_status')+'　<b>最低声子频率：</b>'+number('phonon_min_THz')+' THz（'+safe('phonon_status')+'）'+
            '　<b>混合焓：</b>'+number('mixing_enthalpy_meV_atom')+' meV/原子（'+safe('mixing_status')+'）'+
            '　<b>凸包上能：</b>'+number('energy_above_hull_meV_atom')+' meV/原子（'+safe('hull_status')+'）</p>'
            '<p><b>衬底：</b>'+safe('substrate_id')+'　<b>晶面：</b>'+safe('film_miller')+' / '+safe('substrate_miller')+
            '　<b>匹配面积(Å²)：</b>'+safe('match_area_A2')+'　<b>match ID：</b>'+safe('match_id')+'</p>'
            '<p><b>带隙条件：</b>min(EgA, EgB) ≤ 1.239841984 / λ(μm) ≤ max(EgA, EgB)。'
            '当前波长 '+number('target_um')+' μm；'+safe('gap_target_status')+'。仅使用端元带隙范围。</p>'
            '<p><b>综合评价：</b>'+safe('material_grade')+'　<b>证据完整性：</b>'+safe('evidence_completeness')+
            '　'+safe('material_reason')+'</p>'
            '<p><b>几何等级：</b>'+safe('geometry_grade')+
            '　<b>应变约定：</b>衬底固定，薄膜变形；正值拉伸、负值压缩。未计算共同松弛及弹性应变能。</p>'
            '<p><b>限制：</b>'+safe('caution')+'</p>'
        )

    def export(self) -> None:
        if not self._results:
            QMessageBox.information(self,'暂无结果','请先读取候选结果。');return
        default=self._root()/'13_geometry'/'candidate_assessment.csv'
        filename,_=QFileDialog.getSaveFileName(self,'导出材料级评价',str(default),'CSV文件 (*.csv)')
        if not filename:return
        try:export_rows(Path(filename),self._results)
        except OSError as exc:
            QMessageBox.critical(self,'导出失败',str(exc));return
        QMessageBox.information(self,'导出完成',f'已保存：\n{filename}')
