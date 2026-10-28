from decimal import Decimal as D, getcontext
import json
getcontext().prec=40
out=[]
for label,ss in [('原路径',['.20','.30','.40','.45']),('延迟路径',['.20','.25','.30','.40'])]:
 prev=None
 for y,s in enumerate(ss):
  p=D(100)*(1-D(s))+D(150)*D(s);r=100*p
  out.append(dict(path=label,year=y,asp=str(p),revenue=str(r),growth=None if prev is None else str(r/prev-1)));prev=r
print(json.dumps(dict(paths=out,pv=str(D(220)/D('1.10')),equity=str(D(1500)+110+60-280-75),per_share=str((D(1500)+110+60-280-75)/100)),ensure_ascii=False,indent=2))
