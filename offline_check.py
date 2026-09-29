"""Inspect the public sent-target fixture without opening any hardware port."""
import json
from pathlib import Path

def main():
    p=Path(__file__).with_name('recorded_prefix_fixture.json')
    if not p.exists():
        raise SystemExit('Extract microduck-source-20260929.zip first; the fixture is inside it.')
    d=json.loads(p.read_text(encoding='utf8'));rows=d['frames']
    assert len(rows)==250 and all(set(r['sent_targets'])==set(map(str,range(1,16))) for r in rows)
    assert all(r['sent_targets']==d['r3'] for r in rows[:150])
    assert all(0<=v<=4095 for r in rows for v in r['sent_targets'].values())
    print(json.dumps(dict(scope='OFFLINE_ONLY_NO_SERIAL_NO_SSH',frames=len(rows),prepare=150,action=100,
        raw_target_range={str(i):[min(r['sent_targets'][str(i)] for r in rows),max(r['sent_targets'][str(i)] for r in rows)] for i in range(1,16)}),indent=2))

if __name__=='__main__':main()
