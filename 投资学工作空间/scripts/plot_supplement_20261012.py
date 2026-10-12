from pathlib import Path
import json,argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=json.loads(a.inputs.read_text('utf8'));fontfile=Path('C:/Windows/Fonts/msyh.ttc');font=FontProperties(fname=str(fontfile)) if fontfile.exists() else FontProperties()
fig,ax=plt.subplots(1,2,figsize=(12,4.7));xs=[v['year'] for v in r]
for panel,key,title,label,color in [(ax[0],'company_asp','公司茅台酒产品组均价','万元/公司销售吨','#1f6c8b'),(ax[1],'quote','21年飞天散瓶行情字段','原CSV数值，单位待补','#b45a46')]:
 ys=[float(v[key]) for v in r];panel.plot(xs,ys,marker='o',color=color,linewidth=2);panel.set_xticks(xs);panel.set_title(title,fontproperties=font,fontsize=13);panel.set_ylabel(label,fontproperties=font);panel.grid(axis='y',alpha=.2)
 for x,y in zip(xs,ys):panel.annotate(f'{y:.2f}',(x,y),textcoords='offset points',xytext=(0,9),ha='center',fontsize=10)
 panel.margins(y=.22);panel.spines[['top','right']].set_visible(False)
fig.text(.5,.02,'两图对象和计量不同；公司组均价不等于固定SKU净价。CSV为附件候选，未新增学生Fact。',ha='center',fontproperties=font,fontsize=10)
fig.tight_layout(rect=(0,.08,1,1));a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=150);plt.close(fig)
