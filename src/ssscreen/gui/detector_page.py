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
    QTableWidgetItem,QTextBrowser,QVBoxLayout,QWidget,
)

from ..detector import (
    BAND_PRESETS_UM, DEFAULT_TARGET_UM, DEMO_ROWS, assess_rows, export_rows,
    index_geometry, read_csv,
)


class DetectorAssessmentPage(QWidget):
    """Evidence is read by identity; expensive geometry runs in a QProcess."""

    run_requested = Signal(list, str)

    COLUMNS=(
        ('candidate_material','候选材料'),('gap_a_eV','端元A带隙'),
        ('gap_b_eV','端元B带隙'),('target_um','目标波长'),
        ('target_gap_eV','目标能量'),('gap_candidate_status','带隙候选判断'),
        ('lattice_mismatch_pct','晶格失配'),
        ('substrate_recommendations','推荐衬底及薄膜面内主应变'),
        ('candidate_grade','候选等级优先'),
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
        form.addRow('目标波长',wavelength);root.addWidget(controls)
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
        # Give long bilingual headers two lines without changing their data keys.
        wrapped_headers={
            'gap_a_eV': '端元A带隙\n(eV)',
            'gap_b_eV': '端元B带隙\n(eV)',
            'target_um': '目标波长\n(μm)',
            'target_gap_eV': '目标能量\n(eV)',
            'lattice_mismatch_pct': '晶格失配\n(%)',
            'substrate_recommendations': '推荐衬底及薄膜面内主应变\n(%)',
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
        minimum_widths=(150,112,112,105,112,145,120,390,135)
        metrics=header.fontMetrics()
        for index,((key,title),minimum) in enumerate(zip(self.COLUMNS,minimum_widths)):
            shown=wrapped_headers.get(key,title)
            needed=max(metrics.horizontalAdvance(line) for line in shown.split('\n'))+28
            self.table.setColumnWidth(index,max(minimum,needed))
            self.table.horizontalHeaderItem(index).setToolTip(title)

        self.table.itemSelectionChanged.connect(self._detail)
        root.addWidget(self.table,3)
        self.details=QTextBrowser();self.details.setMaximumHeight(150)
        self.details.setOpenExternalLinks(False);root.addWidget(self.details,1)

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
        argv=['geometry-evaluate','--input',str(path),'--config',str(config),'--output',str(out)]
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
        evaluated=sum(r['substrate_principal_strain_pct'] is not None for r in self._results)
        self.summary.setText(f"数据来源：{'虚构演示' if self._demo_mode else '工程文件'}  |  候选 {len(self._results)}  |  端元范围覆盖目标 {covered}  |  已有衬底几何证据 {evaluated}")
        self.table.setRowCount(len(self._results))
        for i,row in enumerate(self._results):
            for j,(key,_) in enumerate(self.COLUMNS):
                v=row.get(key)
                if v is None or v=='':
                    shown='—'
                elif key in ('gap_a_eV','gap_b_eV','target_gap_eV'):
                    shown=f'{float(v):.4f} eV'
                elif key=='target_um':
                    shown=f'{float(v):.1f} μm'
                elif key=='lattice_mismatch_pct':
                    shown=f'{float(v):.4f}%'
                elif isinstance(v,float):
                    shown=f'{v:.5g}'
                else:
                    shown=str(v)
                item=QTableWidgetItem(shown)
                item.setToolTip(str(v) if v not in (None,'') else '缺少可追溯的有效数据')
                if key=='candidate_grade':
                    item.setForeground(Qt.darkGreen if v=='优先' else Qt.darkYellow)
                if key=='gap_candidate_status':
                    item.setForeground(Qt.darkGreen if v=='满足带隙候选' else Qt.darkYellow)
                if key=='band_match' and v=='端元范围覆盖':item.setForeground(Qt.darkGreen)
                self.table.setItem(i,j,item)
        self.details.setHtml('<p>选中候选，查看几何、稳定性证据、match ID及数据来源。</p>')
        if self._results:self.table.selectRow(0)

    def _detail(self) -> None:
        selected=self.table.selectedItems()
        if not selected:return
        index=selected[0].row()
        if index >= len(self._results):return
        row=self._results[index]
        def safe(key: str) -> str:
            val=row.get(key)
            return html.escape(str(val if val not in (None,'') else '—'))
        self.details.setHtml(
            '<p><b>端元A带隙：</b>'+safe('gap_a_eV')+' eV　<b>端元B带隙：</b>'+safe('gap_b_eV')+
            ' eV　<b>端元带隙范围：</b>'+safe('endpoint_gap_min_eV')+'–'+safe('endpoint_gap_max_eV')+
            ' eV　<b>目标光子能量：</b>'+safe('target_gap_eV')+' eV　<b>范围评估：</b>'+safe('band_match')+'</p>'
            '<p><b>带隙候选判断：</b>'+safe('gap_candidate_status')+'　<b>候选等级优先：</b>'+safe('candidate_grade')+
            '　<b>来源：</b>'+safe('gap_origin')+
            '　<b>数据：</b>'+safe('data_origin')+'</p>'
            '<p><b>晶格：</b>'+safe('lattice_status')+'　<b>声子：</b>'+safe('phonon_status')+
            '　<b>混合焓：</b>'+safe('mixing_status')+'　<b>凸包：</b>'+safe('hull_status')+'</p>'
            '<p><b>衬底：</b>'+safe('substrate_id')+'　<b>晶面：</b>'+safe('film_miller')+' / '+safe('substrate_miller')+
            '　<b>匹配面积(Å²)：</b>'+safe('match_area_A2')+'　<b>match ID：</b>'+safe('match_id')+'</p>'
            '<p><b>几何等级：</b>'+safe('geometry_grade')+'　<b>限制：</b>'+safe('caution')+'</p>'
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
