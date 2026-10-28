import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import nibabel as nib
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from prepare_public_maps import protected_union,archive_maps,sha256


def make_paper(tmp_path):
    root=tmp_path/'paper'
    original=[f'sub-{i:05d}' for i in range(50)]
    supplemental=[f'sub-{i:05d}' for i in range(50,62)]
    split=root/'work/splits/subject_split_v1.tsv'; split.parent.mkdir(parents=True)
    split.write_text('subject\tsplit\n'+''.join(s+'\tholdout\n' for s in original)+'sub-00999\tdevelopment\n')
    manifest=root/'work/revised/samples/manifest.tsv'; manifest.parent.mkdir(parents=True)
    # Repeated cohorts/policies are legitimate. Original holdouts with failed QC remain protected.
    manifest.write_text('subject\tpartition\teligible\n'+''.join(s+'\tholdout\tFalse\n' for s in original+supplemental)+
                        ''.join(s+'\tholdout\tTrue\n' for s in original+supplemental)+'sub-00999\tdevelopment\tTrue\n')
    old=root/'provenance/subject_split_v1.json'; old.parent.mkdir(parents=True); old.write_text(json.dumps({'sha256':sha256(split)}))
    revised=root/'provenance/revised/samples/samples.json'; revised.parent.mkdir(parents=True)
    revised.write_text(json.dumps(dict(original_split_sha256=sha256(split),manifest_sha256=sha256(manifest),
            protected_holdout_total_n=62,original_holdout_redrawn=False,holdout_scored=False)))
    return root,original,supplemental


def test_original_and_supplemental_holdouts_retained_even_when_qc_failed(tmp_path):
    root,original,supplemental=make_paper(tmp_path)
    held=protected_union(root,no_additional=True)
    assert held['paper_protected_n']==62 and set(held['participant_ids'])==set(original+supplemental)
    public=set(original[:11]+supplemental[:3]+['sub-00999'])
    assert len(public&set(held['participant_ids']))==14 and len(public-set(held['participant_ids']))==1
    assert held['original_n']==50 and len(held['supplemental_participant_ids'])==12


def test_missing_or_changed_membership_and_ambiguous_external_scope_stop(tmp_path):
    root,_,_=make_paper(tmp_path)
    with pytest.raises(ValueError,match='external exclusion'): protected_union(root)
    path=root/'work/revised/samples/manifest.tsv'; path.write_text(path.read_text()+'sub-00000\tdevelopment\tTrue\n')
    with pytest.raises(ValueError,match='fingerprint'): protected_union(root,no_additional=True)
    with pytest.raises(ValueError,match='unavailable'): protected_union(tmp_path/'missing',no_additional=True)


def test_complete_external_file_is_unioned_with_full_paper_pool(tmp_path):
    root,_,_=make_paper(tmp_path); path=tmp_path/'external.json'
    path.write_text(json.dumps(dict(complete=True,dataset_namespace='rf1-sra',participant_ids=['sub-88888'])))
    held=protected_union(root,external=path)
    assert len(held['participant_ids'])==63 and 'sub-88888' in held['participant_ids']
    with pytest.raises(ValueError,match='OR explicit'): protected_union(root,external=path,no_additional=True)


def image_fixture(tmp_path):
    person='sub-00999'; path=tmp_path/'sources'/person/'ses-01/stats/cope1.nii.gz'; path.parent.mkdir(parents=True)
    image=nib.Nifti1Image(np.linspace(-3,2,24,dtype='float32').reshape(2,3,4),np.eye(4))
    image.header['descrip']=b'private person details'; image.header['aux_file']=b'private aux'; image.header['db_name']=b'private db'
    nib.save(image,path)
    mask=tmp_path/'independent_mask.nii.gz'; nib.save(nib.Nifti1Image(np.ones((2,3,4),dtype='uint8'),np.eye(4)),mask)
    meta=tmp_path/'mask.json'; meta.write_text(json.dumps(dict(kind='independent_template',source_url='https://example.org/fixed-mask',description='Synthetic test reference',sha256=sha256(mask))))
    row=dict(participant_id=person,task='sharedreward',partner='computer',valence='negative',phase='outcome',
             source_dataset='ds005123',source_version='1.0.0',qc_included='true',contrast_name='C_pun',contrast_index=1,
             contrast_weights='EV1=+1',retained_runs='1',run_strategy='l1_passthrough',
             source_path=str(path),source_sha256=sha256(path),byte_size=path.stat().st_size)
    return path,mask,meta,row


def test_archive_checks_guard_before_reading_source_voxels(tmp_path,monkeypatch):
    path,mask,meta,row=image_fixture(tmp_path)
    real=nib.load
    def guarded(p,*args,**kwargs):
        assert Path(p)!=path,'Protected image was opened'
        return real(p,*args,**kwargs)
    monkeypatch.setattr(nib,'load',guarded)
    with pytest.raises(ValueError,match='Protected participant'):
        archive_maps(tmp_path/'out',[row],{'participant_ids':[row['participant_id']]},mask,meta,{'source_doi':'test'})


