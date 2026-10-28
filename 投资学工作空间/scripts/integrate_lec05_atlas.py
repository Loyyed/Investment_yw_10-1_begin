from pathlib import Path
import re
from html.parser import HTMLParser
W=Path(__file__).resolve().parents[1];p=W/'outputs/证券投资分析研究图册_V2.2.html'
t=p.read_text(encoding='utf8')
class Locator(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=False);self.text=text;self.lines=[0];self.depth=0;self.start=None;self.end=None
  for i,c in enumerate(text):
   if c=='\n':self.lines.append(i+1)
 def pos(self):a,b=self.getpos();return self.lines[a-1]+b
 def handle_starttag(self,tag,attrs):
  if tag=='section':
   if dict(attrs).get('id')=='lec05' and self.start is None:self.start=self.pos();self.depth=1
   elif self.depth:self.depth+=1
 def handle_endtag(self,tag):
  if tag=='section' and self.depth:
   self.depth-=1
   if not self.depth:self.end=self.pos()+len('</section>')
loc=Locator(t);loc.feed(t)
c=(W/'work/lec05-20261028/atlas-chapter.html').read_text(encoding='utf8')
if loc.start is not None:t=t[:loc.start]+t[loc.end:]
source=re.search(r'<section\b[^>]*\bid=["\\\']sources["\\\']',t)
if source:t=t[:source.start()]+c+t[source.start():]
else:t=t.replace('</main>',c+'</main>',1)
nav=re.search(r'<nav\b[^>]*>.*?</nav>',t,re.S)
if nav:
 body=nav.group(0)
 entry=re.search(r'<a\b[^>]*href=["\\\']#lec05["\\\'][^>]*>.*?</a>',body,re.S)
 item=entry.group(0) if entry else '<a href="#lec05"><span>09</span>Lec05 · 完整任务与延伸</a>'
 if entry:body=body[:entry.start()]+body[entry.end():]
 anchor=re.search(r'<a\b[^>]*href=["\\\']#sources["\\\']',body)
 if anchor:body=body[:anchor.start()]+item+body[anchor.start():]
 else:body=body.replace('</nav>',item+'</nav>',1)
 t=t[:nav.start()]+body+t[nav.end():]
p.write_text(t,encoding='utf8')
