# Isolated local retrospective review process — engineering control, not clinical blinding

The default engineering server contains expert reference labels and can be viewed by the data owner.
Use this **separate process** for local usability rehearsal only. Do not run the engineering
server in front of study reviewers, and do not claim independent blinding or ethics approval.

## Windows

Install via `scripts\start-windows.bat` once, stop with Ctrl+C, then open PowerShell:

```powershell
cd D:\WaveAssure-v0.9\WaveAssure
$env:WAVEASSURE_REVIEW_KEY = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
$env:WAVEASSURE_WORKSPACE_MODE = 'review'
.\.venv\Scripts\python.exe -m uvicorn waveassure.api:app --host 127.0.0.1 --port 8001
```

Go to `http://127.0.0.1:8001` and enter the generated secret into the reviewer form.
It remains valid for this local process only. Keep it out of screenshots/logs.

Prior to launching review mode, the **research data custodian** must import cases in
engineering mode and stop that server. This does not stop someone with filesystem or
administrator access from seeing local database labels. The separate research reviewer
service has no engineering API endpoints and requires a shared secret on pilot routes.
It is not independent, validated clinical blinding. A hospital study needs separately
managed participant accounts, an external assessor, protected label custody, ethics
oversight, and a validated protocol.
