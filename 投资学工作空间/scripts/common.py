from pathlib import Path
from decimal import Decimal
import json
W=Path(__file__).resolve().parents[1]
D=json.loads((W/'work/structured-data.json').read_text(encoding='utf-8'))
STATUS='> Agent定位、PDF原值对照和结构检查已完成；人工核验为待核验，候选披露仍为Unknown。本人核验并签认后才能升级Fact。人名及签署日期按用户要求留空。\n'
def write(p,t):
 f=W/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(t.strip()+'\n',encoding='utf-8')
def table(h,rows):
 def c(x):return str(x).replace('|','／').replace('\n','；')
 return '| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+'\n'.join('| '+' | '.join(c(x) for x in r)+' |' for r in rows)+'\n'
def money(x):return f'{Decimal(x):,.2f}'
