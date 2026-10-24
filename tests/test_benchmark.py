import csv
import pytest
from benchmarks.train_vtac import split_rows

def write(path,headers,rows):
    with path.open('w',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=headers);writer.writeheader();writer.writerows(rows)

def test_official_partition_preserved(tmp_path):
    labels=[dict(record=f'p{i}',event=f'e{i}',decision='True' if i%2 else 'False') for i in range(6)]
    splits=[dict(record=r['record'],event=r['event'],split='train' if i<2 else 'validation' if i<4 else 'test') for i,r in enumerate(labels)]
    write(tmp_path/'event_labels.csv',['record','event','decision'],labels)
    write(tmp_path/'benchmark_data_split.csv',['record','event','split'],splits)
    assert len(split_rows(tmp_path))==6

def test_refuse_patient_leak(tmp_path):
    write(tmp_path/'event_labels.csv',['record','event','decision'],[
      dict(record='patientA',event='e1',decision='True'),dict(record='patientA',event='e2',decision='False')])
    write(tmp_path/'benchmark_data_split.csv',['record','event','split'],[
      dict(record='patientA',event='e1',split='train'),dict(record='patientA',event='e2',split='test')])
    with pytest.raises(ValueError,match='leakage'):split_rows(tmp_path)
