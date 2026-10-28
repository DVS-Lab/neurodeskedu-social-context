"""Validate private curation metadata before any map export; never open images.

This is not an exporter. An approved metadata check is necessary but not sufficient
for release: source provenance, QC and image contents still need curator review.
"""
import argparse
import csv
import itertools
import json
from pathlib import Path

CELLS=set(itertools.product(('sharedreward','trust'),('computer','friend','stranger'),('positive','negative')))


def check(public_rows,plan_rows,protected):
    if protected.get('complete') is not True or not {'sealed_N50','external_validation'}<=set(protected.get('covers',[])):
        raise ValueError('A complete curator-prepared union of both protected membership sets is required')
    public={r['participant_id'] for r in public_rows}; blocked=set(protected['participant_ids'])
    if not public or not plan_rows: raise ValueError('Empty public participant list or export plan')
    by_person={}; sizes=[]
    for r in plan_rows:
        person=r['participant_id']
        if person not in public: raise ValueError('Export plan includes a participant outside the pinned public release')
        if person in blocked: raise ValueError('Export plan intersects protected validation membership; stop before image access')
        if r['source_dataset']!='ds005123' or r['source_version']!='1.0.0' or r['phase']!='outcome':
            raise ValueError('Unexpected source release or phase')
        if r['qc_included'].strip().lower()!='true': raise ValueError('QC-ineligible input in export plan')
        cell=(r['task'],r['partner'],r['valence'])
        if cell not in CELLS or cell in by_person.setdefault(person,set()): raise ValueError('Invalid/duplicate condition map')
        by_person[person].add(cell)
        value=int(r['byte_size'])
        if value<=0: raise ValueError('Missing/invalid byte_size; collect metadata without reading held-out images')
        sizes.append(value)
    if any(cells!=CELLS for cells in by_person.values()): raise ValueError('Exactly 12 complete condition maps per eligible person required')
    return dict(status='metadata_checks_passed',n=len(by_person),map_count=len(plan_rows),
                total_recorded_map_bytes=sum(sizes),decimal_GB=sum(sizes)/1e9,
                participant_images_opened=False,ready_to_publish=False)


def table(path):
    with Path(path).open(newline='') as f: return list(csv.DictReader(f,delimiter='\t' if Path(path).suffix=='.tsv' else ','))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--public-participants',type=Path,required=True)
    p.add_argument('--export-plan',type=Path,required=True)
    p.add_argument('--protected-membership',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(check(table(a.public_participants),table(a.export_plan),json.loads(a.protected_membership.read_text())),indent=2))

if __name__=='__main__': main()
