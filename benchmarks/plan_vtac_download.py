"""Make a selective *resumable* VTaC download plan (does NOT download anything).

Only requests the explicit labelled subset within each official partition; no 18GB crawl.
Requires event_labels.csv and benchmark_data_split.csv from official PhysioNet.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
import re
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from benchmarks.train_vtac import dataset_root, split_rows

NAME = re.compile(r'[A-Za-z0-9_-]+\Z')


def build_plan(rows, counts):
    selected=[]
    used=set()
    # Stable order, preferentially choose a single event per record first.
    for name in ('train','validation','test'):
        for klass in (1,0):
            candidates=[r for r in rows if r['partition']==name and r['y']==klass]
            candidates.sort(key=lambda r:(r['record'],r['event']))
            first=[r for r in candidates if r['record'] not in used]
            later=[r for r in candidates if r['record'] in used]
            take=[]
            for r in first+later:
                if len(take)>=counts[name]:break
                take.append(r)
                used.add(r['record'])
            if len(take)<counts[name]:
                raise ValueError(f'Not enough annotated events in {name} for label {klass}')
            selected+=take
    return selected


def make_script(rows, root, out, version):
    remote = ('annotated_waveforms' if version=='1.1' else 'waveforms')
    base=f'https://physionet.org/files/vtac/{version}/{remote}'
    # Windows PowerShell 5.1-compatible, deliberately non-parallel to avoid heavy server load.
    script=[
        '# Research-only VTaC selective downloads. Generated from official labels and official partitions.',
        '# Run again to resume interrupted downloads. May be extremely slow due to PhysioNet bandwidth limiting.',
        f'$root = {json.dumps(str(root))}',
        '$ErrorActionPreference = "Stop"',
        '$items = @('
    ]
    for row in rows:
        record,event=row['record'],row['event']
        if not NAME.fullmatch(record) or not NAME.fullmatch(event):
            raise ValueError('Unexpected record identifier; refusing to generate a PowerShell command')
        script.append(f'    @{{record="{record}"; event="{event}"; partition="{row["partition"]}"; label="{row["y"]}"}}')
    script.extend([
        ')',
        f'$urlBase = {json.dumps(base)}',
        'foreach ($item in $items) {',
        '  $folder = Join-Path (Join-Path $root '+('"annotated_waveforms"' if version=='1.1' else '"waveforms"')+') $item.record',
        '  New-Item -ItemType Directory -Force -Path $folder | Out-Null',
        '  foreach ($ext in @("hea","dat")) {',
        '    $name = "$($item.event).$ext"',
        '    $target = Join-Path $folder $name',
        '    $uri = "$urlBase/$($item.record)/$name"',
        '    $success = $false',
        '    for($attempt=1; $attempt -le 5; $attempt++) {',
        '      & curl.exe -fL -C - --connect-timeout 25 --max-time 420 -o $target $uri',
        '      if ($LASTEXITCODE -eq 0) { $success=$true; break }',
        '      Start-Sleep -Seconds 12',
        '    }',
        '    if (-not $success) { Write-Warning "Not yet downloaded: $uri ; rerun the script later" }',
        '  }',
        '}',
        'Write-Host "Finished attempted transfers; run the audit and training command to validate all actual waveform files."'
    ])
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('\n'.join(script)+'\n',encoding='utf-8-sig')
    return len(rows)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('download-selected-vtac.ps1'))
    parser.add_argument('--version',choices=('1.0','1.1'),default='1.0',help='1.0 is smaller; use official URLs')
    parser.add_argument('--train-per-class',type=int,default=24)
    parser.add_argument('--eval-per-class',type=int,default=7)
    args=parser.parse_args(argv)
    if args.train_per_class < 20 or args.eval_per_class < 5:
        parser.error('Required minimum per class: 20 train, 5 validation/test (NOT sufficient for clinical claims)')
    root=dataset_root(args.root)
    selected=build_plan(split_rows(root),dict(train=args.train_per_class,validation=args.eval_per_class,test=args.eval_per_class))
    n=make_script(selected,root,args.output,args.version)
    print(f'Planned {n} labelled events. Created {args.output}. Each event has a header and a data file.')
    print('No downloads have happened yet. Transfers may be very slow. Use official PhysioNet licensing/citations.')

if __name__=='__main__':main()
