"""Stage 13 material-level detector suitability page and optional geometry runner."""
from __future__ import annotations

import html
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
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

    COLUMNS=(
        ('candidate_id','候选ID'),('comp_a','端元A'),('comp_b','端元B'),
        ('fraction_b','组分x'),('gap_eV','带隙(eV)'),
        ('gap_equivalent_wavelength_um','带隙等效波长(μm)'),('band_match','目标波段'),
        ('lattice_mismatch_pct','晶格常数匹配(%)'),('phonon_min_THz','声子(THz)'),
        ('mixing_enthalpy_meV_atom','混合焓(meV/atom)'),
        ('energy_above_hull_meV_atom','凸包上能(meV/atom)'),
        ('substrate_principal_strain_pct','衬底主应变(%)'),
        ('candidate_grade','候选等级'),
    )

    def __init__(self, project_provider, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_provider=project_provider
        self._results: list[dict[str,object]]=[]
        self._source_rows: list[dict[str,str]]=[]
        self._demo_mode=False
        self._proc: QProcess | None=None
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
        self.geometry_path=QLineEdit('13_detector/geometry/output/candidate_evaluation.csv')
        form.addRow('几何评价表',self.geometry_path)
        self.geometry_input=QLineEdit('13_detector/geometry/input')
        form.addRow('几何输入目录',self.geometry_input)
        self.geometry_config=QLineEdit('13_detector/geometry/config.json')
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
            'gap_equivalent_wavelength_um': '带隙等效波长\n(μm)',
            'lattice_mismatch_pct': '晶格常数匹配\n(%)',
            'phonon_min_THz': '声子\n(THz)',
            'mixing_enthalpy_meV_atom': '混合焓\n(meV/atom)',
            'energy_above_hull_meV_atom': '凸包上能\n(meV/atom)',
            'substrate_principal_strain_pct': '衬底主应变\n(%)',
        }
        self.table.setHorizontalHeaderLabels([
            wrapped_headers.get(key,title) for key,title in self.COLUMNS
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False);self.table.setWordWrap(False)
        self.table.setAlternatingRowColors(True)

        # Never squeeze all 13 columns into the viewport: preserve readable
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
        minimum_widths=(112,108,108,86,103,156,120,154,115,143,148,150,132)
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
        if self._proc is not None and self._proc.state()!=QProcess.NotRunning:
            QMessageBox.information(self,'正在计算','几何计算正在执行，请不要重复启动。');return
        path=self._resolve(self.geometry_input.text())
        config=self._resolve(self.geometry_config.text())
        if not (path/'candidates.csv').exists() or not config.is_file():
            QMessageBox.warning(self,'几何输入不完整',
                '请先按模板准备几何输入（candidates.csv、endmembers.csv、alloy_structures.csv、substrates.json）及config.json。\n'
                '缺失数据不会自动填零或从演示行生成。')
            return
        out=self._resolve(self.geometry_path.text()).parent
        proc=QProcess(self)
        proc.setProgram(sys.executable)
        proc.setArguments(['-m','ssscreen.geometry_cli','--input',str(path),'--config',str(config),'--output',str(out)])
        proc.setWorkingDirectory(str(self._root()))
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.finished.connect(self._geometry_finished)
        proc.errorOccurred.connect(self._geometry_error)
        self._proc=proc;self.geometry_button.setEnabled(False)
        self.summary.setText('真实结构几何计算中…')
        proc.start()

    def _geometry_error(self, error) -> None:
        self.geometry_button.setEnabled(True)
        QMessageBox.warning(self,'无法启动几何计算',str(error))

    def _geometry_finished(self, code: int, _status) -> None:
        self.geometry_button.setEnabled(True)
        detail=bytes(self._proc.readAllStandardOutput()).decode('utf-8','replace') if self._proc else ''
        if code:
            QMessageBox.warning(self,'几何计算失败',f'请检查输入结构、身份和配置：\n{detail[-3000:]}')
        else:
            self.refresh()
            QMessageBox.information(self,'计算完成','几何结果已保存并载入；单构型衬底结论不代表器件性能。')

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
        covered=sum(r['band_match']=='带隙覆盖' for r in self._results)
        evaluated=sum(r['substrate_principal_strain_pct'] is not None for r in self._results)
        self.summary.setText(f"数据来源：{'虚构演示' if self._demo_mode else '工程文件'}  |  候选 {len(self._results)}  |  带隙覆盖 {covered}  |  已有衬底几何证据 {evaluated}")
        self.table.setRowCount(len(self._results))
        for i,row in enumerate(self._results):
            for j,(key,_) in enumerate(self.COLUMNS):
                v=row.get(key)
                shown='—' if v is None or v=='' else f'{v:.5g}' if isinstance(v,float) else str(v)
                item=QTableWidgetItem(shown)
                item.setToolTip(str(v) if v not in (None,'') else '缺少可追溯的有效数据')
                if key=='band_match' and v=='带隙覆盖':item.setForeground(Qt.darkGreen)
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
            '<p><b>带隙：</b>'+safe('gap_origin')+'　<b>数据：</b>'+safe('data_origin')+'</p>'
            '<p><b>晶格：</b>'+safe('lattice_status')+'　<b>声子：</b>'+safe('phonon_status')+
            '　<b>混合焓：</b>'+safe('mixing_status')+'　<b>凸包：</b>'+safe('hull_status')+'</p>'
            '<p><b>衬底：</b>'+safe('substrate_id')+'　<b>晶面：</b>'+safe('film_miller')+' / '+safe('substrate_miller')+
            '　<b>匹配面积(Å²)：</b>'+safe('match_area_A2')+'　<b>match ID：</b>'+safe('match_id')+'</p>'
            '<p><b>几何等级：</b>'+safe('geometry_grade')+'　<b>限制：</b>'+safe('caution')+'</p>'
        )

    def export(self) -> None:
        if not self._results:
            QMessageBox.information(self,'暂无结果','请先读取候选结果。');return
        default=self._root()/'13_detector'/'detector_assessment.csv'
        filename,_=QFileDialog.getSaveFileName(self,'导出材料级评价',str(default),'CSV文件 (*.csv)')
        if not filename:return
        try:export_rows(Path(filename),self._results)
        except OSError as exc:
            QMessageBox.critical(self,'导出失败',str(exc));return
        QMessageBox.information(self,'导出完成',f'已保存：\n{filename}')
