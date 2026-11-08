"""Independent consistency checks for this planning baseline. Python 3.9+."""
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))
wbs={r['wbs_id']:r for r in rows('lr07_wbs/wbs.csv')}
parents={r['parent_id'] for r in wbs.values() if r['parent_id']}
for k,r in wbs.items():
    children=[x for x in wbs.values() if x['parent_id']==k]
    if children: assert float(r['estimate_hours'])==sum(float(x['estimate_hours']) for x in children)
leaves=set(wbs)-parents
tasks={r['task_id']:r for r in rows('lr07_wbs/schedule.csv')}
pred={k:[p for p in r['predecessors'].split(';') if p] for k,r in tasks.items()}
es={};ef={};order=[]
while len(order)<len(tasks):
    ready=[k for k in tasks if k not in ef and all(p in ef for p in pred[k])]
    assert ready,'Cycle or missing predecessor'
    for k in ready:
        es[k]=max([ef[p] for p in pred[k]] or [0]);ef[k]=es[k]+int(tasks[k]['duration_days']);order.append(k)
end=max(ef.values());ls={};lf={}
for k in reversed(order):
    successors=[s for s in tasks if k in pred[s]]
    lf[k]=min([ls[s] for s in successors] or [end]);ls[k]=lf[k]-int(tasks[k]['duration_days'])
    assert int(tasks[k]['float_days'])==ls[k]-es[k],k
    assert tasks[k]['is_critical']==('yes' if ls[k]==es[k] else 'no'),k
assert {t['wbs_id'] for t in tasks.values()}==leaves
details={r['task_id']:r for r in rows('lr07_wbs/calendar_details.csv')}
for k,r in details.items():
    assert [int(r[c]) for c in ('es','ef','ls','lf')]==[es[k],ef[k],ls[k],lf[k]]
for leaf in leaves:
    assert float(wbs[leaf]['estimate_hours'])==sum(float(details[k]['effort_hours']) for k,t in tasks.items() if t['wbs_id']==leaf)
caps={'PM':4,'BA':8,'Dev1':8,'Dev2':8,'QA':4}
for day in range(end):
    for role,cap in caps.items():
        load=sum(float(r['effort_hours'])/int(tasks[k]['duration_days']) for k,r in details.items() if r['role']==role and es[k]<=day<ef[k])
        assert load<=cap+1e-9,(day,role,load)
backlog=rows('lr06_backlog/backlog.csv');rel1={r['story_id'] for r in backlog if r['release']=='REL-1'}
covered={sid for r in details.values() for sid in r['story_ids'].split(';') if sid}
assert rel1<=covered
votes=rows('lr08_poker/votes.csv');est=rows('lr08_poker/estimates.csv')
assert {r['story_id'] for r in est}==rel1
assert len({(r['story_id'],r['round'],r['voter']) for r in votes})==len(votes)
scale=[0,1,2,3,5,8,13,21]
for e in est:
    v=[r for r in votes if r['story_id']==e['story_id']]
    rnd=max(int(r['round']) for r in v);assert rnd==int(e['rounds'])
    final={r['voter']:int(r['vote']) for r in v if int(r['round'])==rnd}
    assert set(final)=={'optimistic','likely','pessimistic'}
    o,m,p=[final[k] for k in ('optimistic','likely','pessimistic')];assert o<=m<=p
    pert=(o+4*m+p)/6;assert abs(int(e['final_estimate'])-pert)<=min(abs(x-pert) for x in scale)+1e-9
print('PASS: WBS totals, leaf coverage, CPM, resource capacity, story coverage, PERT.')
print(f'WBS: {wbs["1"]["estimate_hours"]} hours; schedule: {end} working days; REL-1: {len(rel1)} stories / {sum(int(e["final_estimate"]) for e in est)} SP.')