def test_archive_preserves_signed_effects_sanitizes_headers_and_hides_sources(tmp_path):
    path,mask,meta,row=image_fixture(tmp_path); original=sha256(path)
    result=archive_maps(tmp_path/'out',[row],{'participant_ids':[]},mask,meta,{'source_doi':'test'})
    assert not result['ready_to_publish'] and result['map_files']==1
    assert sha256(path)==original
    files=list((tmp_path/'out/bundle/maps').glob('*.nii.gz')); image=nib.load(files[0]); source=nib.load(path)
    np.testing.assert_equal(image.get_fdata(),source.get_fdata())
    for field in ('aux_file','db_name'): assert not image.header[field].tobytes().strip(b'\x00')
    assert b'private' not in image.header['descrip'].tobytes()
    manifest=(tmp_path/'out/bundle/manifest.csv').read_text()
    assert str(path) not in manifest and 'source_path' not in manifest and 'source_sha256' not in manifest
    assert (tmp_path/'out/public_outcome_copes.zip').is_file()


def test_overlap_cli_only_reads_metadata_and_reports_no_ids(tmp_path,monkeypatch,capsys):
    import prepare_public_maps as impl
    paper,original,supplemental=make_paper(tmp_path)
    root=tmp_path/'tutorial'; (root/'config').mkdir(parents=True)
    public=root/'work/public_release/participants.tsv'; public.parent.mkdir(parents=True)
    public_ids=original[:11]+supplemental[:3]+['sub-00999']
    public.write_text('participant_id\n'+'\n'.join(public_ids)+'\n')
    metadata=('provenance/subject_split_v1.json','provenance/revised/samples/samples.json')
    contract=dict(paper_metadata={p:sha256(paper/p) for p in metadata},public_participants_sha256=sha256(public),public_participants_n=15)
    (root/'config/source_contract.json').write_text(json.dumps(contract))
    monkeypatch.setattr(impl,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['prepare_public_maps.py','--paper-root',str(paper),'--projects-root',str(tmp_path),'--no-additional-external-validation','--stage','overlap','--output',str(root/'work/overlap')])
    monkeypatch.setattr(impl,'source_scope',lambda *a:pytest.fail('Overlap stage accessed scientific source adapters'))
    monkeypatch.setattr(nib,'load',lambda *a:pytest.fail('Overlap stage loaded an image'))
    assert impl.main()==0
    text=capsys.readouterr().out
    assert 'sub-' not in text and '"protected_overlap_n": 14' in text
    summary=json.loads((root/'work/overlap/overlap_summary.json').read_text())
    assert summary['public_unprotected_n']==1 and not summary['participant_images_accessed']


def test_cross_person_source_alias_rejected_before_any_header_read(tmp_path,monkeypatch):
    path,mask,meta,row=image_fixture(tmp_path)
    # An authorized ID attached to another person's source must not authorize it.
    row['participant_id']='sub-00888'
    monkeypatch.setattr(nib,'load',lambda *a:pytest.fail('Guard should fail before any image header'))
    with pytest.raises(ValueError,match='Source participant mismatch'):
        archive_maps(tmp_path/'out',[row],{'participant_ids':['sub-00999']},mask,meta,{'source_doi':'test'})


def test_plan_filters_protected_and_unpublished_runs_before_source_access(tmp_path,monkeypatch):
    import types
    import prepare_public_maps as impl
    public=[{'participant_id':s} for s in ('sub-00999','sub-00888','sub-00000')]
    protected=dict(complete=True,covers=['sealed_N50','external_validation'],participant_ids=['sub-00000'],paper_protected_n=62)
    paths={}
    for task in impl.MAPPING:
        for k,_,_,_ in impl.MAPPING[task]:
            path=tmp_path/'sources/sub-00999/ses-01'/task/f'cope{k}.nii.gz'; path.parent.mkdir(parents=True,exist_ok=True)
            nib.save(nib.Nifti1Image(np.ones((2,3,4),dtype='float32'),np.eye(4)),path); paths[task,k]=path
    scope={'c':types.SimpleNamespace(analysis={'space':'MNI152NLin6Asym'})}
    monkeypatch.setattr(impl,'source_scope',lambda *a:scope)
    def phase_index(sc):
        return {s:dict(runs=(1,),strategy='l1_passthrough') for s in ('sub-00999','sub-00888')}
    def phase_unit(sc,s):
        assert s=='sub-00999','Excluded person reached map adapter'
        return {k:p for (task,k),p in paths.items() if task=='sharedreward'}
    monkeypatch.setitem(sys.modules,'final_stress_sources',types.SimpleNamespace(phase_index=phase_index,phase_unit=phase_unit,
        qc_table=lambda c:None,qc_reason=lambda *a:'',guard_path=lambda sc,p,s:p))
    def inspect(c,s,*args,**kwargs): assert s=='sub-00999'
    monkeypatch.setitem(sys.modules,'inventory',types.SimpleNamespace(inspect_unit=inspect,
        cope_path=lambda c,s,t,k,*a:paths[t,k],header_info=lambda *a:{},same_grid=lambda a,b:a.shape==b.shape))
    monkeypatch.setitem(sys.modules,'utils',types.SimpleNamespace(InputUnavailable=type('InputUnavailable',(Exception,),{})))
    monkeypatch.setattr(nib.Nifti1Image,'get_fdata',lambda *a,**k:pytest.fail('Plan materialized voxel arrays'))
    runs=[dict(participant_id=s,task=t,run=r) for s in ('sub-00999','sub-00888') for t,r in
          [('sharedreward',1),('trust',1)]]+[dict(participant_id='sub-00999',task='trust',run=2)]
    rows,result=impl.plan(tmp_path/'paper',tmp_path/'sources',tmp_path/'plan',protected,public,{'public_task_runs':runs})
    assert len(rows)==12 and result['n']==1 and not result['intensities_loaded']
    assert result['protected_public_n']==1
    assert result['exclusion_counts']=={'retained_source_runs_not_all_in_public_release':1}
