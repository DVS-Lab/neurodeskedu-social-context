"""Finalize an approved staged archive without redistributing template assets.

Only README and dataset_description.json change; mask.nii.gz is removed from
the upload. Every COPE and the manifest retain their exact bytes. The notebook
retrieves the pinned template separately and verifies the reconstructed mask.
No paper checkout, private membership file, model or held-out image is opened.
"""
import argparse
import csv
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import zipfile

import nibabel as nib
import numpy as np

TEMPLATE_URL='https://templateflow.s3.amazonaws.com/tpl-MNI152NLin6Asym/tpl-MNI152NLin6Asym_res-02_desc-brain_mask.nii.gz'
TEMPLATE_SHA256='e4e2b284170271afdafe26ac0997b2af5a0f5ddac35e28a7e796b52e8bc5adb1'
CC0_URL='https://creativecommons.org/publicdomain/zero/1.0/'
SUPPORT={'README','manifest.csv','dataset_description.json','aggregate_image_checks.json'}


def sha256(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def require(condition,message):
    if not condition: raise ValueError(message)


def finalize(source,destination,expected_sha256):
    source=Path(source); destination=Path(destination)
    require(source.resolve()!=destination.resolve(),'Preserve the original archive; choose a new output filename')
    require(not destination.exists(),'Output already exists; do not silently replace a release')
    require(sha256(source)==expected_sha256,'Staged archive checksum differs from the reviewed candidate')
    with zipfile.ZipFile(source) as old:
        rows=list(csv.DictReader(io.StringIO(old.read('manifest.csv').decode())))
        require(bool(rows),'Empty manifest')
        names=old.namelist(); expected={r['path'] for r in rows}|SUPPORT|{'mask.nii.gz'}
        require(len(names)==len(set(names)) and set(names)==expected,'Unexpected, duplicate or missing staged archive entries')
        cells=set(itertools.product(('sharedreward','trust'),('computer','friend','stranger'),('positive','negative')))
        people={}
        for row in rows:
            path=Path(row['path'])
            require(not path.is_absolute() and '..' not in path.parts and path.parts[0]=='maps','Invalid public map path')
            require(row['phase']=='outcome' and row['source_dataset']=='ds005123' and row['source_version']=='1.0.0'
                    and row['qc_included'].lower()=='true','Unexpected map provenance or QC')
            people.setdefault(row['participant_id'],[]).append((row['task'],row['partner'],row['valence']))
        require(all(len(v)==12 and set(v)==cells for v in people.values()),'Exactly twelve complete outcome conditions required')
        description=json.loads(old.read('dataset_description.json'))
        provenance=description['MaskProvenance']
        require(provenance['template_sha256']==TEMPLATE_SHA256,'Unexpected template mask source')
        # Only this already-exported mask is inspected, never a source subject.
        mask_bytes=old.read('mask.nii.gz')
        mask_image=nib.Nifti1Image.from_bytes(gzip.decompress(mask_bytes) if mask_bytes.startswith(b'\x1f\x8b') else mask_bytes)
        mask=mask_image.get_fdata()
        require(mask.ndim==3 and np.isin(mask,[0,1]).all() and mask.any(),'Invalid exported mask')
        mask_sha=hashlib.sha256(mask.astype('uint8').tobytes(order='C')).hexdigest()
        for key in ('sha256','license_note'): provenance.pop(key,None)
        provenance.update(distribution='external_reference_only',template_download_url=TEMPLATE_URL,
            expected_resampled_mask_data_sha256=mask_sha,
            description='Fixed TemplateFlow MNI152NLin6Asym res-02 binary brain mask; retrieved separately and resampled with nearest-neighbor interpolation to the common COPE grid.',
            license_note='Third-party template is not redistributed in this archive and is not offered under its CC0 dedication. Obtain it from the upstream provider subject to its terms.')
        description.update(Version='1.0.0',License='CC0-1.0',LicenseURL=CC0_URL,
            LicenseScope='Distributed COPE maps and original archive metadata. No third-party template files are included.',
            MaskDistribution='external_reference_only',MaskProvenance=provenance)
        description.pop('MaskLicense',None)
        readme=f'''PUBLIC EDUCATIONAL SOCIAL-CONTEXT OUTCOME MAPS — version 1.0.0

Contents: {len(people)} participants, {len(rows)} signed outcome COPEs. Each person
has computer/friend/stranger x positive/negative outcomes for Shared Reward and
Trust. See manifest.csv for exact contrasts, retained runs, bytes and checksums.

Source: OpenNeuro ds005123 v1.0.0
https://doi.org/10.18112/openneuro.ds005123.v1.0.0
Notebook and preparation code:
https://github.com/DVS-Lab/neurodeskedu-social-context

The maps are signed, uncentered source-model effect estimates on a common
MNI152NLin6Asym grid, not z scores or percent signal change. Source values are
unchanged. The tutorial constructs valence-averaged human/computer features.
Public-release membership, existing QC and complete twelve-condition inputs
were required. All original and supplemental protected validation participants
were excluded before source access; private membership records are not included.
Tutorial cross-validation uses only the educational subset, not that reserved
validation cohort. This is an educational derivative dataset, not a trained or
externally validated neural signature.

LICENSE — COPE MAPS AND ORIGINAL ARCHIVE METADATA
To the extent the releaser has rights in these distributed materials, they are
dedicated to the public domain under CC0 1.0 Universal:
{CC0_URL}
Citation of the source dataset and this derivative release is requested as
scholarly practice. This request does not add a condition to CC0.

EXTERNAL TEMPLATE REFERENCE — NOT INCLUDED OR RELICENSED
No TemplateFlow/FSL template image or mask is distributed in this archive.
The notebook retrieves the reference from the original provider, verifies its
SHA256, resamples it using fixed nearest-neighbor interpolation and verifies
that the resulting binary mask matches the reviewed mask. See MaskProvenance
in dataset_description.json. The provider's terms apply to that external file;
this dataset's CC0 dedication does not apply to it.
Template source: https://github.com/templateflow/tpl-MNI152NLin6Asym
TemplateFlow citation: https://doi.org/10.1038/s41592-022-01681-2
Template reference: https://doi.org/10.1016/j.neuroimage.2012.01.024
No decisions, neutral maps, other tasks, fitted paper models, raw time series,
anatomical scans or private membership lists are included.
'''
        destination.parent.mkdir(parents=True,exist_ok=True)
        temporary=destination.with_suffix('.part')
        try:
            with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_STORED) as new:
                for name in sorted(expected-{'mask.nii.gz','README','dataset_description.json'}):
                    data=old.read(name)
                    if name.startswith('maps/'):
                        row=next(r for r in rows if r['path']==name)
                        require(len(data)==int(row['byte_size']) and hashlib.sha256(data).hexdigest()==row['sha256'],'Source map checksum/size mismatch')
                    new.writestr(name,data)
                new.writestr('README',readme)
                new.writestr('dataset_description.json',json.dumps(description,indent=2)+'\n')
            with zipfile.ZipFile(temporary) as new:
                require(set(new.namelist())==expected-{'mask.nii.gz'},'Final allowlist mismatch')
                for name in expected-{'mask.nii.gz','README','dataset_description.json'}:
                    require(new.read(name)==old.read(name),'Finalization changed a map or manifest')
            temporary.replace(destination)
        finally: temporary.unlink(missing_ok=True)
    summary=dict(status='final_archive_verified',version='1.0.0',n=len(people),outcome_maps=len(rows),
        support_files=len(SUPPORT),archive_entries=len(rows)+len(SUPPORT),third_party_template_files_included=False,
        cope_and_manifest_bytes_unchanged=True,license='CC0-1.0',archive_bytes=destination.stat().st_size,
        archive_sha256=sha256(destination),source_archive_sha256=expected_sha256,
        expected_resampled_mask_data_sha256=mask_sha,zenodo_publication_performed=False)
    destination.with_suffix('.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sha256',required=True); a=p.parse_args()
    print(json.dumps(finalize(a.input,a.output,a.sha256),indent=2))
