import copy
import csv
import importlib.util
import itertools
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def fixtures():
    rows=[dict(participant_id='sub-public001',task=t,partner=p,valence=v,phase='outcome',
               source_dataset='ds005123',source_version='1.0.0',qc_included='true',byte_size=1000,
               source_path='/must/not/be/opened.nii.gz')
          for t,p,v in itertools.product(('sharedreward','trust'),('computer','friend','stranger'),('positive','negative'))]
    protected=dict(complete=True,covers=['sealed_N50','external_validation'],participant_ids=['sub-protected001'])
    return [{'participant_id':'sub-public001'}],rows,protected


def test_size_arithmetic_and_manifest_sum_never_open_image_paths(tmp_path):
    mod=load('estimate_release_size'); x=mod.estimates()
    assert x[1]['total_maps']==1368 and x[1]['total_bytes']==1179478656
    assert x[2]['total_bytes']==2*x[1]['total_bytes']
    assert mod.estimates(57)[1]['total_bytes']==x[1]['total_bytes']//2
    table=tmp_path/'manifest.csv'; table.write_text('path,byte_size\n/forbidden/sealed.nii.gz,700\n/no-such-file.nii.gz,300\n')
    assert mod.measured_manifest(table)['total_bytes']==1000


def test_metadata_guard_accepts_complete_public_only_plan_without_images():
    mod=load('check_export_plan'); public,rows,protected=fixtures()
    result=mod.check(public,rows,protected)
    assert result['n']==1 and result['map_count']==12 and result['total_recorded_map_bytes']==12000
    assert not result['participant_images_opened'] and not result['ready_to_publish']


def test_metadata_guard_rejects_reserved_or_nonpublic_people():
    mod=load('check_export_plan'); public,rows,protected=fixtures()
    protected['participant_ids'].append('sub-public001')
    with pytest.raises(ValueError,match='protected validation'): mod.check(public,rows,protected)
    protected['participant_ids']=[]
    with pytest.raises(ValueError,match='outside'): mod.check([{'participant_id':'sub-other'}],rows,protected)
    protected['covers']=['external_validation']
    with pytest.raises(ValueError,match='complete curator'): mod.check(public,rows,protected)


def test_metadata_guard_rejects_incomplete_duplicate_and_ineligible_maps():
    mod=load('check_export_plan'); public,rows,protected=fixtures()
    with pytest.raises(ValueError,match='12 complete'): mod.check(public,rows[:-1],protected)
    with pytest.raises(ValueError,match='duplicate'): mod.check(public,rows+[rows[0]],protected)
    for field,value in [('phase','fulltrial'),('source_version','latest'),('qc_included','false'),('byte_size','0')]:
        changed=copy.deepcopy(rows); changed[0][field]=value
        with pytest.raises(ValueError): mod.check(public,changed,protected)


def test_notebook_code_parses_and_defaults_to_the_published_public_release():
    import ast,nbformat
    nb=nbformat.read(ROOT/'Cross_task_decoding.ipynb',as_version=4)
    nbformat.validate(nb)
    for cell in nb.cells:
        if cell.cell_type=='code':
            ast.parse(cell.source)
            assert len(cell.source.splitlines())<100
    first=next(c.source for c in nb.cells if c.cell_type=='code')
    assert 'MODE = "public"' in first
    assert nb.metadata.neurodeskedu_draft.no_real_participant_data_packaged is True
    config=json.loads((ROOT/'data_release.json').read_text())
    assert config['status']=='published' and config['expected_n']==67
    assert config['derivative_doi']=='10.5281/zenodo.23718599'
    assert '23718599' in config['archive_url'] and len(config['archive_sha256'])==64
    assert all(config['membership_audit'].values())


def test_public_mode_stops_before_network_when_release_unpublished():
    import ast,nbformat
    nb=nbformat.read(ROOT/'Cross_task_decoding.ipynb',as_version=4)
    source=next(c.source for c in nb.cells if c.cell_type=='code' and 'def public_release' in c.source)
    namespace={}; exec(compile(ast.parse(source),'<notebook download helpers>','exec'),namespace)
    config=json.loads((ROOT/'data_release.json').read_text())
    config['status']='draft_not_published'
    with pytest.raises(AssertionError,match='Publish and review'):
        namespace['public_release'](config)


def test_public_loader_rejects_a_corrupted_cache_before_extraction(tmp_path,monkeypatch):
    import ast,hashlib,stat,urllib.request,zipfile
    nb=json.loads((ROOT/'Cross_task_decoding.ipynb').read_text())
    source=next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code' and 'def public_release' in ''.join(c['source']))
    namespace=dict(Path=Path,hashlib=hashlib,urllib=__import__('urllib'),stat=stat,zipfile=zipfile,DATA_DIR=tmp_path,N_FOLDS=5)
    exec(compile(ast.parse(source),'<notebook download helpers>','exec'),namespace)
    config=json.loads((ROOT/'data_release.json').read_text())
    (tmp_path/(config['archive_sha256']+'.zip')).write_bytes(b'corrupted download')
    monkeypatch.setattr(urllib.request,'urlopen',lambda *a,**k:pytest.fail('Existing corrupt cache must stop, not download or fall back'))
    with pytest.raises(AssertionError,match='Cached archive changed'):
        namespace['public_release'](config)
    assert not list(tmp_path.glob('public-*'))


def test_public_loader_requires_all_audit_attestations_before_network(tmp_path):
    import ast
    nb=json.loads((ROOT/'Cross_task_decoding.ipynb').read_text())
    source=next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code' and 'def public_release' in ''.join(c['source']))
    namespace=dict(N_FOLDS=5)
    exec(compile(ast.parse(source),'<notebook download helpers>','exec'),namespace)
    config=json.loads((ROOT/'data_release.json').read_text())
    config['membership_audit']['sealed_N50_excluded']=False
    with pytest.raises(AssertionError,match='Curator membership/QC audit'):
        namespace['public_release'](config)
