from common import *
from decimal import ROUND_HALF_UP
import sys
from review_store import ReviewStore

def verified_change(current,previous,conditions):
 if not all(conditions.get(k) is True for k in ['report_version','periods','unit_currency','reporting_entity','consolidation_scope','metric_definition','no_restatement']): raise ValueError('人工可比性未全部确认：停止计算，保留Unknown')
 a,b=Decimal(current),Decimal(previous)
 if b==0:raise ValueError('比较基数为零：停止计算，保留Unknown')
 return ((a-b)/b*100).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)

def main():
 if sys.stdout is not None: sys.stdout.reconfigure(encoding='utf-8')
 review=json.loads((W/'config/human-review.json').read_text(encoding='utf-8'))
 result=[]
 try:
  store=ReviewStore(W)
  snapshot=store.comparison_snapshot()
  if store.validate_comparability(expected_binding=snapshot["binding"]) is not True: raise ValueError("尚未完成来源一致的人工可比性确认")
  for metric in ['营业收入','归属于上市公司股东的净利润']:
   r=next(x for x in snapshot['rows'] if x['metric']==metric)
   rate=verified_change(r['current'],r['previous'],review['human_confirmation'])
   result.append({'metric':metric,'current':r['current'],'previous':r['previous'],'source_binding':snapshot['binding'],'formula':'(current-previous)/previous*100','percent':str(rate),'rounding':'ROUND_HALF_UP 2 decimal places','state':'Unknown','note':'公式复算结果仍待本人核验，不自动成为Fact'})
 except ValueError as e:
  write('work/change-recalculation.json',json.dumps({'status':'stopped','reason':str(e),'results':[]},ensure_ascii=False,indent=2));print(str(e));return 2
 write('work/change-recalculation.json',json.dumps({'status':'calculated-awaiting-human-verification','results':result},ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
