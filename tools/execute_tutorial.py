#!/usr/bin/env python3
"""Execute the public tutorial in a fresh Neurodesk kernel, preserving failures for review."""
from pathlib import Path
import argparse
import os
import time
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=root / 'work' / 'executed-public.ipynb')
parser.add_argument('--kernel', default='python3')
parser.add_argument('--directory', type=Path, default=root, help='Execute in another directory to test the standalone notebook.')
args = parser.parse_args()
# Use the interpreter that launched this maintainer check. In Play this is its default Python, not a virtual environment.
os.environ['PATH'] = str(Path(__import__('sys').executable).parent) + os.pathsep + os.environ['PATH']
notebook = nbformat.read(root / 'Cross_task_decoding.ipynb', as_version=4)
for cell in notebook.cells:
    if cell.cell_type == 'code':
        cell.outputs = []
        cell.execution_count = None
        cell.metadata.pop('execution', None)
started = time.perf_counter()

def progress(cell, cell_index, **kwargs):
    if cell.cell_type == 'code':
        print(f'Running cell {cell_index}: {cell.source.splitlines()[0][:90]}', flush=True)

args.output.parent.mkdir(parents=True, exist_ok=True)
client = NotebookClient(notebook, timeout=1800, kernel_name=args.kernel,
                        resources={'metadata': {'path': str(args.directory.resolve())}}, on_cell_start=progress)
try:
    client.execute()
finally:
    nbformat.write(notebook, args.output)
print(f'COMPLETED in {time.perf_counter() - started:.1f} s: {args.output}', flush=True)
print((args.directory / 'outputs/public/execution_summary.json').read_text(), flush=True)
