"""SQLite local-only persistence and hash-linked engineering audit trail."""
from __future__ import annotations
import os, sqlite3, json, gzip, hashlib, uuid, zlib
from pydantic import ValidationError
from datetime import datetime, timezone
from pathlib import Path
from .schemas import RecordCreate

DB_PATH = Path(os.environ.get('WAVEASSURE_DB', str(Path.home()/'.waveassure'/'workbench.sqlite3')))

def _now(): return datetime.now(timezone.utc).isoformat()
def _canonical(d): return json.dumps(d, sort_keys=True, separators=(',',':'), ensure_ascii=False)
def _digest(d): return hashlib.sha256(_canonical(d).encode('utf-8')).hexdigest()

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db=sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('''CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, title TEXT NOT NULL, origin TEXT NOT NULL,
        parent_id TEXT, fault TEXT, payload BLOB NOT NULL, data_sha256 TEXT NOT NULL,
        FOREIGN KEY(parent_id) REFERENCES records(id))''')
    db.execute('''CREATE TABLE IF NOT EXISTS audit (
        seq INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, event TEXT NOT NULL,
        object_id TEXT NOT NULL, details TEXT NOT NULL, previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL)''')
    db.commit()
    return db

class StorageIntegrityError(ValueError):
    """Stored evidence or hash-link consistency has failed; never silently continue."""


def _verify_audit_in_connection(db):
    previous = 'GENESIS'
    count = 0
    for row in db.execute('SELECT * FROM audit ORDER BY seq'):
        try:
            details = json.loads(row['details'])
            expected = _digest(dict(timestamp=row['timestamp'],event=row['event'],
                                    object_id=row['object_id'],details=details,
                                    previous_hash=row['previous_hash']))
        except (ValueError, TypeError, KeyError) as exc:
            raise StorageIntegrityError('Audit history contains invalid event metadata') from exc
        if row['previous_hash'] != previous or row['entry_hash'] != expected:
            raise StorageIntegrityError(f'Audit history integrity failed at sequence {row["seq"]}')
        previous = row['entry_hash']
        count += 1
    return count, previous


def _append(db, event, obj_id, details):
    # Fail closed on an altered audit history. This is still NOT a signed audit
    # system: a privileged database administrator could rewrite the whole chain.
    _verify_audit_in_connection(db)
    last=db.execute('SELECT entry_hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
    prev=last['entry_hash'] if last else 'GENESIS'
    d=dict(timestamp=_now(), event=event, object_id=obj_id, details=details, previous_hash=prev)
    db.execute('INSERT INTO audit(timestamp,event,object_id,details,previous_hash,entry_hash) VALUES (?,?,?,?,?,?)',
               (d['timestamp'],event,obj_id,_canonical(details),prev,_digest(d)))

def save(record: RecordCreate, parent_id=None, fault=None) -> str:
    raw=_canonical(record.model_dump()).encode('utf-8')
    raw_hash=hashlib.sha256(raw).hexdigest()
    obj_id=uuid.uuid4().hex
    db=connect()
    try:
        with db:
            db.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?)',
                       (obj_id,_now(),record.title,record.origin,parent_id,fault,gzip.compress(raw),raw_hash))
            _append(db,'record.created',obj_id,dict(origin=record.origin,source_sha256=raw_hash,parent_id=parent_id,fault=fault))
    finally: db.close()
    return obj_id

def get(obj_id: str):
    db=connect()
    try:
        row=db.execute('SELECT * FROM records WHERE id=?',(obj_id,)).fetchone()
        if row is None: return None
        try:
            raw = gzip.decompress(row['payload'])
        except (gzip.BadGzipFile, EOFError, OSError, zlib.error, TypeError) as exc:
            raise StorageIntegrityError('Stored record payload cannot be decompressed') from exc
        if hashlib.sha256(raw).hexdigest() != row['data_sha256']:
            raise StorageIntegrityError('Record checksum does not match stored evidence')
        try:
            record = RecordCreate.model_validate_json(raw)
        except (ValidationError, ValueError, TypeError) as exc:
            raise StorageIntegrityError('Stored record schema is invalid') from exc
        if record.title != row['title'] or record.origin != row['origin']:
            raise StorageIntegrityError('Stored record metadata disagrees with evidence payload')
        return dict(metadata={k:row[k] for k in ('id','created_at','title','origin','parent_id','fault','data_sha256')}, record=record)
    finally: db.close()

def list_records():
    db=connect()
    try:
        return [dict(r) for r in db.execute('SELECT id,created_at,title,origin,parent_id,fault,data_sha256 FROM records ORDER BY created_at DESC LIMIT 75').fetchall()]
    finally: db.close()

def verify():
    db = connect()
    try:
        try:
            count, last = _verify_audit_in_connection(db)
        except StorageIntegrityError as exc:
            return dict(ok=False, warning=str(exc),
                        limitation='Not independently signed or externally timestamped')
        return dict(ok=True, events_checked=count, last_hash=last,
                    warning='Local hash chain only; privileged modification or deletion is not independently detectable.')
    finally:
        db.close()


def audit_rows():
    db=connect()
    try: return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY seq DESC LIMIT 75')]
    finally: db.close()
