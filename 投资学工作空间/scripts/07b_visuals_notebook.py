from common import *
from workspace_utils import guard_generated_writes
guard_generated_writes(W, "07b_visuals_notebook.py")
import os,sys
from PIL import Image,ImageDraw,ImageFont
import nbformat
sys.stdout.reconfigure(encoding='utf-8')
FONT='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(FONT,n)
def base(title,sub):
 im=Image.new('RGB',(1600,960),'#f5f7fa'); d=ImageDraw.Draw(im)
 d.text((65,44),title,font=font(43),fill='#132b49');d.text((67,112),sub,font=font(24),fill='#536578');return im,d

def box(d,xy,title,lines,accent='#236d9d'):
 x,y,x2,y2=xy;d.rounded_rectangle(xy,radius=17,fill='white',outline='#cfdae5',width=2);d.rounded_rectangle((x,y,x+9,y2),radius=4,fill=accent)
 d.text((x+27,y+19),title,font=font(29),fill='#18344b')
 for i,t in enumerate(lines):d.text((x+27,y+67+i*37),t,font=font(24),fill='#526578')

def arrow(d,a,b):
 d.line([a,b],fill='#3c7594',width=4);x,y=b
 if abs(b[0]-a[0])>abs(b[1]-a[1]):poly=[(x,y),(x-13*(1 if b[0]>a[0] else -1),y-8),(x-13*(1 if b[0]>a[0] else -1),y+8)]
 else:poly=[(x,y),(x-8,y-13),(x+8,y-13)]
 d.polygon(poly,fill='#3c7594')
im,d=base('投资学工作空间｜材料、过程与成果','按课程工作台模板落地；原始资料与研究产物分别保存')
boxes=[((65,180,785,360),'sources/｜原始材料',['五年PDF、检索MD、课件与工具参考','原样保留 + SHA-256；原件不改动']),((825,180,1535,360),'tasks/ + 项目规则',['前四次合同 + Lec03命题合同','README、CLAUDE、AGENTS明确边界']),((65,395,785,575),'work/｜过程与候选',['提取表、口径冲突、检索与修正','Unknown与63条证据候选']),((825,395,1535,575),'evidence/｜本人核验',['证据日志 + 本人核验表','当前人工签认Fact：0条']),((65,610,785,790),'outputs/｜阶段成果',['收入结构、口径卡、变化记录准备','商业模式矩阵与课程提交准备包']),((825,610,1535,790),'docs/ + scripts/ + .git/',['图片说明、复现脚本、研究Notebook','本地版本与检查；无需远程仓库'])]
for xy,t,ls in boxes:box(d,xy,t,ls)
d.text((65,855),'关键边界：自动核对 ≠ 学生本人核验；签名及正式关闭留给本人。',font=font(27),fill='#986527')
im.save(W/'docs/images/workspace-structure.png')
im,d=base('工作流程｜从课件到可核验的任务链','已完成整理与自动检查；人工证据确认作为清晰的下一步')
steps=[('1 清点与解压',['六个压缩包','读取正文、登记用途']),('2 定位原披露',['五年657页PDF','记录版本、页、表、口径']),('3 结构与口径',['51条收入成本候选','区分主营、全部收入、主体']),('4 变化核验准备',['保留代入式与披露比例','人工可比性未确认则停止']),('5 商业模式命题',['六条机制候选与反证','行业、资本、现金流问题']),('6 本人核验签署',['确认Fact与Unknown','登记证据编号、补签合同'])]
for i,(t,ls) in enumerate(steps):
 row=i//3;col=i%3 if row==0 else 2-i%3;x=65+col*500;y=190+row*270
 box(d,(x,y,x+465,y+205),t,ls,'#c39136' if i==5 else '#236d9d')
 if row==0 and col<2:arrow(d,(x+470,y+102),(x+495,y+102))
 if row==1 and col>0:arrow(d,(x-5,y+102),(x-30,y+102))
arrow(d,(1460,405),(1460,445))
d.text((65,795),'每一步留底稿与Unknown → 保存Git版本 → 可以重新定位、比较和继续研究',font=font(28),fill='#314d66')
d.text((65,850),'本人未核验前，不把候选披露标成Fact，不将年报数字直接升级为投资结论。',font=font(25),fill='#986527')
im.save(W/'docs/images/workflow.png')
im,d=base('商业模式经济逻辑｜贵州茅台研究命题','箭头为待检验联系；依据2024年报，待学生核验与机制裁决')
parts=[('收入',['销量 × 同口径价格','产品组合与渠道结构','酒类 + 其他业务']),('成本与费用',['粮食、人工、制造、物流','营销与渠道费用另列','高毛利不等于低成本']),('资本投入',['产能与在建项目','基酒储存、存货占用','新增产能不等于即期销售']),('现金转换',['收款与营运资本时点','财务公司资金流影响','利润与自由现金流不同'])]
for i,(t,ls) in enumerate(parts):
 x=65+i*382;box(d,(x,245,x+350,500),t,ls)
 if i<3:arrow(d,(x+356,373),(x+376,373))
box(d,(65,575,790,770),'解释与替代解释',['品牌溢价、结构变化、渠道分配','供给限制、库存节奏、金融资金归集'])
box(d,(830,575,1535,770),'后续验证与反证',['同规格量价、竞品、费用与资本回报','终端价差收窄、动销下降、现金转化弱化'])
d.text((65,850),'证据来源：2024年PDF第7—10、14、63—64、108页；均保留原文指针。',font=font(25),fill='#536578')
im.save(W/'docs/images/business-model.png')
# Reproducible notebook without pretending human approval.
nb=nbformat.v4.new_notebook()
nb.metadata={'kernelspec':{'display_name':'Python (Anaconda investments)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.4'}}
nb.cells=[nbformat.v4.new_markdown_cell('# 投资学研究笔记\n\n仅使用指定年报数据。候选披露仍为Unknown；不要把执行Notebook当成本人证据核验。'),nbformat.v4.new_code_cell("from pathlib import Path\nimport json, sys\nimport pandas as pd\nworkspace = Path.cwd()\nif not (workspace / 'work/structured-data.json').exists(): workspace = workspace.parent\ndata = json.loads((workspace / 'work/structured-data.json').read_text(encoding='utf-8'))\nprint(sys.executable)\nprint('收入成本候选:', len(data['structure']) + len(data['full_structure']))"),nbformat.v4.new_code_cell("structure = pd.DataFrame(data['full_structure'] + data['structure'])\nstructure.loc[structure.year == 2024, ['id','dimension','item','revenue_raw','cost_raw','scope','pdf_pages','state']]"),nbformat.v4.new_code_cell("checks = pd.DataFrame(data['reconciliations'])\nassert checks['pass'].all()\nprint('分项合计检查通过:', len(checks))\nchecks"),nbformat.v4.new_markdown_cell('## 原文入口\n\n2024年收入见PDF63页，归母利润64页，全部营业收入分解108页；酒类分解9页。2022利润重述见2023年5及86页。'),nbformat.v4.new_code_cell("review = json.loads((workspace / 'config/human-review.json').read_text(encoding='utf-8'))\nprint('人工可比性确认:', review['human_confirmation'])\nprint('全部确认前不执行正式变化计算。')"),nbformat.v4.new_markdown_cell('## 下一步\n\n本人逐行核验后填写证据日志；口径可比性确认后运行 scripts/07_compute_changes.py。它不会自动改写人工证据。')]
nbformat.write(nb,W/'research.ipynb')
print('Three diagrams and research.ipynb generated')
