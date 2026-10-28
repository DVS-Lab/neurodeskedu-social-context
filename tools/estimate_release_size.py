"""Header arithmetic only: no participant images or main-project files are opened."""
import argparse
import csv
import json
import math
from pathlib import Path

SCENARIOS = [
    ("Compact: two tasks × human/computer, valence averaged", 4),
    ("Core: two tasks × three partners × two valences", 12),
    ("Core plus corresponding z-stat images", 24),
    ("Core COPEs separately for two runs", 24),
]


def estimates(n=114,shape=(57,70,54),dtype_bytes=4):
    per_map=352+math.prod(shape)*dtype_bytes
    return [dict(scenario=name,n=n,maps_per_person=count,total_maps=n*count,
                 bytes_per_map=per_map,total_bytes=n*count*per_map,
                 decimal_GB=n*count*per_map/1e9,GiB=n*count*per_map/2**30)
            for name,count in SCENARIOS]


def measured_manifest(path):
    """Sum recorded compressed-file sizes without touching paths in the table."""
    with Path(path).open(newline='') as f: rows=list(csv.DictReader(f))
    sizes=[int(r['byte_size']) for r in rows]
    if any(v<0 for v in sizes): raise ValueError('negative byte_size')
    return dict(files=len(rows),total_bytes=sum(sizes),decimal_GB=sum(sizes)/1e9,
                note='Recorded manifest sizes only; no image paths accessed')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n',type=int,default=114); p.add_argument('--shape',type=int,nargs=3,default=(57,70,54))
    p.add_argument('--manifest',type=Path); a=p.parse_args()
    if a.n<1 or any(v<1 for v in a.shape): p.error('n and shape must be positive')
    result=dict(assumptions='NIfTI-1 header + float32 full-grid voxels; before gzip; maps only, no raw BOLD',
                grid_shape=a.shape,scenarios=estimates(a.n,a.shape))
    if a.manifest: result['measured_compressed_files']=measured_manifest(a.manifest)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
