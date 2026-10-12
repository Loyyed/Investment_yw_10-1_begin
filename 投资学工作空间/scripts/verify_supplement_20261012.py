from pathlib import Path
import json,csv,hashlib,sys
from decimal import Decimal,ROUND_HALF_UP
import argparse
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
w=args.workspace.resolve();base=(args.inputs or w/'work/20261012-supplement').resolve();sup=w.parent/'课件与任务文件/补充材料'
source=sup/'白酒行业_iFinD字段全集_上市以来.csv'
a=json.loads((base/'analysis.json').read_text('utf8'));s=json.loads((base/'selected-observations.json').read_text('utf8'));p=json.loads((base/'python-profile.json').read_text('utf8'));j=json.loads((base/'csv-profile.json').read_text('utf8'))
checks=[]
def chk(name,condition):
 if not condition:raise ValueError(name)
 checks.append({'check':name,'passed':True})
D=Decimal
chk('两解析器条数一致',p['records']==j['records']==138652)
chk('两解析器序列数一致',p['series_count']==j['series']==538)
chk('两解析器重复/冲突均0',p['duplicate_records']==j['duplicate_keys']==0 and p['conflicting_records']==j['conflict_keys']==0)
chk('主/后续窗口分开',p['included_by_observation_date']+p['after_observation_cutoff']==p['records'])
with source.open(encoding='utf-8-sig',newline='') as f:
 rr=csv.DictReader(f);rows={i+2:r for i,r in enumerate(rr)}
for r in s['records']:
 raw=rows[r['source_line']]
 chk('原行绑定'+str(r['source_line']),all(raw[k]==r[k] for k in rr.fieldnames))
sys.path.insert(0,str(w/'scripts'))
from review_store import ReviewStore
fresh={r['id']:r for r in ReviewStore(w).lec03_agent_facts()}
for r in a['inventory']:
 current=fresh[r['annual_record_id']]['data']['physical_inventory']
 chk('库存原报告绑定'+str(r['year']),D(r['pdf_finished'])==D(current['finished_tonnes']) and D(r['pdf_semi'])==D(current['semi_finished_tonnes']))
for r in a['inventory']:chk('库存合计'+str(r['year']),D(r['csv_value'])==D(r['pdf_finished'])+D(r['pdf_semi']))
for r in a['volmatch']:chk('销售量交叉'+r['id']+str(r['year']),D(r['csv_value'])==D(r['pdf_value']))
price=(D('2400')/D('2810')-1)*100
chk('报价同比Decimal复算',str(price.quantize(D('.01'),rounding=ROUND_HALF_UP))==a['priceChange']['percent'])
for r in a['industry']:
 current,rate,prior=[rows[k]['value'] for k in r['source_lines']]
 expected=(D(current)/D(prior)-1)*100
 chk('行业机械比'+str(r['year']),str(expected.quantize(D('.01'),rounding=ROUND_HALF_UP))==r['mechanical_yoy'])
win=json.loads((base/'window-counts.json').read_text('utf8'))
chk('主会计期条数',sum('2020-01-01'<=r['time']<='2024-12-31' for r in rows.values())==win['main']['records'])
chk('更早历史条数',sum(r['time']<'2020-01-01' for r in rows.values())==win['earlier_history']['records'])
chk('后续跟踪条数',sum(r['time']>'2024-12-31' for r in rows.values())==win['later_followup']['records'])
chk('主期晚更新条数',sum('2020-01-01'<=r['time']<='2024-12-31' and r['rtime'][:10]>'2024-12-31' for r in rows.values())==win['main']['updated_after_period_end'])
# 讲义188页：把损失0.3的投资占比f，与输光风险本金的下注比例x=f*0.3分开。
pv,g,l=D('.9'),D('3'),D('.3');x=pv-(1-pv)/(g/l);f=pv/l-(1-pv)/g
chk('凯利归一化风险本金比例',x==D('.89'))
chk('凯利比例单位转换',abs(f*l-x)<D('1e-25'))
chk('期望回报两案例',pv*g-(1-pv)*l==D('2.67') and D('.1')*D('.1')-D('.9')*D('.8')==D('-.71'))
for r in a['annualFactory']:
 selected=[rows[line] for line in r['source_lines']]
 mean=sum(D(v['value']) for v in selected)/D(len(selected))
 chk('出厂观测均值'+str(r['year']),abs(mean-D(str(r['unweighted_observation_mean'])))<D('1e-9'))
protected=json.loads((base/'protected-before.json').read_text('utf8'))
chk('旧原件与权威保持',all(hashlib.sha256((w/k).read_bytes()).hexdigest()==v for k,v in protected.items()))
for r in json.loads((base/'reading-manifest.json').read_text('utf8')):chk('补充原件SHA '+r['name'],hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'])
res={'date':'2026-10-12','checks':checks,'count':len(checks),'kelly':{'risked_capital_fraction':str(x),'unconstrained_investment_fraction':str(f),'no_leverage_math_domain':[0,1],'actual_portfolio_decision':'不生成'},'old_authority_preserved':True,'source_fingerprint':j['sha256']}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8');print({'checks':len(checks),'passed':True,'source_unchanged':True})
