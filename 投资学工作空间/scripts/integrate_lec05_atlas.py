from pathlib import Path
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
if loc.start is not None:t=t[:loc.start]+c+t[loc.end:]
else:t=t.replace('</main>',c+'</main>',1)
if 'href="#lec05"' not in t:t=t.replace('</nav>','<a href="#lec05">Lec05 · 完整任务与延伸</a></nav>',1)
p.write_text(t,encoding='utf8')
