"""Maintain current output navigation. Never copy history into outputs."""
from pathlib import Path
import json,hashlib,html
W=Path(__file__).resolve().parents[1];O=W/'outputs'
def category(p):
 if p.startswith('01_路演与讲稿/'):return '路演与讲稿'
 if p.startswith('02_Lec05'):return 'Lec05新成果'
 if p.startswith('03_方法与图表/'):return '方法与图表'
 if p.endswith(('.xlsx','.csv','.json')):return '复算与数据'
 if p.endswith('.md') and p!='README.md':return '专题与核验'
 return '当前综合成果'
rows=[dict(path=p.relative_to(O).as_posix(),category=category(p.relative_to(O).as_posix()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['文件目录.json','00_从这里开始.html']]
def a(p,t):return '<a href="'+html.escape(p,quote=True)+'">'+html.escape(t)+'</a>'
css='body{font:17px/1.9 Microsoft YaHei,sans-serif;background:#f3f5f0;color:#173f38;margin:0}main{max-width:1100px;margin:auto;padding:40px 24px}h1{font-size:36px}a{color:#126b61}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.cards a{background:white;border:1px solid #becfc2;border-radius:10px;padding:22px;display:block;text-decoration:none;font-size:21px}details{margin:20px 0;padding:20px;background:white;border:1px solid #ccd8cc;border-radius:10px}summary{cursor:pointer;font-size:21px}li{overflow-wrap:anywhere}'
main=[('01_路演与讲稿/投资分析系统与茅台研究_首次听众路演V2.5.html','路演 V2.5'),('01_路演与讲稿/投资分析系统与茅台研究_首次听众讲稿V2.5.html','配套讲稿'),('证券投资分析研究图册_V2.2.html','当前研究图册'),('研究结论与合同回答_V2.2.html','综合研究与合同回答'),('02_Lec05叙事与估值/index.html','Lec05三项成果'),('全任务合同核查与覆盖清单.html','原合同覆盖清单')]
body='<h1>投资研究成果</h1><p>先选当前成果，再按用途查找专题。历史版本保存在GitHub，不放在本目录。</p><div class="cards">'+''.join(a(p,t) for p,t in main)+'</div>'
for cat in ['方法与图表','专题与核验','复算与数据','当前综合成果']:
 items=[r for r in rows if r['category']==cat and not r['path'].endswith(('.png','.svg'))]
 body+='<details><summary>'+cat+' · '+str(len(items))+'</summary><ul>'+''.join('<li>'+a(r['path'],Path(r['path']).name)+'</li>' for r in items)+'</ul></details>'
body+='<p>'+a('../docs/20261028-output-policy.md','目录规则与历史恢复')+' · '+a('文件目录.json','全部文件与指纹')+'</p>'
(O/'00_从这里开始.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>投资研究成果</title><style>'+css+'</style><main>'+body+'</main></html>',encoding='utf8')
portal=O/'00_从这里开始.html';rows.append(dict(path=portal.name,category='当前综合成果',bytes=portal.stat().st_size,sha256=hashlib.sha256(portal.read_bytes()).hexdigest()))
(O/'文件目录.json').write_text(json.dumps(dict(date='2026-10-28',policy='current outputs only; history in GitHub; no physical backups',files=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
