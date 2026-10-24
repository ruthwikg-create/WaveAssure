"""Run with: python -m uvicorn waveassure.api:app --host 127.0.0.1 --port 8000"""
from __future__ import annotations
from pathlib import Path
import ipaddress
import os
import secrets
from urllib.parse import urlsplit
from fastapi import Request
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from . import __version__
from .schemas import RecordCreate, FaultRequest, CSVImport
from pydantic import BaseModel, Field
from .wfdb_input import import_local_wfdb, configured_root
from .signals import analyze, demo_record, inject_fault, preview
from .evidence import create_evidence
from .report_html import report_html
from .storage import save, get, list_records, verify, audit_rows, StorageIntegrityError
from .csv_input import parse_csv
from .alarm_model import read_model, assess, features_from_record
from .reviewer_pilot import NewSession, Decision, open_session, get_session, case_preview, submit_decision, finalize, export_report



ROOT=Path(__file__).resolve().parent.parent
RESEARCH_MODEL_PATH = ROOT / 'models' / 'vtac' / 'vt_model.json'  # installation-controlled local JSON
app=FastAPI(title='WaveAssure Research Workbench',version=__version__,
    description='Offline-first technical waveform assurance; NOT FOR CLINICAL USE.',
    docs_url=None, redoc_url=None)
app.mount('/static',StaticFiles(directory=str(ROOT/'web')),name='static')

@app.exception_handler(StorageIntegrityError)
async def evidence_failure(_request: Request, _error: StorageIntegrityError):
    # Preserve a controlled fail-closed response instead of leaking a traceback.
    return JSONResponse({'detail': 'Local research evidence integrity failed; action blocked.'},
                        status_code=409, headers=_SECURITY_HEADERS)


# Fail closed for LAN/WAN requests and DNS-rebinding attempts. This is a local
# research workbench, NOT an authenticated or internet-hostable application.
_ALLOWED_HTTP_HOSTS = {'localhost', '127.0.0.1', '::1', 'testserver'}
_SECURITY_HEADERS = {
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Content-Security-Policy': (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"),
}


def _is_loopback(peer: str) -> bool:
    if peer == 'testclient':  # Starlette in-process test fixture; not a real socket peer.
        return True
    try:
        return ipaddress.ip_address(peer).is_loopback
    except (ValueError, TypeError):
        return False


def _allowed_host(host_header: str) -> bool:
    try:
        parsed = urlsplit('http://' + host_header)
        return (parsed.hostname in _ALLOWED_HTTP_HOSTS
                and parsed.username is None and parsed.password is None
                and (parsed.port is None or 1 <= parsed.port <= 65535)
                and not parsed.path and not parsed.query and not parsed.fragment)
    except ValueError:
        return False


@app.middleware('http')
async def local_only_security(request: Request, call_next):
    mode = os.environ.get('WAVEASSURE_WORKSPACE_MODE', 'engineering').lower()
    if mode not in {'engineering', 'review'}:
        return JSONResponse({'detail': 'Invalid operational mode; access denied'}, status_code=503, headers=_SECURITY_HEADERS)
    if mode == 'review':
        # Dedicated review process: the entire engineering API (and its ground-
        # truth labels) is unreachable through this server, even if a reviewer
        # manually invokes the endpoint instead of using the user interface.
        allowed = (request.url.path == '/' or request.url.path == '/api/health'
                   or request.url.path.startswith('/static/')
                   or request.url.path.startswith('/api/pilot/'))
        if not allowed:
            return JSONResponse({'detail': 'Engineering API unavailable in dedicated review mode'}, status_code=403, headers=_SECURITY_HEADERS)
        if request.url.path.startswith('/api/pilot/'):
            secret = os.environ.get('WAVEASSURE_REVIEW_KEY', '')
            supplied = request.headers.get('x-waveassure-review-key', '')
            if len(secret) < 32 or not secrets.compare_digest(supplied, secret):
                return JSONResponse({'detail': 'Reviewer authorization required'}, status_code=401, headers=_SECURITY_HEADERS)
    peer = request.client.host if request.client else ''
    host = request.headers.get('host', '')
    if not _is_loopback(peer) or not _allowed_host(host):
        return JSONResponse({'detail': 'Local-only research application; network access denied'}, status_code=403, headers=_SECURITY_HEADERS)
    origin = request.headers.get('origin')
    if origin:
        try:
            target = urlsplit(origin)
            origin_host = target.hostname
            host_port = urlsplit('http://' + host).port
            if (target.scheme not in {'http', 'https'}
                or origin_host != urlsplit('http://' + host).hostname
                or target.port != host_port):
                return JSONResponse({'detail': 'Cross-origin requests are not permitted'}, status_code=403, headers=_SECURITY_HEADERS)
        except ValueError:
            return JSONResponse({'detail': 'Invalid Origin header'}, status_code=403, headers=_SECURITY_HEADERS)
    length = request.headers.get('content-length')
    if length:
        try:
            if int(length) > 10_000_000 or int(length) < 0:
                return JSONResponse({'detail': 'Request body exceeds the 10 MB limit'}, status_code=413, headers=_SECURITY_HEADERS)
        except ValueError:
            return JSONResponse({'detail': 'Invalid Content-Length header'}, status_code=400, headers=_SECURITY_HEADERS)
    response = await call_next(request)
    response.headers.update(_SECURITY_HEADERS)
    return response


