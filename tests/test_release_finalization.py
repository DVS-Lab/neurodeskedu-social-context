import ast
import csv
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import zipfile

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from prepare_public_maps import archive_maps,MAPPING
from finalize_public_release import finalize,sha256,TEMPLATE_SHA256
from test_public_export import image_fixture


def staged(tmp_path):
    _,mask,metadata,row=image_fixture(tmp_path)
    meta=json.loads(metadata.read_text()); meta['template_sha256']=TEMPLATE_SHA256
    metadata.write_text(json.dumps(meta))
    rows=[]
    for task,conditions in MAPPING.items():
        for k,partner,valence,name in conditions:
            rows.append(dict(row,task=task,partner=partner,valence=valence,contrast_index=k,contrast_name=name))
    archive_maps(tmp_path/'stage',rows,{'participant_ids':[]},mask,metadata,{'source_doi':'test'})
    return tmp_path/'stage/public_outcome_copes.zip'


def test_final_archive_omits_template_and_preserves_all_map_and_manifest_bytes(tmp_path):
    source=staged(tmp_path); old_hash=sha256(source)
    result=finalize(source,tmp_path/'final.zip',old_hash)
    assert sha256(source)==old_hash
    assert result['n']==1 and result['outcome_maps']==12 and result['archive_entries']==16
    assert result['cope_and_manifest_bytes_unchanged'] and not result['third_party_template_files_included']
    with zipfile.ZipFile(source) as old,zipfile.ZipFile(tmp_path/'final.zip') as new:
        assert 'mask.nii.gz' not in new.namelist()
        for name in new.namelist():
            if name.startswith('maps/') or name=='manifest.csv': assert new.read(name)==old.read(name)
        meta=json.loads(new.read('dataset_description.json'))
        assert meta['License']=='CC0-1.0' and meta['MaskDistribution']=='external_reference_only'
        assert 'expected_resampled_mask_data_sha256' in meta['MaskProvenance']
        assert b'staged, unreviewed' not in new.read('README')


def test_finalizer_stops_on_changed_candidate_or_extra_files(tmp_path):
    source=staged(tmp_path); old_hash=sha256(source)
    with zipfile.ZipFile(source,'a') as z:z.writestr('private_records.json','{}')
    with pytest.raises(ValueError,match='checksum differs'):finalize(source,tmp_path/'final.zip',old_hash)
    with pytest.raises(ValueError,match='Unexpected'):finalize(source,tmp_path/'final.zip',sha256(source))
    assert not (tmp_path/'final.zip').exists()


def test_notebook_reconstructs_only_the_pinned_reference_and_checks_voxel_hash(tmp_path,monkeypatch):
    notebook=json.loads((ROOT/'Cross_task_decoding.ipynb').read_text())
    cell=next(''.join(c['source']) for c in notebook['cells'] if 'def reconstruct_external_mask' in ''.join(c['source']))
    functions=[node for node in ast.parse(cell).body if isinstance(node,ast.FunctionDef) and node.name in ('sha256','reconstruct_external_mask')]
    namespace=dict(Path=Path,json=json,hashlib=hashlib,nib=nib,np=np,pd=pd,urllib=__import__('urllib'),DATA_DIR=tmp_path/'cache')
    exec(compile(ast.Module(body=functions,type_ignores=[]),'notebook_functions','exec'),namespace)
    bundle=tmp_path/'bundle';bundle.mkdir(); values=np.ones((2,3,4),dtype='uint8')
    cache=namespace['DATA_DIR'];cache.mkdir();temp=cache/'template.nii.gz'
    nib.save(nib.Nifti1Image(values,np.eye(4)),temp); h=sha256(temp);temp.rename(cache/f'template-{h}.nii.gz')
    nib.save(nib.Nifti1Image(np.zeros((2,3,4),dtype='float32'),np.eye(4)),bundle/'reference.nii.gz')
    (bundle/'manifest.csv').write_text('path\nreference.nii.gz\n')
    from finalize_public_release import TEMPLATE_URL
    metadata=dict(MaskDistribution='external_reference_only',MaskProvenance=dict(template_download_url=TEMPLATE_URL,
        template_sha256=h,expected_resampled_mask_data_sha256=hashlib.sha256(values.tobytes()).hexdigest()))
    (bundle/'dataset_description.json').write_text(json.dumps(metadata))
    monkeypatch.setattr(urllib.request,'urlopen',lambda *a,**k:pytest.fail('Pinned cached reference should not need a network request'))
    namespace['reconstruct_external_mask'](bundle)
    np.testing.assert_equal(nib.load(bundle/'mask.nii.gz').get_fdata(),values)
    metadata['MaskProvenance']['expected_resampled_mask_data_sha256']='0'*64
    (bundle/'dataset_description.json').write_text(json.dumps(metadata))
    with pytest.raises(AssertionError):namespace['reconstruct_external_mask'](bundle)
