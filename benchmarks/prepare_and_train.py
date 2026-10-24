"""Windows offline-first VTaC expert-labelled data acquisition and baseline training.

No generated clinical data, no claimed accuracy without genuine recordings.
Requests a small official 76-event subset, reuses valid files, supports HTTP range resume.
Research use ONLY; does not connect to patient monitors or modify live alarms.
"""
from __future__ import annotations
import argparse,json,sys,time,urllib.request,urllib.error
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from benchmarks.train_vtac import (dataset_root,split_rows,locate_waveform,
    verify_format16_waveform,load_feature_rows,train)
BASE='https://physionet.org/files/vtac'


def resumable(url: str, target: Path, retries=5, pause=time.sleep):
    if not url.startswith(BASE+'/'):raise ValueError('Unexpected download origin')
    target.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(retries):
        length=target.stat().st_size if target.is_file() else 0
        headers={'Accept-Encoding':'identity','User-Agent':'WaveAssure-research/0.4'}
        if length:headers['Range']=f'bytes={length}-'
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as response:
                if response.status not in (200,206):raise ValueError('Unexpected HTTP status')
                append=response.status==206 and length>0
                if append and not response.headers.get('Content-Range','').startswith(f'bytes {length}-'):
                    raise ValueError('Wrong HTTP range offset; refusing corrupt append')
                with target.open('ab' if append else 'wb') as handle:
                    while True:
                        block=response.read(65536)
                        if not block:break
                        handle.write(block)
            return True
        except urllib.error.HTTPError as exc:
            if exc.code==416 and length:return True  # caller verifies bytes/checksums
            print('HTTP error',exc.code,target.name,'attempt',attempt+1,flush=True)
        except (OSError,ValueError,urllib.error.URLError) as exc:
            print('Download interrupted:',str(exc)[:140],target.name,'attempt',attempt+1,flush=True)
        if attempt<retries-1:pause(5*(attempt+1))
    return False


def is_valid(root,rec,event):
    try:return bool(verify_format16_waveform(locate_waveform(root,rec,event)))
    except (OSError,ValueError,FileNotFoundError):return False


def select_subset(rows,root,training_each=24,eval_each=7):
    result=[]
    # Prioritize records already downloaded, without crossing any official partition.
    used=set()
    for part in ('train','validation','test'):
        for label in (1,0):
            candidates=[r for r in rows if r['partition']==part and r['y']==label]
            candidates.sort(key=lambda r:(not is_valid(root,r['record'],r['event']),r['record'],r['event']))
            want=training_each if part=='train' else eval_each
            chosen=[]
            for row in candidates:
                if row['record'] not in used:
                    chosen.append(row);used.add(row['record'])
                if len(chosen)==want:break
            if len(chosen)<want:
                for row in candidates:
                    if row not in chosen:chosen.append(row)
                    if len(chosen)==want:break
            if len(chosen)<want:raise ValueError('Insufficient source events for '+part+' '+str(label))
            result+=chosen
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(r'D:\WaveAssure-Datasets'))
    parser.add_argument('--output',type=Path,default=Path('models/vtac'))
    parser.add_argument('--version',choices=['1.0','1.1'],default='1.0')
    parser.add_argument('--no-download',action='store_true')
    args=parser.parse_args(argv)
    root=args.root.resolve();root.mkdir(parents=True,exist_ok=True)
    if not args.no_download:
        for name in ('event_labels.csv','benchmark_data_split.csv'):
            file=root/name
            if not file.is_file() or file.stat().st_size<100:
                if file.exists():file.unlink()
                print('Get official',name,flush=True)
                if not resumable(f'{BASE}/{args.version}/{name}',file):
                    raise RuntimeError('Official metadata download incomplete: '+name)
    dataset=dataset_root(root)
    rows=split_rows(dataset)
    selected=select_subset(rows,dataset)
    (root/'waveassure_selection.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    print('Selected',len(selected),'officially labelled events; no labels are fabricated.',flush=True)
    if not args.no_download:
        branch='waveforms' if args.version=='1.0' else 'annotated_waveforms'
        consecutive_errors=0
        for i,row in enumerate(selected,1):
            rec,ev=row['record'],row['event']
            if is_valid(root,rec,ev):
                print(f'[{i}/{len(selected)}] Reuse validated {rec}/{ev}',flush=True);continue
            print(f'[{i}/{len(selected)}] Download labelled {rec}/{ev}, {row["partition"]}, class {row["y"]}',flush=True)
            base=root/branch/rec/ev
            ok=True
            for ext in ('.hea','.dat'):
                file=base.with_suffix(ext)
                if ext=='.hea' and file.exists():
                    # Prior stalled recursive downloads commonly left zero-byte header files.
                    try:
                        if file.stat().st_size<100 or not file.read_text('ascii').strip():file.unlink()
                    except (OSError,UnicodeError):file.unlink()
                if not resumable(f'{BASE}/{args.version}/{branch}/{rec}/{ev}{ext}',file):ok=False;break
            if ok and is_valid(root,rec,ev):consecutive_errors=0
            else:
                consecutive_errors+=1
                print('Still incomplete; re-running this same script continues the download',flush=True)
            (root/'waveassure_download_progress.json').write_text(json.dumps({'processed':i,'planned':len(selected),
                'current':f'{rec}/{ev}','valid_current':is_valid(root,rec,ev)},indent=2),encoding='utf-8')
            if consecutive_errors>=6:
                print('Stopped after 6 consecutive download failures to avoid stressing the server',flush=True)
                break
    X,y,part,ids,skipped=load_feature_rows(root,selected)
    print('Verified examples per official partition:',dict(Counter(part)),flush=True)
    if skipped:print('Missing, partial or invalid:',len(skipped),flush=True)
    try:metrics=train(X,y,part,ids,args.output,dataset_version=args.version)
    except ValueError as exc:
        print('MODEL NOT TRAINED:',str(exc),flush=True)
        print('Re-run the same script once there are sufficient real True and False labelled waveforms.',flush=True)
        return 2
    (args.output/'skipped.json').write_text(json.dumps(skipped,indent=2),encoding='utf-8')
    print('RETROSPECTIVE RESEARCH MODEL TRAINED. Held-out results:',json.dumps(metrics['results']['test'],indent=2),flush=True)
    print('Not clinically validated. Do not suppress/route/priority-rank real alarms.',flush=True)
    return 0

if __name__=='__main__':sys.exit(main())
