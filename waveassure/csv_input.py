"""Strict local CSV import. Reject identifying columns and untrusted time axes."""
import csv, io, math
from .schemas import Channel, RecordCreate, CSVImport

CHANNEL_HEADERS={"ECG_mV":("ECG","mV"),"PPG_au":("PPG","a.u."),"ABP_mmHg":("ABP","mmHg")}

def parse_csv(data: CSVImport) -> RecordCreate:
    reader=csv.DictReader(io.StringIO(data.csv_text))
    header=reader.fieldnames
    if not header or 'time_s' not in header or len(header)!=len(set(header)):
        raise ValueError('CSV needs unique headers including time_s')
    unknown=set(header)-{'time_s',*CHANNEL_HEADERS.keys()}
    if unknown: raise ValueError('Unsupported columns (including identifiers) forbidden: '+', '.join(sorted(unknown)))
    chosen=[key for key in CHANNEL_HEADERS if key in header]
    if not chosen: raise ValueError('CSV requires ECG_mV, PPG_au or ABP_mmHg')
    times=[];columns={k:[] for k in chosen}
    for row in reader:
        if len(times)>=100_000: raise ValueError('CSV maximum 100000 samples')
        if None in row: raise ValueError('Row has extra fields')
        try:
            t=float(row['time_s'])
            if not math.isfinite(t): raise ValueError('Nonfinite time')
            times.append(t)
            for k in chosen:
                raw=row[k]
                n=None if raw is None or not raw.strip() else float(raw)
                if n is not None and not math.isfinite(n):raise ValueError('Nonfinite sample')
                columns[k].append(n)
        except (TypeError,ValueError) as exc:
            raise ValueError(f'Invalid numeric value at sample {len(times)}') from exc
    if len(times)<100: raise ValueError('At least 100 samples required')
    dt=[b-a for a,b in zip(times,times[1:])]
    if any(x<=0 for x in dt):raise ValueError('Time must increase strictly')
    mid=sorted(dt)[len(dt)//2]
    if mid<=0 or any(abs(x-mid)>mid*.02 for x in dt):
        raise ValueError('Sampling intervals must be uniform within 2%')
    fs=1/mid
    channels=[Channel(kind=CHANNEL_HEADERS[k][0],unit=CHANNEL_HEADERS[k][1],samples=columns[k]) for k in chosen]
    return RecordCreate(title=data.title,sample_rate_hz=fs,channels=channels,
                        origin='local_csv_unverified', source_reference='Local CSV; user responsible for de-identification and source validation')
