"""Manifest evidence integrity, offline output, and conservative error handling."""
from pathlib import Path
import json
import csv

import numpy as np
import pytest
from ssscreen.geometry_pipeline import _config,_effective_supercell_matrix,evaluate
from ssscreen.detector import assess_rows,index_geometry,read_csv

FIXTURES=Path(__file__).parent/'data'/'stage13_geometry'


def test_effective_supercell_matrix_reconstructs_reduced_zsl_basis():
    base=np.array([[4.,0.,0.],[0.,4.,0.]])
    # The returned ZSL basis can differ from its original area-multiple matrix
    # after the Zur reduction swaps vectors or adds/subtracts one row.
    reduced=np.array([[2,2],[0,2]])@base
    transform=_effective_supercell_matrix(base,reduced)
    assert np.array_equal(transform,[[2,2],[0,2]])
    assert np.allclose(transform@base,reduced)


def test_offline_pipeline_never_invents_geometry(tmp_path):
    out=tmp_path/'output'
    summary=evaluate(FIXTURES/'input',FIXTURES/'config.json',out)
    assert summary['candidate_count']==1
    main=read_csv(out/'candidate_evaluation.csv')[0]
    assert main['selected_structure_id']=='syn-101'
    assert main['available_configurations']=='2'
    assert main['phonon_min_THz']=='0.1'
    assert main['mixing_enthalpy_meV_atom']=='18.0'
    assert main['energy_above_hull_meV_atom']=='12.0'
    assert main['gap_status']=='有效'
    assert 'seed202' not in (main.get('selected_structure_id') or '')
    assert '晶格常数匹配（新增）' in (out/'report.md').read_text()
    for filename in ('lattice_matches.csv','substrate_top_matches.csv','structure_matches.csv','match_details.jsonl.gz','summary.json'):
        assert (out/filename).is_file()
    if main['substrate_principal_strain_pct']:
        assert main['match_id']
    else:
        assert main['candidate_grade']!='优先进一步验证'


def test_explicit_stage12_pair_and_x_join():
    result=[{'candidate_id':'XYZ','stage12_pair_index':'4','actual_fraction_b':'0.5',
             'gap_eV':'0.4','gap_status':'有效','candidate_grade':'待补充'}]
    stage12=[{'recommendation_id':'per-structure-1','pair_index':'4','actual_fraction_b':'0.5',
              'structure_id':'s101'},
             {'recommendation_id':'per-structure-2','pair_index':'4','actual_fraction_b':'0.5',
              'structure_id':'s202'}]
    assessed=assess_rows(stage12,2.0,index_geometry(result))
    assert len(assessed)==1
    assert assessed[0]['candidate_id']=='XYZ'
    assert assessed[0]['gap_eV']==0.4


def test_config_rejects_unsupported_substitution(tmp_path):
    config={'schema_version':2,'substrate':{'allow_automatic_seed_fallback':True}}
    path=tmp_path/'bad.json';path.write_text(json.dumps(config),encoding='utf-8')
    with pytest.raises(ValueError,match='fallback'):_config(path)


def test_missing_gap_target_has_pending_grade(tmp_path):
    config={'schema_version':2}
    path=tmp_path/'unset.json';path.write_text(json.dumps(config))
    assert _config(path)['gap_target_eV'] is None
