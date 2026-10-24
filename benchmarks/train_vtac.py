"""Train a genuine, retrospective research baseline using labelled PhysioNet VTaC events.

NEVER used for alarm suppression, patient care, or live monitoring.
Requires enough real, valid, expert-labelled events in ALL official partitions.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
import platform
from importlib.metadata import version as package_version
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from waveassure.alarm_model import (FEATURE_NAMES, extract_features, export_model, assess,
                                     ALARM_SECOND, FEATURE_SECONDS)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f'Missing dataset metadata: {path}')
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def dataset_root(root):
    root = Path(root).resolve()
    if (root/'event_labels.csv').exists():
        return root
    candidates = list(root.glob('**/event_labels.csv'))
    if len(candidates) == 1:
        return candidates[0].parent
    raise FileNotFoundError('Could not uniquely locate event_labels.csv; pass the dataset metadata folder with --root')


def split_rows(root):
    root = Path(root)
    labels = read_csv(root/'event_labels.csv')
    partitions = read_csv(root/'benchmark_data_split.csv')
    if not labels or not partitions:
        raise ValueError('Empty labels or split metadata')
    if not {'record','event','decision'}.issubset(labels[0]):
        raise ValueError('Unexpected event_labels.csv columns: '+str(list(labels[0])))
    if 'record' not in partitions[0]:
        raise ValueError('Official partition must contain record identity; cannot prevent patient leakage')
    split_col = next((key for key in ('split','dataset','partition','set','data_split') if key in partitions[0]), None)
    if split_col is None:
        raise ValueError('Unrecognized partition column. Actual columns: '+str(list(partitions[0])))
    split_map = {'train':'train','training':'train','val':'validation','valid':'validation',
                 'validation':'validation','test':'test','testing':'test'}
    # Support record-only partitions and record+event partitions, but never silently guess.
    has_event = 'event' in partitions[0]
    partition_index = {}
    for row in partitions:
        key = (row['record'],row['event']) if has_event else row['record']
        raw = row[split_col].strip().lower()
        if raw not in split_map:
            raise ValueError(f'Unknown partition label {raw!r}')
        split = split_map[raw]
        if key in partition_index and partition_index[key] != split:
            raise ValueError('Conflicting official split assignment: '+str(key))
        partition_index[key] = split
    rows=[]
    for label in labels:
        key=(label['record'],label['event']) if has_event else label['record']
        if key not in partition_index:
            raise ValueError('Label has no official split assignment: '+str(key))
        decision=label['decision'].strip().lower()
        if decision not in ('true','false'):
            raise ValueError(f'Unrecognized binary label {decision!r}')
        rows.append({'record':label['record'],'event':label['event'],
                     'partition':partition_index[key],'y':1 if decision=='true' else 0})
    if len(set((r['record'],r['event']) for r in rows)) != len(rows):
        raise ValueError('Duplicate label events')
    patient_splits = defaultdict(set)
    for row in rows:
        patient_splits[row['record']].add(row['partition'])
    leakage=[key for key,v in patient_splits.items() if len(v)>1]
    if leakage:
        raise ValueError(f'Patient-record leakage across official partitions: {len(leakage)}')
    return rows


def locate_waveform(root, record, event):
    """Both official annotated_waveforms and overlapping v1.1 waveforms supported."""
    for directory in ('annotated_waveforms', 'waveforms'):
        p=root/directory/record/event
        if p.with_suffix('.hea').is_file() and p.with_suffix('.dat').is_file():
            return str(p)
    # Prior user's partial sample folder; restrict to exact label/event, never relabel.
    p=root/'sample'/record/event
    if p.with_suffix('.hea').is_file() and p.with_suffix('.dat').is_file():
        return str(p)
    raise FileNotFoundError(f'No local header+data pair for {record}/{event}')


def audit_data(root, rows):
    audit = {'official_total':len(rows), 'official_counts':{}, 'local_candidate_pairs':{}, 'local_expected_missing':{},
             'unique_patients':{}}
    for name in ('train','validation','test'):
        subset=[r for r in rows if r['partition']==name]
        audit['official_counts'][name]={'true':sum(r['y']==1 for r in subset), 'false':sum(r['y']==0 for r in subset)}
        audit['unique_patients'][name]=len({r['record'] for r in subset})
        c=Counter()
        for row in subset:
            try:
                locate_waveform(root,row['record'],row['event'])
                c['candidate_pairs']+=1
            except FileNotFoundError:
                c['missing_pair']+=1
        audit['local_candidate_pairs'][name]=c['candidate_pairs']
        audit['local_expected_missing'][name]=c['missing_pair']
    audit['warning']='Candidate file pairs are NOT confirmed valid; use waveform decoding or the integrity validator.'
    return audit



def verify_format16_waveform(base):
    """Validate *entire* WFDB sample file before fitting (shared interleaved format 16 only).

    This deliberately limits the benchmark loader to VTaC format-16 examples. It does
    not substitute for PhysioNet's published SHA256SUMS authenticity verification.
    """
    path=Path(base)
    lines=[line.strip() for line in path.with_suffix('.hea').read_text(encoding='ascii').splitlines()
           if line.strip() and not line.startswith('#')]
    if not lines:
        raise ValueError('Empty WFDB header')
    lead=lines[0].split()
    if len(lead)<4 or lead[0]!=path.name:
        raise ValueError('Invalid WFDB main header')
    channels=int(lead[1]);samples=int(lead[3])
    if channels<1 or channels>16 or samples<1 or len(lines)<channels+1:
        raise ValueError('Unsupported channels or sample count')
    checksum=[]
    for line in lines[1:channels+1]:
        field=line.split()
        if len(field)<7 or field[0]!=(path.name+'.dat') or field[1]!='16':
            raise ValueError('Unsupported WFDB layout; shared 16-bit file required')
        checksum.append(int(field[6]) & 65535)
    dat=path.with_suffix('.dat')
    expected=channels*samples*2
    if dat.stat().st_size!=expected:
        raise ValueError(f'Incomplete format-16 data: {dat.stat().st_size:,}/{expected:,} bytes')
    all_samples=np.memmap(dat,dtype='<i2',mode='r',shape=(samples,channels))
    for idx,c in enumerate(checksum):
        if (int(np.sum(all_samples[:,idx],dtype=np.int64)) & 65535)!=c:
            raise ValueError(f'WFDB sample checksum mismatch in channel {idx}')
    del all_samples
    return True


def physical_pre_alarm_window(base):
    """Read verified WFDB format-16 signals in physical units (no external WFDB decoder).

    Only the last 30 s BEFORE the 300 s alarm onset are loaded. Format 16 only.
    """
    import re
    base=Path(base)
    lines=[line.strip() for line in base.with_suffix('.hea').read_text(encoding='ascii').splitlines() if line.strip() and not line.startswith('#')]
    meta=lines[0].split()
    nch=int(meta[1]);fs=float(meta[2]);samples=int(meta[3])
    first=int(round((ALARM_SECOND-FEATURE_SECONDS)*fs));last=int(round(ALARM_SECOND*fs))
    if first<0 or last>samples or fs<50 or fs>1000:raise ValueError('Pre-alarm segment unavailable')
    names=[];gains=[];baselines=[]
    for line in lines[1:nch+1]:
        c=line.split()
        if len(c)<9 or c[0] != base.name+'.dat' or c[1]!='16':raise ValueError('Unsupported WFDB channel layout')
        m=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)(?:\((-?\d+)\))?/([a-zA-Z0-9.]+)',c[2])
        if not m:raise ValueError('Missing or unsupported WFDB ADC gain')
        gain=float(m.group(1)); baseline=int(m.group(2) if m.group(2) is not None else c[4])
        if not np.isfinite(gain) or gain<=0:raise ValueError('Invalid WFDB calibration')
        names.append(c[-1]);gains.append(gain);baselines.append(baseline)
    digital=np.memmap(base.with_suffix('.dat'),mode='r',dtype='<i2',shape=(samples,nch))
    raw=np.asarray(digital[first:last],dtype=float)
    missing=raw==-32768
    window=(raw-np.asarray(baselines))/np.asarray(gains)
    window[missing]=np.nan
    del digital
    return window,names,fs


def load_feature_rows(root, rows, cap=0):
    X=[];y=[];parts=[];identities=[];skipped=[];done=Counter()
    for row in rows:
        part=row['partition']
        if cap and done[part]>=cap:continue
        try:
            path=locate_waveform(root,row['record'],row['event'])
            verify_format16_waveform(path)
            signal,names,fs=physical_pre_alarm_window(path)
            features=extract_features(signal,names,fs,alarm_s=FEATURE_SECONDS)
            if not np.isfinite(np.asarray(features)).any():raise ValueError('No valid features')
        except (OSError,ValueError,FileNotFoundError,RuntimeError) as exc:
            skipped.append({'record':row['record'],'event':row['event'],'reason':str(exc)[:220]})
            continue
        X.append(features);y.append(row['y']);parts.append(part)
        identities.append(f"{row['record']}/{row['event']}");done[part]+=1
    return np.asarray(X,dtype=float).reshape((-1,len(FEATURE_NAMES))),np.asarray(y,dtype=int),np.asarray(parts),identities,skipped


def wilson(success,total):
    if not total:return None
    z=1.96;p=success/total;d=1+z*z/total
    center=(p+z*z/(2*total))/d
    half=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [round(float(max(0,center-half)),4),round(float(min(1,center+half)),4)]


def validation_threshold(y,prob,target=.95):
    """Select exploratory alarm-study threshold on validation ONLY; no test peeking."""
    from sklearn.metrics import confusion_matrix
    if len(set(y))!=2:raise ValueError('Both labels needed in validation')
    options=np.unique(np.r_[.01,.5,.99,np.clip(prob,.01,.99)])
    candidates=[]
    for th in options:
        tn,fp,fn,tp=confusion_matrix(y,prob>=th,labels=[0,1]).ravel()
        candidates.append((float(th),tp/(tp+fn),tn/(tn+fp)))
    good=[v for v in candidates if v[1]>=target]
    best=max(good,key=lambda v:(v[2],v[0])) if good else max(candidates,key=lambda v:(v[1],v[2],v[0]))
    return best[0],{'target_sensitivity':target,'reached':bool(good),'validation_sensitivity':best[1],'validation_specificity':best[2],
                     'disclaimer':'Exploratory threshold selected on validation ONLY. Not a clinical safety target.'}


def report_scores(y,prob,threshold=.5):
    from sklearn.metrics import confusion_matrix,roc_auc_score,average_precision_score,brier_score_loss
    tn,fp,fn,tp=confusion_matrix(y,prob>=threshold,labels=[0,1]).ravel()
    return {'n':len(y),'true':int(np.sum(y==1)),'false':int(np.sum(y==0)),
            'threshold':round(float(threshold),6),'tp':int(tp),'fn':int(fn),'tn':int(tn),'fp':int(fp),
            'sensitivity':round(float(tp/(tp+fn)),4) if tp+fn else None,
            'specificity':round(float(tn/(tn+fp)),4) if tn+fp else None,
            'precision_ppv':round(float(tp/(tp+fp)),4) if tp+fp else None,
            'sensitivity_wilson_95':wilson(tp,tp+fn),'specificity_wilson_95':wilson(tn,tn+fp),
            'auroc':round(float(roc_auc_score(y,prob)),4) if len(set(y))==2 else None,
            'auprc':round(float(average_precision_score(y,prob)),4) if len(set(y))==2 else None,
            'brier':round(float(brier_score_loss(y,prob)),4)}


def train(X, y, parts, identities, output, *, min_train=40, min_eval=10, smoke=False, dataset_version='unspecified'):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    if len(X) != len(y) or len(X) != len(parts) or len(X) != len(identities):
        raise ValueError('Training X, labels, partitions and record identities must align')
    if len(identities) != len(set(identities)):
        raise ValueError('Duplicate dataset event identities would cause leakage')
    patients = {}
    for identity, part in zip(identities, parts):
        if '/' not in identity or part not in ('train', 'validation', 'test'):
            raise ValueError('Malformed record identity or partition')
        patient = identity.split('/', 1)[0]
        if patient in patients and patients[patient] != part:
            raise ValueError('Patient-record leakage across partitions')
        patients[patient] = part
    if dataset_version not in ('1.0', '1.1', 'unspecified'):
        raise ValueError('Unrecognized VTaC dataset version')
    counts={name:int(np.sum(parts==name)) for name in ('train','validation','test')}
    for name,n in counts.items():
        minimum=4 if smoke else min_train if name=='train' else min_eval
        if n<minimum or len(set(y[parts==name]))<2:
            raise ValueError(f'{name} contains only {n} usable events or lacks both True and False; '
                             f'need >= {minimum} and both labels. Model not trained. '
                             'Run --audit, download more labelled records in the official split, and rerun.')
    training=X[parts=='train'].copy()
    valid=np.isfinite(training)
    medians=np.asarray([np.median(training[valid[:,j],j]) if valid[:,j].any() else 0. for j in range(X.shape[1])])
    train_imputed=np.where(valid,training,medians)
    scaler=StandardScaler()
    X_train=scaler.fit_transform(train_imputed)
    model=LogisticRegression(class_weight='balanced',C=.5,max_iter=1500,random_state=42)
    model.fit(X_train,y[parts=='train'])
    def predict(mask):
        x=X[mask].copy()
        x=np.where(np.isfinite(x),x,medians)
        return model.predict_proba(scaler.transform(x))[:,1]
    threshold,selection=validation_threshold(y[parts=='validation'],predict(parts=='validation'))
    scores={name:report_scores(y[parts==name],predict(parts==name),threshold) for name in ('train','validation','test')}
    provenance={'training_mode':'ARTIFICIAL SMOKE TEST - NOT VTaC PERFORMANCE' if smoke else 'RETROSPECTIVE VTaC RESEARCH BASELINE',
                'threshold':threshold,'threshold_selection':selection, 'feature_window_s':FEATURE_SECONDS,
                'alarm_onset_s':ALARM_SECOND,'counts':counts, 'results':scores,
                'train_patient_events_sha256':hashlib.sha256('\n'.join(sorted(k for i,k in enumerate(identities) if parts[i]=='train')).encode()).hexdigest(),
                'data_provenance':('VTaC source version ' + dataset_version +
                    '; local copies of official PhysioNet waveforms; official partitions asserted from CSV; '
                    'SHA256 manifest verification must be reported separately'),
                'data_version':dataset_version,
                'model_settings':{'algorithm':'LogisticRegression', 'C':0.5,'class_weight':'balanced',
                    'max_iter':1500,'random_state':42, 'scaler':'StandardScaler (train partition only)',
                    'imputation':'per-feature train-only median'},
                'environment':{'python':platform.python_version(),
                    'numpy':package_version('numpy'), 'scikit_learn':package_version('scikit-learn')},
                'dataset_scope':'exploratory subset unless full VTaC 5037-event integrity and coverage independently established',
                'research_only':True,'not_clinically_validated':True}
    output.mkdir(parents=True,exist_ok=True)
    temporary=output/'vt_model.unverified.json'
    artifact=export_model(model,medians,scaler.mean_,scaler.scale_,provenance,temporary)
    # Numerical parity test for independent runtime inference without sklearn/pickle.
    from waveassure.alarm_model import read_model
    loaded=read_model(temporary, internal_smoke_test=True)  # Training-process parity check ONLY; runtime still requires a pinned signature.
    for idx in range(min(5,len(X))):
        expected=float(predict(np.arange(len(X))==idx)[0])
        actual=assess(loaded,X[idx].tolist())['research_probability_true_vt']
        if abs(expected-actual)>2e-6:
            raise AssertionError('Exported runtime model parity failure')
    temporary.replace(output/'vt_model.json')
    (output/'metrics.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    with (output/'heldout_predictions.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.writer(handle);writer.writerow(['record_event','expert_label_true_vt','research_probability_true_vt','threshold'])
        mask=parts=='test'
        for event,reference,prob in zip(np.asarray(identities)[mask],y[mask],predict(mask)):
            writer.writerow([event,int(reference),format(float(prob),'.9f'),format(float(threshold),'.9f')])
    return provenance


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--dataset-version',choices=('1.0','1.1','unspecified'),default='unspecified',help='Actual downloaded waveform version, not metadata version')
    parser.add_argument('--output',default=Path('benchmark-results'),type=Path)
    parser.add_argument('--audit',action='store_true',help='Inspect official split and local file coverage without training')
    parser.add_argument('--max-per-split',type=int,default=0,help='Limit samples for development only, never published evaluation')
    parser.add_argument('--smoke',action='store_true',help='Allow tiny dataset as engineering test; do NOT publish results')
    args=parser.parse_args(argv)
    root=dataset_root(args.root)
    rows=split_rows(root)
    if args.audit:
        print(json.dumps(audit_data(root,rows),indent=2));return
    if args.max_per_split < 0:
        parser.error('max-per-split must be >= 0')
    if args.max_per_split and not args.smoke:
        parser.error('--max-per-split requires --smoke (never claim subset metrics as VTaC benchmark)')
    X,y,parts,identities,skipped=load_feature_rows(root,rows,args.max_per_split)
    print('Valid waveforms loaded by split:',dict(Counter(parts)))
    if skipped:
        print('Incomplete/invalid/unavailable event count:',len(skipped))
    provenance=train(X,y,parts,identities,args.output,smoke=args.smoke,dataset_version=args.dataset_version)
    (args.output/'skipped.json').write_text(json.dumps(skipped[:5000],indent=2),encoding='utf-8')
    print(json.dumps(provenance,indent=2))
    print('Research-only JSON model saved. NO live alarm control or medical use.')

if __name__=='__main__':
    main()