@app.get('/',include_in_schema=False)
def home():return FileResponse(ROOT/'web'/('review.html' if os.environ.get('WAVEASSURE_WORKSPACE_MODE', 'engineering').lower()=='review' else 'index.html'))

@app.get('/api/health')
def health():return {'status':'ok','version':__version__,'intended_use':'research_only','alarm_control':'none','live_monitoring':False, 'workspace_mode':os.environ.get('WAVEASSURE_WORKSPACE_MODE', 'engineering')}

@app.get('/api/records')
def records():return {'items':list_records()}

@app.post('/api/demo',status_code=201)
def demo(kind:str=Query(default='baseline',pattern='^(baseline|tachy_simulation|artifact)$')):
    record=demo_record(kind)
    return {'id':save(record),'source':'SYNTHETIC / NOT PATIENT DATA'}

@app.post('/api/records',status_code=201)
def create_record(payload:RecordCreate):
    if payload.origin!='synthetic':
        raise HTTPException(400,'Use dedicated controlled import workflow for non-synthetic data')
    # Never allow caller-supplied expert ground-truth labels or source lineage on synthetic records.
    cleaned = payload.model_copy(update={'reference_label': 'Unlabeled', 'source_reference': 'User-provided synthetic research data (unverified)'})
    return {'id':save(cleaned)}

@app.post('/api/import-csv',status_code=201)
def import_csv(payload:CSVImport):
    try: record=parse_csv(payload)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    return {'id':save(record),'warning':'Research-use local CSV, not validated or de-identified by this software.'}

class WFDBImportRequest(BaseModel):
    record_path: str = Field(min_length=1, max_length=220)

@app.get('/api/wfdb/config')
def wfdb_config():
    root=configured_root()
    return {'configured':root.is_dir(), 'root':str(root),
            'supported':'WFDB single shared file, little-endian format 16, max 8 supported channels',
            'clinical_use':False}

@app.post('/api/import-wfdb',status_code=201)
def import_wfdb(payload:WFDBImportRequest):
    try: record=import_local_wfdb(payload.record_path)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    return {'id':save(record),'origin':'wfdb_research','reference_label':record.reference_label,
            'note':'The reference label is NOT an AI prediction.'}

@app.get('/api/records/{record_id}/preview')
def record_preview(record_id:str, start_s:float=Query(default=0,ge=0,le=600), window_s:float=Query(default=30,ge=2,le=600)):
    try: source=get(record_id)
    except ValueError as exc: raise HTTPException(409, 'Stored record integrity check failed') from exc
    if not source: raise HTTPException(404,'Record not found')
    return {'waveforms':preview(source['record'], start_s=start_s, window_s=window_s)}

@app.get('/api/records/{record_id}')
def get_record(record_id:str):
    try: result=get(record_id)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc
    if not result:raise HTTPException(404,'Record not found')
    record=result['record']
    return {'metadata':result['metadata'],'analysis':analyze(record),
            'waveforms':preview(record,start_s=max(0,min(285, len(record.channels[0].samples)/record.sample_rate_hz-30)) if record.origin=='wfdb_research' else 0, window_s=30 if record.origin=='wfdb_research' else None),
            'reference_label':record.reference_label,
            'sampling_hz':record.sample_rate_hz,'source_reference':record.source_reference,
            'full_sample_count':len(record.channels[0].samples)}

@app.post('/api/records/{record_id}/fault',status_code=201)
def apply_fault(record_id:str, fault:FaultRequest):
    try: source=get(record_id)
    except ValueError as exc: raise HTTPException(409, 'Stored record integrity check failed') from exc
    if not source:raise HTTPException(404,'Record not found')
    try: altered=inject_fault(source['record'],fault)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    out=save(altered,parent_id=record_id,fault=fault.model_dump_json())
    return {'id':out,'parent_id':record_id,'description':'Injected educational signal fault; no clinical interpretation'}

@app.get('/api/records/{record_id}/evidence')
def evidence(record_id: str):
    try: source = get(record_id)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    if not source: raise HTTPException(404, 'Record not found')
    return create_evidence(source['record'], source['metadata'], verify())

@app.get('/api/records/{record_id}/report.html')
def printable_report(record_id: str):
    try: source = get(record_id)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    if not source: raise HTTPException(404,'Record not found')
    data = create_evidence(source['record'],source['metadata'],verify())
    return HTMLResponse(report_html(data))

