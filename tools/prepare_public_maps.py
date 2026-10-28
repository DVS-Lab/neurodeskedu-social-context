"""Plan/stage public outcome COPEs without modifying the paper or scoring anyone.

Run where the private membership locks and source FEAT outputs are accessible.
Default stage is metadata/provenance planning. All curation records and source
paths remain under this repository's ignored work/ directory.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_export_plan import check

MAPPING={
 'sharedreward':[(1,'computer','negative','C_pun'),(2,'computer','positive','C_rew'),
                 (3,'friend','negative','F_pun'),(4,'friend','positive','F_rew'),
                 (5,'stranger','negative','S_pun'),(6,'stranger','positive','S_rew')],
 'trust':[(4,'computer','negative','C_def'),(5,'computer','positive','C_rec'),
          (6,'friend','negative','F_def'),(7,'friend','positive','F_rec'),
          (8,'stranger','negative','S_def'),(9,'stranger','positive','S_rec')]
}


def require(condition,message):
    if not condition: raise ValueError(message)


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()


def read_table(path):
    with Path(path).open(newline='') as f: return list(csv.DictReader(f,delimiter='\t' if Path(path).suffix=='.tsv' else ','))


def write_json(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.part'); temporary.write_text(json.dumps(value,indent=2)+'\n'); temporary.replace(path)


def write_table(path,rows):
    require(bool(rows),'No eligible complete participants; no maps will be staged')
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    path.chmod(0o600)


def protected_union(paper,external=None,no_additional=False):
    """Read/hash existing locks; retain unavailable original holdouts; never redraw."""
    paper=Path(paper)
    paths={
      'original_metadata':paper/'provenance/subject_split_v1.json',
      'original_split':paper/'work/splits/subject_split_v1.tsv',
      'revised_metadata':paper/'provenance/revised/samples/samples.json',
      'revised_manifest':paper/'work/revised/samples/manifest.tsv'}
    require(all(p.is_file() for p in paths.values()),'Private paper split/manifest files are unavailable. Run this on Linux2; do not recreate or infer membership.')
    old=json.loads(paths['original_metadata'].read_text()); revised=json.loads(paths['revised_metadata'].read_text())
    require(sha256(paths['original_split'])==old['sha256']==revised['original_split_sha256'],'Original membership fingerprint mismatch')
    require(sha256(paths['revised_manifest'])==revised['manifest_sha256'],'Revised membership fingerprint mismatch')
    rows=read_table(paths['original_split']); manifest=read_table(paths['revised_manifest'])
    require(len({r['subject'] for r in rows})==len(rows) and {r['split'] for r in rows}=={'development','holdout'},'Invalid original split')
    original={r['subject'] for r in rows if r['split']=='holdout'}
    partitions={}
    for r in manifest: partitions.setdefault(r['subject'],set()).add(r['partition'])
    require(all(len(x)==1 and x<={'development','holdout'} for x in partitions.values()),'Revised participant changes partition')
    protected={s for s,p in partitions.items() if p=={'holdout'}}
    require(len(original)==50 and original<=protected and len(protected)==revised['protected_holdout_total_n'],'Protected pool incomplete')
    require(revised['original_holdout_redrawn'] is False and revised['holdout_scored'] is False,'Unexpected paper membership provenance')
    require((external is not None) != no_additional,'Specify an external exclusion file OR explicit --no-additional-external-validation')
    extra=set(); inputs={str(p):sha256(p) for p in paths.values()}
    if external is not None:
        external=Path(external); record=json.loads(external.read_text())
        require(record.get('complete') is True and record.get('dataset_namespace')=='rf1-sra','External exclusion file must be complete and use the RF1 participant namespace')
        extra=set(record['participant_ids']); inputs[str(external)]=sha256(external)
    all_people=protected|extra
    require(all(re.fullmatch(r'sub-[A-Za-z0-9]+',s) for s in all_people),'Invalid protected participant ID')
    return dict(complete=True,covers=['sealed_N50','external_validation'],participant_ids=sorted(all_people),
                original_n=len(original),paper_protected_n=len(protected),additional_external_n=len(extra),
                original_participant_ids=sorted(original),supplemental_participant_ids=sorted(protected-original),
                no_additional_external_validation_confirmed=no_additional,source_hashes=inputs)


def public_metadata(contract):
    path=ROOT/'work/public_release/participants.tsv'; path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(contract['public_participants_url'],timeout=45) as r: data=r.read(1024*1024)
        path.write_bytes(data)
    require(sha256(path)==contract['public_participants_sha256'],'Pinned public participants metadata changed')
    rows=read_table(path)
    require(len(rows)==contract['public_participants_n'] and len({r['participant_id'] for r in rows})==len(rows),'Public participant inventory mismatch')
    return rows


def source_scope(paper,projects,subjects,blocked,contract):
    # Reuse read-only contrast/design guards, not model-fitting entry points.
    # Suppress bytecode writes into the paper checkout.
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(paper/'code'))
    from utils import load_config
    from revised_design import revised_config
    from revised_samples import RevisedGuard
    base=load_config(root=paper)
    for key in ('linux2','sharedreward','trust'):
        require(base.repos[key].resolve()==(projects/base.paths['repositories'][key]).resolve(),
                'Configured source root differs; set PROJECTS_ROOT/RF1_*_ROOT consistently')
    for rel,h in contract['paper_metadata'].items(): require(sha256(paper/rel)==h,'Reviewed paper membership metadata changed')
    for task,files in contract['runtime_sources'].items():
        for rel,h in files.items(): require(sha256(base.repos[task]/rel)==h,'Reviewed source model/audit changed: '+task+'/'+rel)
    c=revised_config(base,'inventory')
    return dict(c=c,subjects=subjects,guard=RevisedGuard(frozenset(subjects),frozenset(blocked)),folds={})


def plan(paper,projects,out,protected,public_rows,contract):
    import nibabel as nib
    from final_stress_sources import phase_index,phase_unit,qc_table,qc_reason,guard_path
    from inventory import inspect_unit,cope_path,header_info,same_grid
    from utils import InputUnavailable
    allowed=sorted({r['participant_id'] for r in public_rows}-set(protected['participant_ids']))
    require(bool(allowed),'No unprotected public participants')
    scope=source_scope(paper,projects,allowed,protected['participant_ids'],contract)
    c=scope['c']; scope['phase_index']=phase_index(scope); qc=qc_table(c)
    public_runs={}
    for r in contract['public_task_runs']: public_runs.setdefault((r['participant_id'],r['task']),set()).add(int(r['run']))
    records=[]; excluded=Counter(); private_exclusions=[]; geometry=None
    for person in allowed:
        unit=scope['phase_index'].get(person)
        if unit is None:
            reason='absent_phase_resolved_source'
        elif not set(unit['runs'])<=public_runs.get((person,'sharedreward'),set()) or not {1,2}<=public_runs.get((person,'trust'),set()):
            reason='retained_source_runs_not_all_in_public_release'
        else:
            reason=qc_reason(qc,person,'sharedreward',unit['runs']) or qc_reason(qc,person,'trust',(1,2))
        if reason:
            excluded[reason]+=1; private_exclusions.append(dict(participant_id=person,reason=reason)); continue
        try:
            sr=phase_unit(scope,person)
            inspect_unit(c,person,'trust','L2',required_copes_only=True)
        except InputUnavailable as exc:
            reason='unavailable_source:'+str(exc)
            excluded[reason]+=1; private_exclusions.append(dict(participant_id=person,reason=reason)); continue
        person_rows=[]
        for task in MAPPING:
            for cope,partner,valence,name in MAPPING[task]:
                require(person not in protected['participant_ids'],'Protected participant reached source inventory')
                path=guard_path(scope,sr[cope] if task=='sharedreward' else cope_path(c,person,task,cope,'L2'),person)
                header_info(path,c.analysis['space']); image=nib.load(path)
                if geometry is None: geometry=image
                require(same_grid(image,geometry),'Source geometries differ; do not resample or modify paper inputs silently')
                person_rows.append(dict(participant_id=person,task=task,partner=partner,valence=valence,phase='outcome',
                    source_dataset='ds005123',source_version='1.0.0',qc_included='true',contrast_name=name,
                    contrast_index=cope,contrast_weights=f'EV{cope}=+1',
                    retained_runs=','.join(map(str,unit['runs'])) if task=='sharedreward' else '1,2',
                    run_strategy=unit['strategy'] if task=='sharedreward' else 'fixed_effects',
                    source_path=str(path),source_sha256=sha256(path),byte_size=path.stat().st_size))
        records.extend(person_rows)
    metadata_check=check(public_rows,records,protected)
    write_table(out/'private_export_plan.csv',records)
    if private_exclusions: write_table(out/'private_exclusions.csv',private_exclusions)
    summary=dict(status='plan_complete',public_release_n=len(public_rows),public_unprotected_candidates=len(allowed),
                 protected_public_n=len(public_rows)-len(allowed),paper_protected_n=protected['paper_protected_n'],
                 exclusion_counts=dict(excluded),**{k:v for k,v in metadata_check.items() if k!='status'},
                 intensities_loaded=False,source_headers_and_allowed_bytes_hashed=True)
    write_json(out/'plan_summary.json',summary)
    return records,summary


def guarded_source(row,blocked):
    person=row['participant_id']; require(person not in blocked,'Protected participant reached copy stage')
    path=Path(row['source_path'])
    require(person in path.parts and person in path.resolve().parts,'Source participant mismatch')
    require(not any(p.startswith('sub-') and p!=person for p in path.resolve().parts),'Cross-person source symlink')
    return path


def archive_maps(out,rows,protected,mask_path,mask_metadata,contract):
    import numpy as np
    import nibabel as nib
    blocked=set(protected['participant_ids'])
    require(bool(rows),'Empty map plan')
    for row in rows: guarded_source(row,blocked)
    require(mask_path is not None and mask_metadata is not None,'Archive stage requires an independently defined mask and its provenance JSON')
    mask_path=Path(mask_path).resolve(); meta=json.loads(Path(mask_metadata).read_text())
    require(meta.get('kind')=='independent_template' and meta.get('source_url') and meta.get('description'),'Independent mask provenance incomplete')
    require(meta['sha256']==sha256(mask_path),'Independent mask checksum mismatch')
    require(not any(p.startswith('sub-') for p in mask_path.parts),'Participant image cannot be an independent mask')
    mask=nib.load(mask_path); mask_data=mask.get_fdata()
    require(mask_data.ndim==3 and np.isfinite(mask_data).all() and np.isin(mask_data,[0,1]).all() and mask_data.any(),'Invalid binary mask')
    source=nib.load(rows[0]['source_path'])
    require(source.shape==mask.shape and np.allclose(source.affine,mask.affine,atol=1e-5,rtol=0),'Mask must already match source grid; no unreviewed mask resampling')
    destination=out/'bundle'; require(not destination.exists(),'Bundle already exists; preserve and inspect it rather than overwrite')
    destination.mkdir(parents=True); output_rows=[]; metrics=[]
    blocked=set(protected['participant_ids'])
    for row in rows:
        person=row['participant_id']; require(person not in blocked,'Protected participant reached copy stage')
        path=guarded_source(row,blocked)
        require(sha256(path)==row['source_sha256'],'Planned source changed before export')
        image=nib.load(path); data=image.get_fdata(dtype=np.float32)
        require(data.shape==mask.shape and np.allclose(image.affine,mask.affine,atol=1e-5,rtol=0) and np.isfinite(data).all(),'Invalid signed map or geometry')
        relative=f'maps/{person}_{row["task"]}_{row["partner"]}_{row["valence"]}_cope.nii.gz'
        target=destination/relative; target.parent.mkdir(exist_ok=True)
        header=image.header.copy(); header.set_data_dtype('float32'); header['descrip']=b'Public educational outcome COPE'
        header['aux_file']=b''; header.set_intent('none',name=''); header.extensions.clear()
        for field in ('data_type','db_name'): header[field]=b''
        nib.save(nib.Nifti1Image(data,image.affine,header),target)
        checked=nib.load(target).get_fdata(dtype=np.float32)
        require(np.array_equal(data,checked),'Export changed signed effect values')
        public={k:v for k,v in row.items() if k not in ('source_path','source_sha256','byte_size')}
        public.update(path=relative,sha256=sha256(target),byte_size=target.stat().st_size)
        output_rows.append(public)
        metrics.append(dict(minimum=float(data.min()),maximum=float(data.max()),negative_fraction=float((data[mask_data.astype(bool)]<0).mean())))
    clean=nib.Nifti1Image(mask_data.astype('uint8'),mask.affine); clean.header.set_xyzt_units('mm'); nib.save(clean,destination/'mask.nii.gz')
    write_table(destination/'manifest.csv',output_rows)
    write_json(destination/'dataset_description.json',dict(Name='Public educational social-context outcome COPEs',
        SourceDatasetDOI=contract['source_doi'],SourceDatasetVersion='1.0.0',License='CC0',
        Description='Signed uncentered condition COPEs; no paper models or protected validation maps',
        MaskProvenance=meta,ContrastDefinitions=MAPPING,PrivateMembershipAuditRetained=True))
    write_json(destination/'aggregate_image_checks.json',dict(finite_maps=len(metrics),negative_effects_preserved=True,
        minimum=min(x['minimum'] for x in metrics),maximum=max(x['maximum'] for x in metrics),
        negative_fraction_range=[min(x['negative_fraction'] for x in metrics),max(x['negative_fraction'] for x in metrics)]))
    (destination/'README').write_text('Curated educational derivatives of OpenNeuro ds005123 v1.0.0.\n'
        'See manifest for exact outcome contrasts and retained-run strategy. Human/computer construction occurs in the notebook.\n'
        'Original and supplemental paper holdouts and all declared external-validation subjects were removed before source access.\n'
        'Signed COPE units are source-model effect estimates, not z scores or percent signal change. No thresholding or centering is applied.\n'
        'The mask is independently defined; the later release review must verify its coverage and source provenance.\n'
        'This is a staged, unreviewed derivative bundle, not a published Zenodo release.\n')
    archive=out/'public_outcome_copes.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for p in sorted(destination.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(destination))
    require(archive.stat().st_size<50_000_000_000,'Archive exceeds default Zenodo quota')
    summary=dict(status='archive_staged_for_review',n=len({r['participant_id'] for r in rows}),map_files=len(rows),
                 compressed_map_bytes=sum(r['byte_size'] for r in output_rows),archive_bytes=archive.stat().st_size,
                 archive_sha256=sha256(archive),ready_to_publish=False,holdout_images_accessed=False)
    write_json(out/'archive_summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--paper-root',type=Path,required=True)
    p.add_argument('--projects-root',type=Path,default=Path('/ZPOOL/data/projects'))
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--external-validation',type=Path)
    group.add_argument('--no-additional-external-validation',action='store_true')
    p.add_argument('--stage',choices=('overlap','plan','archive'),default='plan')
    p.add_argument('--mask',type=Path); p.add_argument('--mask-provenance',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'work/zenodo-v1')
    a=p.parse_args(); out=a.output.resolve(); paper=a.paper_root.resolve(); projects=a.projects_root.resolve()
    try:
        require(out.is_relative_to((ROOT/'work').resolve()),'Curation outputs must stay under this tutorial repository work/')
        # The isolated tutorial checkout may be a sibling under projects/. Its
        # own work/ is permitted; the paper checkout is never an output target.
        require(not out.is_relative_to(paper),'Output cannot modify the paper tree')
        contract=json.loads((ROOT/'config/source_contract.json').read_text())
        for rel,h in contract['paper_metadata'].items(): require(sha256(paper/rel)==h,'Reviewed paper membership metadata changed')
        protected=protected_union(paper,a.external_validation,a.no_additional_external_validation)
        out.mkdir(parents=True,exist_ok=True); write_json(out/'protected_union.json',protected); (out/'protected_union.json').chmod(0o600)
        public_rows=public_metadata(contract)
        if a.stage=='overlap':
            public={r['participant_id'] for r in public_rows}
            original=set(protected['original_participant_ids']); supplemental=set(protected['supplemental_participant_ids'])
            union=set(protected['participant_ids'])
            summary=dict(status='metadata_only_overlap',public_release_n=len(public),paper_protected_n=protected['paper_protected_n'],
                original_overlap_n=len(public&original),supplemental_overlap_n=len(public&supplemental),
                protected_overlap_n=len(public&union),public_unprotected_n=len(public-union),
                qc_and_complete_maps_not_yet_checked=True,participant_images_accessed=False)
            for path,h in protected['source_hashes'].items(): require(sha256(path)==h,'Membership changed during overlap check')
            write_json(out/'overlap_summary.json',summary); print(json.dumps(summary,indent=2)); return 0
        # Load scientific adapters only after membership is verified; no source image reads before this point.
        scope=source_scope(paper,projects,sorted({r['participant_id'] for r in public_rows}-set(protected['participant_ids'])),protected['participant_ids'],contract)
        rows,summary=plan(paper,projects,out,protected,public_rows,contract)
        print(json.dumps(summary,indent=2))
        if a.stage=='archive':
            if a.mask: require(not a.mask.resolve().is_relative_to(paper),'Do not use a paper-derived group/coverage mask')
            print(json.dumps(archive_maps(out,rows,protected,a.mask,a.mask_provenance,contract),indent=2))
        for path,h in protected['source_hashes'].items(): require(sha256(path)==h,'Membership source changed during export')
        print('Paper membership files unchanged; no held-out images accessed. No Zenodo upload performed.')
    except (ValueError,FileNotFoundError) as exc:
        print('STOP: '+str(exc)); return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
