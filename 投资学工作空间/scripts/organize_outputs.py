from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];O=W/'outputs'
rows=[dict(path=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='文件目录.json']
(O/'文件目录.json').write_text(json.dumps(dict(date='2026-10-28',policy='current only; history in Git; bound evidence stays in place',files=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
