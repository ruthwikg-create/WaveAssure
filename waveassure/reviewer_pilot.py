"""Offline retrospective clinician-review usability pilot. NOT a clinical trial.

No identifiable reviewer names and no patient care. Dataset labels intentionally excluded
from review responses until finalization; this is not access-control-grade blinding because
WaveAssure's engineering API can expose reference labels on the same localhost instance.
"""
from __future__ import annotations
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
from . import storage
from .signals import preview

class NewSession(BaseModel):
    reviewer_code: str = Field(min_length=3,max_length=32,pattern=r'^[A-Za-z0-9_-]+$')

class Decision(BaseModel):
    record_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    decision: Literal['True','False','Indeterminate']
    confidence: Literal['low','medium','high']
    quality: Literal['adequate','limited','uninterpretable']
    notes: str = Field(default='',max_length=600)


def _date(): return datetime.now(timezone.utc).isoformat()


def _init(db):
    db.execute('''CREATE TABLE IF NOT EXISTS pilot_sessions(
        id TEXT PRIMARY KEY, reviewer_code TEXT NOT NULL, created_at TEXT NOT NULL,
        completed_at TEXT, case_ids_json TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS pilot_responses(
        session_id TEXT NOT NULL, record_id TEXT NOT NULL, decision TEXT NOT NULL,
        confidence TEXT NOT NULL, quality TEXT NOT NULL, notes TEXT NOT NULL,
        submitted_at TEXT NOT NULL, PRIMARY KEY(session_id,record_id),
        FOREIGN KEY(session_id) REFERENCES pilot_sessions(id))''')
    db.execute('''CREATE TABLE IF NOT EXISTS pilot_case_snapshots(
        session_id TEXT NOT NULL, record_id TEXT NOT NULL, data_sha256 TEXT NOT NULL,
        PRIMARY KEY(session_id,record_id),
        FOREIGN KEY(session_id) REFERENCES pilot_sessions(id))''')
    db.commit()


def _assert_case_snapshot(db, sid, rid):
    snap=db.execute('SELECT data_sha256 FROM pilot_case_snapshots WHERE session_id=? AND record_id=?',
                    (sid,rid)).fetchone()
    if snap is None:
        raise ValueError('Case evidence snapshot absent; session cannot safely proceed')
    source=storage.get(rid)
    if (source is None or source['metadata']['data_sha256'] != snap['data_sha256']
        or source['record'].origin != 'wfdb_research' or source['metadata']['parent_id'] is not None):
        raise ValueError('Case data has changed since this review session was created')
    return source


def _load(db, session_id):
    s=db.execute('SELECT * FROM pilot_sessions WHERE id=?',(session_id,)).fetchone()
    if not s:raise ValueError('Reviewer session not found')
    return dict(s)


def _snapshot(db, session):
    ids=json.loads(session['case_ids_json'])
    finished={r['record_id'] for r in db.execute('SELECT record_id FROM pilot_responses WHERE session_id=?',(session['id'],))}
    return {'id':session['id'],'reviewer_code':session['reviewer_code'],
            'created_at':session['created_at'],'completed':bool(session['completed_at']),
            'total_cases':len(ids),'completed_cases':len(finished),
            'cases':[{'record_id':rid,'case_number':i+1,'reviewed':rid in finished} for i,rid in enumerate(ids)]}


def open_session(payload:NewSession):
    db=storage.connect()
    try:
        _init(db)
        candidates=db.execute('''SELECT id FROM records WHERE origin='wfdb_research' AND parent_id IS NULL
            ORDER BY id LIMIT 100''').fetchall()
        ids=[]
        digests={}
        for row in candidates:
            try:
                source=storage.get(row['id'])
                if (source is not None and source['record'].origin=='wfdb_research'
                    and len(source['record'].channels[0].samples)/source['record'].sample_rate_hz>=300):
                    ids.append(row['id'])
                    digests[row['id']]=source['metadata']['data_sha256']
            except (ValueError, OSError):
                continue  # Never place malformed/short records in a reviewer session.
        if not ids:raise ValueError('Import at least one intact, de-identified 300-second WFDB research record first')
        sid=uuid.uuid4().hex
        with db:
            db.execute('INSERT INTO pilot_sessions VALUES(?,?,?,?,?)',
                       (sid,payload.reviewer_code,_date(),None,json.dumps(ids)))
            for rid in ids:
                db.execute('INSERT INTO pilot_case_snapshots VALUES (?,?,?)', (sid,rid,digests[rid]))
            storage._append(db,'pilot.session.open',sid,{'case_count':len(ids),'reviewer_code_hash':hashlib.sha256(payload.reviewer_code.encode()).hexdigest()})
        return _snapshot(db,_load(db,sid))
    finally: db.close()


def get_session(sid):
    db=storage.connect()
    try:
        _init(db);return _snapshot(db,_load(db,sid))
    finally:db.close()


