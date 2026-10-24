from waveassure import storage

def test_health_and_not_clinical(client):
    response=client.get('/api/health')
    assert response.status_code==200
    assert response.json()['live_monitoring'] is False
    assert 'Not for clinical use' in client.get('/').text

def test_demo_fault_report(client):
    created=client.post('/api/demo?kind=baseline')
    assert created.status_code==201
    record_id=created.json()['id']
    result=client.get('/api/records/'+record_id).json()
    assert result['metadata']['origin']=='synthetic'
    assert result['analysis']['alarm_classification']['status']=='NOT_AVAILABLE'
    changed=client.post('/api/records/'+record_id+'/fault',json={'kind':'dropout','target':'ECG','severity':.8})
    assert changed.status_code==201
    derived=client.get('/api/records/'+changed.json()['id']).json()
    assert derived['metadata']['parent_id']==record_id
    assert derived['analysis']['status']=='REVIEW_REQUIRED'
    assert client.get('/api/records/'+record_id).json()['analysis']['status']=='TECHNICAL_CHECKS_PASSED'
    report=client.get('/api/records/'+changed.json()['id']+'/report')
    assert report.status_code==200
    assert report.json()['record']['parent_id']==record_id
    assert len(client.get('/api/records').json()['items'])==2

def test_audit_verify_and_detect_manual_tampering(client):
    client.post('/api/demo?kind=baseline')
    assert client.get('/api/audit').json()['verification']['ok']
    db=storage.connect();db.execute("UPDATE audit SET event='modified' WHERE seq=1");db.commit();db.close()
    assert not client.get('/api/audit').json()['verification']['ok']

def test_security_reject_uncontrolled_create(client):
    payload={'title':'fake','origin':'wfdb_research','sample_rate_hz':250,
      'channels':[{'kind':'ECG','unit':'mV','samples':[0]*100}]}
    assert client.post('/api/records',json=payload).status_code==400

def test_nonexistent_record(client):
    assert client.get('/api/records/missing').status_code==404

def test_requirements(client):
    data=client.get('/api/requirements').json()
    assert len(data['requirements'])>=8
