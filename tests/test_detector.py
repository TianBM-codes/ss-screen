"""Stage 13 no fabricated device metrics and strict geometry identity joins."""
import pytest
from ssscreen.detector import assess_candidate, assess_rows, export_rows, read_csv, index_geometry, DEMO_ROWS


def test_demo_gap_only_and_missing_geometry(tmp_path):
    rows=assess_rows(list(DEMO_ROWS),2.0,data_origin='内置演示（非真实材料）')
    assert len(rows)==3
    assert rows[0]['gap_eV']==pytest.approx(.55)
    assert rows[0]['gap_equivalent_wavelength_um']==pytest.approx(1.239841984/.55)
    assert rows[0]['phonon_min_THz'] is None
    assert rows[0]['mixing_enthalpy_meV_atom'] is None
    assert rows[0]['substrate_principal_strain_pct'] is None
    assert '演示数据' in rows[0]['candidate_grade']
    path=tmp_path/'stage13.csv';export_rows(path,rows)
    saved=read_csv(path)
    assert 'responsivity_A_W' not in saved[0]
    assert 'lattice_mismatch_pct' in saved[0]


def test_conservative_status_and_conversion():
    result=assess_candidate({'recommendation_id':'C1','actual_fraction_b':'0.5',
        'mixing_status':'success','mixing_enthalpy_meV_per_atom':'12',
        'phonon_status':'success','minimum_mesh_frequency_THz':'-0.03',
        'phase_status':'success','energy_above_hull_eV_per_atom':'0.015'},2.0)
    assert result['mixing_enthalpy_meV_atom']==12
    assert result['phonon_min_THz']==-.03
    assert result['energy_above_hull_meV_atom']==15
    assert result['candidate_grade']=='待补充'


def test_geometry_matches_exact_id_and_composition():
    data={'candidate_id':'C1','actual_fraction_b':'0.5','lattice_mismatch_pct':'1.98',
          'phonon_min_THz':'0.12','mixing_enthalpy_meV_atom':'20',
          'energy_above_hull_meV_atom':'10','substrate_principal_strain_pct':'0.9',
          'candidate_grade':'优先进一步验证','geometry_grade':'几何优先'}
    result=assess_candidate({'recommendation_id':'C1','target_fraction_b':'0.5',
                             'alloy_gap_eV':'0.4'},2.0,data)
    assert result['lattice_mismatch_pct']==1.98
    assert result['substrate_principal_strain_pct']==.9
    with pytest.raises(ValueError,match='fraction'):
        assess_candidate({'recommendation_id':'C1','target_fraction_b':'0.3'},2.0,data)
    with pytest.raises(ValueError,match='Duplicate'):
        index_geometry([data,data])


def test_not_upgrade_endmember_interpolation():
    data={'candidate_id':'C2','actual_fraction_b':'0.5','candidate_grade':'优先进一步验证'}
    r=assess_candidate({'recommendation_id':'C2','gap_a_eV':'.4','gap_b_eV':'.6',
                        'actual_fraction_b':'.5'},2.0,data)
    assert r['candidate_grade']=='待补充'


def test_nonfinite_and_zero_gap():
    for bad in (0,-1,float('nan'),float('inf')):
        with pytest.raises(ValueError):assess_candidate({},bad)
    assert assess_candidate({'alloy_gap_eV':'0'},2)['gap_eV'] is None
