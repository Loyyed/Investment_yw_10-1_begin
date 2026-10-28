from pathlib import Path
import re
W=Path(__file__).resolve().parents[1];p=W/'outputs/证券投资分析研究图册_V2.2.html'
t=p.read_text(encoding='utf8');t=re.sub(r'<section id="lec05".*?</section>','',t,flags=re.S)
c=(W/'work/lec05-20261028/atlas-chapter.html').read_text(encoding='utf8')
if 'href="#lec05"' not in t:t=t.replace('</nav>','<a href="#lec05">Lec05 · 三项新成果</a></nav>',1)
assert '</main>' in t
p.write_text(t.replace('</main>',c+'</main>',1),encoding='utf8')