def case_preview(sid,rid):
    db=storage.connect()
    try:
        _init(db)
        s=_load(db,sid)
        if rid not in json.loads(s['case_ids_json']):raise ValueError('Case is not included in this session')
        case=_assert_case_snapshot(db,sid,rid)
        record=case['record']
        # Pre-alarm-only view: never return data after 300 seconds or the dataset label.
        duration=len(record.channels[0].samples)/record.sample_rate_hz
        if duration < 300:raise ValueError('This recording is too short for pre-alarm review')
        waveforms=preview(record,start_s=285,window_s=15,max_points=600)
        return {'record_id':rid,'case_number':json.loads(s['case_ids_json']).index(rid)+1,
                'waveforms':waveforms,'window_s':[285,300],
                'description':'15 s before annotated alarm; reference label hidden in reviewer route',
                'reference_label_included':False,'model_prediction_included':False,
                'limitation':'Workflow label masking only. This is not secure or independently blinded.'}
    finally:db.close()


def submit_decision(sid,payload:Decision):
    db=storage.connect()
    try:
        _init(db)
        s=_load(db,sid)
        if s['completed_at']:raise ValueError('Finalized sessions are immutable')
        if payload.record_id not in json.loads(s['case_ids_json']):raise ValueError('Case not in the session')
        _assert_case_snapshot(db,sid,payload.record_id)
        if any(ord(c)<32 and c not in '\t\n' for c in payload.notes):raise ValueError('Invalid note characters')
        if re.search(r'\b(?:@|https?://|\+\d{8,})\b',payload.notes,re.I):
            raise ValueError('Do not include contact information or identifiers')
        try:
            with db:
                db.execute('''INSERT INTO pilot_responses VALUES(?,?,?,?,?,?,?)''',
                           (sid,payload.record_id,payload.decision,payload.confidence,payload.quality,payload.notes,_date()))
                storage._append(db,'pilot.review.submitted',payload.record_id,
                                {'session_id':sid,'decision':payload.decision,'confidence':payload.confidence,'quality':payload.quality})
        except __import__('sqlite3').IntegrityError as exc:
            raise ValueError('Case already reviewed; decisions cannot be changed') from exc
        return _snapshot(db,s)
    finally:db.close()


def finalize(sid):
    db=storage.connect()
    try:
        _init(db);s=_load(db,sid)
        if s['completed_at']:return _snapshot(db,s)
        total=len(json.loads(s['case_ids_json']))
        completed=db.execute('SELECT COUNT(*) AS n FROM pilot_responses WHERE session_id=?',(sid,)).fetchone()['n']
        if completed!=total:raise ValueError(f'Review every case before finalizing ({completed}/{total})')
        # Do not finalize a comparison against recordings changed mid-session.
        for rid in json.loads(s['case_ids_json']):
            _assert_case_snapshot(db,sid,rid)
        with db:
            db.execute('UPDATE pilot_sessions SET completed_at=? WHERE id=?',(_date(),sid))
            storage._append(db,'pilot.session.finalized',sid,{'cases':total})
        return _snapshot(db,_load(db,sid))
    finally:db.close()


def export_report(sid):
    db=storage.connect()
    try:
        _init(db);s=_load(db,sid)
        if not s['completed_at']:raise ValueError('Complete and finalize the review before accessing reference labels')
        answers=[dict(r) for r in db.execute('SELECT * FROM pilot_responses WHERE session_id=? ORDER BY record_id',(sid,))]
        rows=[]; counts={'TP':0,'TN':0,'FP':0,'FN':0,'indeterminate':0,'unlabelled':0}
        for ans in answers:
            origin=_assert_case_snapshot(db,sid,ans['record_id'])
            label=origin['record'].reference_label
            decision=ans['decision']
            if label not in ('True','False'):counts['unlabelled']+=1
            elif decision=='Indeterminate':counts['indeterminate']+=1
            else:
                tag={('True','True'):'TP',('True','False'):'FN',('False','False'):'TN',('False','True'):'FP'}[(label,decision)]
                counts[tag]+=1
            rows.append({'case_id':ans['record_id'],'reviewer_decision':decision,'reference_label':label,
                         'quality':ans['quality'],'confidence':ans['confidence'],'notes':ans['notes']})
        pos=counts['TP']+counts['FN'];neg=counts['TN']+counts['FP']
        report={'report_type':'offline_reviewer_usability_pilot_v1','session_id':sid,
                'reviewer_code':s['reviewer_code'],'created_at':s['created_at'],
                'finalized_at':s['completed_at'],'cases':rows,'counts':counts,
                'descriptive_sensitivity':counts['TP']/pos if pos>=30 else None,
                'descriptive_specificity':counts['TN']/neg if neg>=30 else None,
                'clinical_validation':False,'ai_model_assessed':False,
                'notes':['Clinician manual responses, not AI model metrics',
                  'Insufficient diversity/size cannot establish medical performance',
                  'Numerical sensitivity and specificity suppressed when either reference class has fewer than 30 reviewed cases; counts are descriptive only',
                  'Dedicated reviewer mode isolates engineering endpoints; no independent clinical blinding is established',
                  'Not an independently blinded or ethics-approved clinical investigation',
                  'Not for diagnosing, suppressing alarms, or treating patients']}
        canonical=json.dumps(report,sort_keys=True,separators=(',',':'))
        report['report_sha256']=hashlib.sha256(canonical.encode()).hexdigest()
        return report
    finally: db.close()
