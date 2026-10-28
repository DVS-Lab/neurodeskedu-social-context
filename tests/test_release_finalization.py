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


def test_notebook_reconstructs_the_pinned_mask_and_stops_on_wrong_voxel_hash(tmp_path):
    from nibabel.processing import resample_from_to
    notebook = json.loads((ROOT / 'Cross_task_decoding.ipynb').read_text())
    source = next(''.join(c['source']) for c in notebook['cells']
                  if c['cell_type'] == 'code' and 'resampled_mask =' in ''.join(c['source']))
    values = np.zeros((57, 70, 54), dtype='uint8')
    values.ravel()[:84479] = 1
    mask_path = tmp_path / 'template.nii.gz'
    reference_path = tmp_path / 'reference.nii.gz'
    nib.save(nib.Nifti1Image(values, np.eye(4)), mask_path)
    nib.save(nib.Nifti1Image(np.zeros_like(values, dtype='float32'), np.eye(4)), reference_path)
    metadata = dict(MaskDistribution='external_reference_only', MaskProvenance=dict(
        expected_resampled_mask_data_sha256=hashlib.sha256(values.tobytes()).hexdigest()))
    (tmp_path / 'dataset_description.json').write_text(json.dumps(metadata))
    namespace = dict(nib=nib, np=np, json=json, hashlib=hashlib, resample_from_to=resample_from_to,
                     example_path=reference_path, RELEASE_DIR=tmp_path,
                     resources=[{}, dict(path=mask_path), dict(path=reference_path)])
    exec(source, namespace)
    np.testing.assert_equal(namespace['mask_values'], values)
    metadata['MaskProvenance']['expected_resampled_mask_data_sha256'] = '0' * 64
    (tmp_path / 'dataset_description.json').write_text(json.dumps(metadata))
    with pytest.raises(AssertionError):
        exec(source, namespace)
