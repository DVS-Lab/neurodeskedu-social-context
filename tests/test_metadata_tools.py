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


def notebook_cell(marker):
    import nbformat
    notebook = nbformat.read(ROOT / 'Cross_task_decoding.ipynb', as_version=4)
    return next(c.source for c in notebook.cells if c.cell_type == 'code' and marker in c.source)


def test_notebook_runs_as_a_self_contained_module_example_without_installation():
    import ast, nbformat
    from IPython.core.inputtransformer2 import TransformerManager
    notebook = nbformat.read(ROOT / 'Cross_task_decoding.ipynb', as_version=4)
    nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type != 'code':
            continue
        ast.parse(TransformerManager().transform_cell(cell.source))
        assert len(cell.source.splitlines()) < 60
        assert not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                       for node in ast.walk(ast.parse(TransformerManager().transform_cell(cell.source))))
        assert 'pip install' not in cell.source and 'venv' not in cell.source
        assert 'data_release.json' not in cell.source
    first = next(c.source for c in notebook.cells if c.cell_type == 'code')
    assert 'await module.load("fsl/6.0.7.22")' in first
    pinned = json.loads((ROOT / 'data_release.json').read_text())
    release_cell = notebook_cell('archive_sha =')
    assert pinned['archive_sha256'] in release_cell and pinned['archive_url'] in release_cell
    assert pinned['status'] == 'published' and all(pinned['membership_audit'].values())


def test_corrupted_cache_stops_before_extraction_or_network(tmp_path, monkeypatch):
    import hashlib, urllib.request, zipfile
    cache = tmp_path / 'bad.zip'
    cache.write_bytes(b'corrupted')
    resources = [dict(name='test maps', path=cache, sha256='0' * 64, url='https://example.org/data')]
    monkeypatch.setattr(urllib.request, 'urlretrieve', lambda *a: pytest.fail('Corrupt cache must stop'))
    namespace = dict(Path=Path, hashlib=hashlib, urllib=__import__('urllib'), zipfile=zipfile,
                     resources=resources, DATA_DIR=tmp_path, archive_sha='0' * 64)
    with pytest.raises(AssertionError, match='Cached file changed'):
        exec(notebook_cell('# Download and verify each file'), namespace)
    assert not list(tmp_path.glob('public-*'))


def test_wrong_download_is_not_promoted_or_extracted(tmp_path, monkeypatch):
    import hashlib, urllib.request, zipfile
    cache = tmp_path / 'maps.zip'
    resources = [dict(name='test maps', path=cache, sha256='0' * 64, url='https://example.org/data')]
    monkeypatch.setattr(urllib.request, 'urlretrieve', lambda url, path: path.write_bytes(b'wrong bytes'))
    namespace = dict(Path=Path, hashlib=hashlib, urllib=__import__('urllib'), zipfile=zipfile,
                     resources=resources, DATA_DIR=tmp_path, archive_sha='0' * 64)
    with pytest.raises(AssertionError, match='Download checksum mismatch'):
        exec(notebook_cell('# Download and verify each file'), namespace)
    assert not cache.exists() and not list(tmp_path.glob('public-*'))


def test_archive_cannot_extract_outside_release_directory(tmp_path):
    import hashlib, urllib.request, zipfile
    cache = tmp_path / 'maps.zip'
    with zipfile.ZipFile(cache, 'w') as archive:
        archive.writestr('../outside.txt', b'bad path')
    checksum = hashlib.sha256(cache.read_bytes()).hexdigest()
    resources = [dict(name='test maps', path=cache, sha256=checksum)]
    namespace = dict(Path=Path, hashlib=hashlib, urllib=__import__('urllib'), zipfile=zipfile,
                     resources=resources, DATA_DIR=tmp_path, archive_sha=checksum)
    with pytest.raises(AssertionError):
        exec(notebook_cell('# Download and verify each file'), namespace)
    assert not (tmp_path / 'outside.txt').exists()
