"""Stage 13 detector *materials-level* evidence adapter.

Legacy instrument columns are intentionally removed. All structural/energy
values are read from existing evidence; lattice and substrate geometry must
be computed from real structure manifests with geometry_pipeline. No device
figures are inferred from gaps or strain.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Mapping

PHOTON_ENERGY_EV_UM = 1.239841984
DEFAULT_TARGET_UM = 2.0
BAND_PRESETS_UM = {
    '近红外（NIR）：1.0 μm': 1.0,
    '短波红外（SWIR）：2.0 μm': 2.0,
    '中波红外（MWIR）：4.0 μm': 4.0,
    '长波红外（LWIR）：10.0 μm': 10.0,
}
OUTPUT_COLUMNS = (
    'candidate_id','pair_index','comp_a','comp_b','fraction_b',
    'gap_a_eV','gap_b_eV','endpoint_gap_min_eV','endpoint_gap_max_eV',
    'alloy_gap_eV','gap_origin','gap_equivalent_wavelength_um',
    'target_um','target_gap_eV','band_match',
    'lattice_mismatch_pct','lattice_status',
    'phonon_min_THz','phonon_status',
    'mixing_enthalpy_meV_atom','mixing_status',
    'energy_above_hull_meV_atom','hull_status',
    'substrate_principal_strain_pct','substrate_status',
    'substrate_id','film_miller','substrate_miller','match_area_A2','match_id',
    'substrate_recommendations',
    'candidate_grade','geometry_grade','evidence_completeness',
    'source_structure_id','data_origin','caution',
)


def _number(value: object) -> float | None:
    if value is None or isinstance(value,bool): return None
    try: x = float(str(value).strip())
    except (ValueError,TypeError): return None
    return x if math.isfinite(x) else None


def read_csv(path: Path) -> list[dict[str,str]]:
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def index_geometry(rows: list[dict[str,str]]) -> dict[str,dict[str,str]]:
    """Reject duplicate identity instead of silently replacing a composition."""
    result: dict[str,dict[str,str]] = {}
    for r in rows:
        cid=str(r.get('candidate_id') or '').strip()
        if not cid: raise ValueError('Geometry candidate_id missing')
        if cid in result: raise ValueError(f'Duplicate geometry candidate_id: {cid}')
        result[cid] = r
    return result


def _checked(row: Mapping[str,object], status_key: str, value_key: str, *,
             nonnegative: bool = False) -> float | None:
    status=str(row.get(status_key) or '').lower().strip()
    if status not in ('success','completed','valid','ok'): return None
    n=_number(row.get(value_key))
    return n if n is not None and (not nonnegative or n>=0) else None


def assess_candidate(row: Mapping[str,object], target_um: float,
                     geometry: Mapping[str,object] | None = None, *,
                     data_origin: str = '工程结果') -> dict[str,object]:
    target=_number(target_um)
    if target is None or target<=0: raise ValueError('目标波长须为正的有限数值（μm）')
    candidate_id=str(row.get('recommendation_id') or row.get('candidate_id') or row.get('pair_index') or '未编号')
    x=_number(row.get('actual_fraction_b'))
    if x is None: x=_number(row.get('target_fraction_b'))
    if x is not None and not 0 <= x <= 1: x=None
    gap_a=_number(row.get('gap_a_eV'))
    gap_b=_number(row.get('gap_b_eV'))
    if gap_a is not None and gap_a < 0: gap_a=None
    if gap_b is not None and gap_b < 0: gap_b=None
    target_gap=PHOTON_ENERGY_EV_UM/target
    if gap_a is not None and gap_b is not None:
        endpoint_gap_min=min(gap_a,gap_b)
        endpoint_gap_max=max(gap_a,gap_b)
        band_match=(
            '端元范围覆盖'
            if endpoint_gap_min <= target_gap <= endpoint_gap_max
            else '端元范围未覆盖'
        )
    else:
        endpoint_gap_min=endpoint_gap_max=None
        band_match='端元带隙缺失'
    gap=None;gap_origin='缺少直接合金带隙'
    for key in ('alloy_gap_eV','gap_alloy_eV','band_gap_eV'):
        n=_number(row.get(key))
        if n is not None and n>0:
            gap=n;gap_origin=f'输入合金带隙（{key}，仍需核验来源与QC）';break
    geom=geometry or {}
    # Geometry results are joined by explicit candidate identity and actual composition.
    linked=bool(geom)
    gx=_number(geom.get('actual_fraction_b'))
    if linked and (gx is None or x is None or abs(gx-x)>1e-6):
        raise ValueError(f'{candidate_id}: geometry actual_fraction_b mismatch')
    if linked and str(geom.get('candidate_id')) != candidate_id:
        raise ValueError(f'{candidate_id}: geometry candidate_id mismatch')
    if linked and str(geom.get('gap_status') or '') == '有效' and _number(geom.get('gap_eV')) is not None and _number(geom.get('gap_eV')) > 0:
        gap = _number(geom['gap_eV'])
        gap_origin = '已有合金构型带隙（几何评价表已核对双构型结构SHA与QC）'
    phonon=_checked(row,'phonon_status','minimum_mesh_frequency_THz')
    mixing=_checked(row,'mixing_status','mixing_enthalpy_meV_per_atom')
    hull=_checked(row,'phase_status','energy_above_hull_eV_per_atom',nonnegative=True)
    # Stage 12 rows carry one structure; two-configuration aggregates from the
    # geometry evaluator take precedence only when explicitly valid.
    def gnumber(key: str) -> float | None:
        return _number(geom.get(key)) if linked else None
    def display(key: str, fallback: object = None) -> object:
        value=geom.get(key) if linked else None
        return value if value not in (None,'') else fallback
    result: dict[str,object] = {
        'candidate_id':candidate_id,'pair_index':row.get('pair_index',''),
        'comp_a':row.get('comp_a',''),'comp_b':row.get('comp_b',''),
        'fraction_b':x,'gap_a_eV':gap_a,'gap_b_eV':gap_b,
        'endpoint_gap_min_eV':endpoint_gap_min,'endpoint_gap_max_eV':endpoint_gap_max,
        'alloy_gap_eV':gap,'gap_origin':gap_origin,
        'gap_equivalent_wavelength_um':PHOTON_ENERGY_EV_UM/gap if gap else None,
        'endpoint_gap_min_eV':endpoint_gap_min,
        'endpoint_gap_max_eV':endpoint_gap_max,
        'target_um':target,'target_gap_eV':target_gap,'band_match':band_match,
        'lattice_mismatch_pct':gnumber('lattice_mismatch_pct'),
        'lattice_status':display('lattice_status','待补充'),
        'phonon_min_THz':gnumber('phonon_min_THz') if gnumber('phonon_min_THz') is not None else phonon,
        'phonon_status':display('phonon_status', '待补充' if phonon is None else '需结合双构型核验'),
        'mixing_enthalpy_meV_atom':gnumber('mixing_enthalpy_meV_atom') if gnumber('mixing_enthalpy_meV_atom') is not None else mixing,
        'mixing_status':display('mixing_status','待补充' if mixing is None else '需结合双构型核验'),
        'energy_above_hull_meV_atom':gnumber('energy_above_hull_meV_atom') if gnumber('energy_above_hull_meV_atom') is not None else (hull*1000 if hull is not None else None),
        'hull_status':display('hull_status','待补充' if hull is None else '需结合双构型核验'),
        'substrate_principal_strain_pct':gnumber('substrate_principal_strain_pct'),
        'substrate_status':display('substrate_status','待补充'),
        'substrate_id':display('substrate_id',''),
        'substrate_recommendations':'',
        'film_miller':display('film_miller',''),
        'substrate_miller':display('substrate_miller',''),
        'match_area_A2':gnumber('match_area_A2'),
        'match_id':display('match_id',''),
        'candidate_grade':display('candidate_grade','待补充'),
        'geometry_grade':display('geometry_grade','几何数据待补充'),
        'evidence_completeness':display('evidence_completeness','部分缺失'),
        'source_structure_id':row.get('structure_id',''),
        'data_origin':data_origin,
        'caution':'材料级预筛；端元带隙范围覆盖仅表示目标光子能量落在两端元带隙之间，不证明合金带隙单调变化或实际探测响应。单seed衬底几何不证明实际外延。',
    }
    # Stage 13's candidate priority is the requested endpoint-gap-range rule.
    # Keep every pair in the table: covered pairs are priority candidates;
    # uncovered or incomplete endpoint evidence remains visible as secondary.
    result['candidate_grade'] = '优先' if band_match == '端元范围覆盖' else '次优'
    # Endpoint range is a pair-level screening estimate, never an alloy-gap
    # interpolation. A direct alloy gap remains a separate evidence field.
    if data_origin.startswith('内置演示'):
        result['candidate_grade']='演示数据（不可评级）'
    return result


def assess_rows(rows: list[Mapping[str,object]], target_um: float,
                geometry: Mapping[str,Mapping[str,object]] | None = None,
                *,data_origin: str='工程结果') -> list[dict[str,object]]:
    """Group Stage 12 by pair + actual x and join geometry only by explicit key.

    Stage 12 recommendation_id is *per structure*, so it must not be used as
    the sole identity for a pair + composition. A geometry record can bind via
    stage12_pair_index or exactly matching candidate ID, never by row index.
    """
    geometry_rows=list((geometry or {}).values())
    grouped: dict[tuple[str,str],list[Mapping[str,object]]] = {}
    for r in rows:
        pair=str(r.get('pair_index') or '').strip()
        x=_number(r.get('actual_fraction_b'))
        if x is None:x=_number(r.get('target_fraction_b'))
        if pair and x is not None:
            key=(pair,f'{x:.8f}')
        else:
            # Unknown identity is preserved as a standalone row, never merged.
            key=('__unmapped__',str(r.get('recommendation_id') or r.get('candidate_id') or len(grouped)))
        grouped.setdefault(key,[]).append(r)
    used: set[tuple[str,str]] = set()
    result=[]
    for g in geometry_rows:
        pair=str(g.get('stage12_pair_index') or '').strip()
        x=_number(g.get('actual_fraction_b'))
        key=(pair,f'{x:.8f}') if pair and x is not None else None
        if key is not None:
            if key in used: raise ValueError(f'duplicate stage12_pair_index + fraction mapping: {key}')
            members=grouped.get(key,[])
            used.add(key)
        else:
            # Only permit exact candidate_id/recommendation_id when no pair map.
            members=[r for r in rows if str(r.get('recommendation_id') or r.get('candidate_id') or '')==str(g.get('candidate_id'))]
        source=dict(members[0]) if members else {}
        source.update({
            'recommendation_id':g.get('candidate_id'),
            'pair_index':pair or source.get('pair_index',''),
            'actual_fraction_b':g.get('actual_fraction_b'),
            'comp_a':g.get('comp_a') or source.get('comp_a',''),
            'comp_b':g.get('comp_b') or source.get('comp_b',''),
        })
        result.append(assess_candidate(source,target_um,g,data_origin=data_origin))
    for key,members in grouped.items():
        if key in used:continue
        source=dict(members[0])
        # Do not claim two valid configurations merely because two rows exist;
        # the required expected_structure_ids / QC / SHA come from manifests.
        assessed=assess_candidate(source,target_um,data_origin=data_origin)
        assessed['caution']+=f' Stage12同组记录数：{len(members)}；尚需完整构型身份与QC核验。'
        result.append(assessed)
    return result


def export_rows(path: Path, rows: list[dict[str,object]]) -> None:
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=OUTPUT_COLUMNS,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)


DEMO_ROWS: tuple[dict[str,str],...]=(
    {'recommendation_id':'DEMO-001','pair_index':'1','comp_a':'演示端元A','comp_b':'演示端元B','gap_a_eV':'0.38','gap_b_eV':'0.72','target_fraction_b':'0.5'},
    {'recommendation_id':'DEMO-002','pair_index':'2','comp_a':'演示端元C','comp_b':'演示端元D','gap_a_eV':'0.13','gap_b_eV':'0.23','target_fraction_b':'0.3'},
    {'recommendation_id':'DEMO-003','pair_index':'3','comp_a':'演示端元E','comp_b':'演示端元F','gap_a_eV':'1.6','gap_b_eV':'2.0','target_fraction_b':'0.7'},
)