@app.get('/api/records/{record_id}/report')
def report(record_id:str):
    try: source=get(record_id)
    except ValueError as exc: raise HTTPException(409, 'Stored record integrity check failed') from exc
    if not source:raise HTTPException(404,'Record not found')
    record=source['record']
    document = create_evidence(record, source['metadata'], verify())
    return JSONResponse(document,headers={'Content-Disposition':f'attachment; filename="waveassure-{record_id[:8]}-evidence.json"'})


@app.get('/api/research-model/status')
def research_model_status():
    try:
        model = read_model(RESEARCH_MODEL_PATH)
    except (FileNotFoundError, ValueError, OSError, KeyError, TypeError) as exc:
        return {'available':False, 'status':'NOT TRAINED / NOT INSTALLED',
                'reason':str(exc)[:200], 'clinical_use':False}
    return {'available':True,'status':'LOCAL RETROSPECTIVE RESEARCH MODEL',
            'sha256':model['sha256'],'provenance':model['provenance'], 'model_attestation':model.get('attestation'),
            'warning':'Not clinically validated; no alarm suppression, diagnosis, or bedside monitoring.'}

@app.post('/api/records/{record_id}/research-assessment')
def research_assessment(record_id:str):
    try:
        model=read_model(RESEARCH_MODEL_PATH)
    except (FileNotFoundError, ValueError, OSError, KeyError, TypeError) as exc:
        raise HTTPException(409, 'No verified locally generated research model installed: '+str(exc)[:140]) from exc
    try:
        result=get(record_id)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc
    if not result:
        raise HTTPException(404,'Record not found')
    record=result['record']
    if record.origin!='wfdb_research' or result['metadata']['parent_id'] is not None:
        raise HTTPException(422,'Only original imported research WFDB recordings are eligible; not synthetic, CSV, or fault-injected signals.')
    try:
        features=features_from_record(record)
        output=assess(model,features,enforce_signal_quality=True)
    except (ValueError,IndexError) as exc:
        raise HTTPException(422,'Cannot extract compatible pre-alarm research features: '+str(exc)) from exc
    # Expert labels are shown separately, never used as feature input or as ground truth for a specific patient decision.
    return {'assessment':output,'reference_label':record.reference_label,
            'record_id':record_id, 'scope':'retrospective research evaluation only',
            'alarm_control':'disabled', 'clinical_use':False}

@app.get('/api/audit')
def audit():return {'events':audit_rows(),'verification':verify()}

@app.get('/api/requirements')
def requirements():
    return {'requirements':[
      {'id':'SWR-001','description':'Import synthetic signal or locally de-identified CSV with consistent samples'},
      {'id':'SWR-002','description':'Reject invalid units and timestamps'},
      {'id':'SWR-003','description':'Perform research signal-quality checks'},
      {'id':'SWR-004','description':'Inject deterministic signal faults without overwriting source'},
      {'id':'SWR-005','description':'Preserve waveform provenance and checksum'},
      {'id':'SWR-006','description':'Provide hash-linked audit trail'},
      {'id':'SWR-007','description':'Prohibit clinical alarm classification and alarm suppression; gate research model behind offline explicit action'},
      {'id':'SWR-008','description':'Export versioned technical evidence reports'},
      {'id':'SWR-009','description':'Validate locally imported WFDB format-16 recordings before analysis'},
      {'id':'SWR-010','description':'Preserve calibrated lead identities and distinguish labels from predictions'},
      {'id':'SWR-011','description':'Reject unsupported, partial or mismatched research-model JSON'},
      {'id':'SWR-012','description':'Do not assess synthetic, derived or non-WFDB records with research VT model'},
      {'id':'SWR-013','description':'Every clinical-style output must disclose provenance, data/measurement source and scope'},
      {'id':'SWR-014','description':'Never carry an expert reference alarm label into a modified derived recording'},
      {'id':'SWR-015','description':'Produce pre- and post-alarm descriptive measurements without unvalidated diagnosis'}]}


# Offline retrospective reviewer usability pilot. Not a clinical trial and no secure blinding.
@app.post('/api/pilot/sessions',status_code=201)
def pilot_create(payload:NewSession):
    try:return open_session(payload)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.get('/api/pilot/sessions/{sid}')
def pilot_status(sid:str):
    try:return get_session(sid)
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc

@app.get('/api/pilot/sessions/{sid}/cases/{rid}')
def pilot_case(sid:str,rid:str):
    try:return case_preview(sid,rid)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.post('/api/pilot/sessions/{sid}/responses',status_code=201)
def pilot_response(sid:str,payload:Decision):
    try:return submit_decision(sid,payload)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.post('/api/pilot/sessions/{sid}/finalize')
def pilot_finalize(sid:str):
    try:return finalize(sid)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.get('/api/pilot/sessions/{sid}/export')
def pilot_export(sid:str):
    try:return export_report(sid)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc
