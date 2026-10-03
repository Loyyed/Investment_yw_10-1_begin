"""Regenerate only managed views of human-confirmed change evidence."""
import json,re
from pathlib import Path
from change_review import ChangeReviewStore

def table(headers,rows):
 clean=lambda s:str(s).replace('|','\\|').replace('\n','；')
 return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
  ['| '+' | '.join(clean(v) for v in row)+' |' for row in rows])

def managed(text,body):
 start='<!-- change-review:progress:start -->'
 end='<!-- change-review:progress:end -->'
 new=start+'\n'+body.rstrip()+'\n'+end
 pattern=re.compile(re.escape(start)+'.*?'+re.escape(end),re.S)
 return pattern.sub(lambda m:new,text) if pattern.search(text) else text.rstrip()+'\n\n'+new+'\n'

def sync_change_views(workspace):
 root=Path(workspace)
 authority=root/'evidence/change-review-state.json'
 if not authority.exists():return []
 store=ChangeReviewStore(root)
 records=store.list_records()
 facts=[r for r in records if r['state']=='Fact']
 ledger=json.loads(authority.read_text(encoding='utf-8'))
 updated=[]
 def save(relative,content):
  path=root/relative
  if not path.exists() or path.read_text(encoding='utf-8-sig')!=content:
   store.review._atomic_text(path,content)
   updated.append(relative)
 export={'schema_version':1,'authority':'evidence/change-review-state.json','updated_at':ledger.get('updated_at',''),
  'fact_count':len(facts),'records':records,'facts':facts,
  'usage_rule':'Recheck ReviewStore.change_facts(); this is a derived view, not confirmation authority.'}
 save('evidence/change-confirmed-facts.json',json.dumps(export,ensure_ascii=False,indent=2)+'\n')
 headers=['编号','指标','2024本期数（元）','2023比较数（元）','同比百分比','定位','有效状态']
 rows=[[r['id'],r['metric'],r['current'],r['previous'],r['percent']+'%',r.get('location','2024PDF第63/64页；第5页交叉核对'),
        r['state']+('：'+r['stale_reason'] if r.get('stale_reason') else '')] for r in records]
 summary=f'当前有效变化Fact：{len(facts)}/2条。原披露Fact及窗口事件单独保留；来源、输入或可比性改变时，本栏将显示Unknown。'
 body='## 当前变化核验状态\n\n'+summary+'\n\n'+table(headers,rows)+'\n\n'
 body+='公式：（本期－比较期）÷比较期×100，展示为百分比；ROUND_HALF_UP保留两位小数。两期均为人民币元、合并口径，2024年度对同份2024年报的2023比较列。\n\n'
 body+='本人确认原话与上下文见[变化确认账本](../evidence/change-review-state.json)；后续调用ReviewStore.change_facts()重新核对来源绑定。变化最多说明方向和幅度，不证明价格、销量、需求、品牌或竞争优势的因果机制。'
 for relative in ['work/change-verification.md','outputs/change-verification-record.md']:
  path=root/relative
  if path.exists():save(relative,managed(path.read_text(encoding='utf-8-sig'),body))
 fact_rows=[]
 for r in facts:
  fact_rows.append([r['id'],f"2024年{r['metric']}较2023年同口径比较数增加{r['percent']}%",'Fact',
   '2024指定PDF；SHA-256='+r.get('pdf_sha256',''), '2024年度／2023年比较列',r.get('location','第63/64页；第5页交叉核对'),
   r['current']+'；比较数'+r['previous']+'；同比'+r['percent']+'%', '人民币元，集团合并；百分比',
   '只支持同口径变化方向与幅度','不能证明经营机制、预测、估值或买卖结论',
   '姓名待补；聊天确认登记'+r.get('confirmed_at',''),'签署待补；其他Unknown按需处理'])
 log_body='## 第四次任务：当前有效变化证据\n\n'+summary+'\n\n'
 log_body+=table(['编号','主张','类型','来源版本','报告期／比较基数','精确定位','原文或数值摘要','单位与口径',
   '支持边界','不能支持什么','人工核验','待解决问题'],fact_rows)+'\n\n'
 log_body+='来源：[变化确认账本](change-review-state.json)；[派生导出](change-confirmed-facts.json)。本次实际聊天原话为“核对完毕”，所指范围由上一条核验步骤保存；登记时间不冒充实际逐页核验开始时间。'
 path=root/'evidence/evidence-log.md'
 save('evidence/evidence-log.md',managed(path.read_text(encoding='utf-8-sig'),log_body))
 calc=root/'work/change-recalculation.json'
 if calc.exists():
  payload=json.loads(calc.read_text(encoding='utf-8-sig'))
  decorated=store.annotate_calculation(payload)
  save('work/change-recalculation.json',json.dumps(decorated,ensure_ascii=False,indent=2)+'\n')
 return updated
