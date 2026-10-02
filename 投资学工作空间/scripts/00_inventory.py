from pathlib import Path
import sys, json, zipfile, hashlib, shutil, importlib.util, os
sys.stdout.reconfigure(encoding='utf-8')
WS=Path(__file__).resolve().parents[1]
from workspace_utils import original_source_root, guard_generated_writes
ROOT=original_source_root(WS)
guard_generated_writes(WS, "00_inventory.py")
for d in ['sources/original-tree','sources/unpacked','sources/annual_reports/md','sources/annual_reports/pdf','tasks','work','evidence','outputs','docs/images','config','tests']:
    (WS/d).mkdir(parents=True,exist_ok=True)
items=[]
prior_inventory = WS/'work/source-inventory.json'
if prior_inventory.exists():
    original_paths = [ROOT/item['path'] for item in json.loads(prior_inventory.read_text(encoding='utf-8'))['files']]
else:
    original_paths = [p for p in ROOT.rglob('*') if not any(part in ['review-ui-build', '投资学工作空间'] for part in p.relative_to(ROOT).parts)]
for p in sorted(original_paths):
    if not p.is_file() or WS in p.parents or '.git' in p.parts: continue
    b=p.read_bytes(); rel=p.relative_to(ROOT)
    meta='__MACOSX' in p.parts or p.name in ['.DS_Store'] or p.name.startswith('._')
    items.append({'path':str(rel),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'metadata_only':meta})
    if not meta:
        target=WS/'sources/original-tree'/rel
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
archives=[]
for p in ROOT.glob('*.zip'):
    base=WS/'sources/unpacked'/p.stem
    with zipfile.ZipFile(p) as z:
        for info in z.infolist():
            name=info.filename
            if not info.flag_bits&0x800:
                try: name=name.encode('cp437').decode('utf-8')
                except (UnicodeError,LookupError):
                    try: name=name.encode('cp437').decode('gb18030')
                    except UnicodeError: pass
            name=name.replace('\\','/')
            parts=Path(name).parts
            meta='__MACOSX' in parts or Path(name).name=='.DS_Store' or Path(name).name.startswith('._')
            archives.append({'archive':p.name,'member':name,'bytes':info.file_size,'metadata_only':meta})
            if meta or info.is_dir(): continue
            target=(base/name).resolve()
            if not target.is_relative_to(base.resolve()): raise ValueError('Unsafe ZIP member '+name)
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(info))
reports=ROOT/'学生用/贵州茅台年报_2020-2024'
for kind in ['md','pdf']:
    for p in (reports/kind).glob('*.'+kind): shutil.copy2(p,WS/'sources/annual_reports'/kind/p.name)
modules=['pandas','numpy','fitz','pypdf','pdfplumber','matplotlib','openpyxl','nbformat','bs4','yaml','jupyter','PIL']
env={'python':sys.executable,'version':sys.version,'modules':{m:bool(importlib.util.find_spec(m)) for m in modules},'conda_meta':(Path(sys.prefix)/'conda-meta').exists()}
(WS/'work/source-inventory.json').write_text(json.dumps({'files':items,'archives':archives,'environment':env},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(env,ensure_ascii=False,indent=2))
print('ORIGINAL FILES',len(items),'ARCHIVE ENTRIES',len(archives))
for p in sorted((WS/'sources/unpacked').rglob('*')):
    if p.is_file(): print(str(p.relative_to(WS)),p.stat().st_size)
