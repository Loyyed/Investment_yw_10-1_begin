"""Portable source location and protection for human review records."""
from pathlib import Path
import json, re, subprocess, hashlib

GIT = Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')

def original_source_root(workspace):
    workspace = Path(workspace)
    config = workspace / 'config/workspace.json'
    if config.exists():
        value = json.loads(config.read_text(encoding='utf-8')).get('original_source_root')
        if value:
            return Path(value).resolve()
    sibling = workspace.parent / '课件与任务文件'
    if sibling.is_dir():
        return sibling.resolve()
    if workspace.parent.name == '课件与任务文件':
        return workspace.parent.resolve()
    raise ValueError('请在config/workspace.json指定原件目录original_source_root。')

def contract_intact(actual, original):
    """Allow normal form completion and formatting; retain substantive clauses."""
    body = actual.split('## 本工作空间执行说明', 1)[0]
    body = re.sub(r'\s*---\s*$', '', body)
    blank_labels = set()
    for line in original.splitlines():
        match = re.fullmatch(r'(\s*-\s*\*\*[^*]+\*\*\s*[：:])\s*', line)
        if match:
            blank_labels.add(re.sub(r'\s+', '', match.group(1)))
    def normalize(text):
        lines = []
        for line in text.splitlines():
            match = re.match(r'(\s*-\s*\*\*[^*]+\*\*\s*[：:])(.*)$', line)
            if match and re.sub(r'\s+', '', match.group(1)) in blank_labels:
                line = match.group(1)
            line = re.sub(r'\[[xX]\]', '[ ]', line)
            if re.match(r'^(document_status|updated):', line):
                line = line.split(':', 1)[0] + ': [填写栏]'
            for key in ('执行人签署', '复核人签署', '日期'):
                line = re.sub(r'(\*\*'+key+r'\*\*[：:])[^*\n]*', r'\1 [填写栏] ', line)
            lines.append(line)
        return re.sub(r'\s+', ' ', '\n'.join(lines)).strip()
    return normalize(body).startswith(normalize(original))

def guard_generated_writes(workspace, script_name):
    workspace = Path(workspace)
    state_path = workspace / 'evidence/review-state.json'
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state.get('events') or state.get('records') or state.get('comparability'):
            raise SystemExit('已有本人核验记录：停止重建，避免覆盖人工内容。日常请使用人工核验入口；重建请使用新的资料副本。')
    protected = ['tasks', 'evidence', 'outputs', 'work/notes.md', 'work/pending-checks.md', 'README.md', 'docs']
    baseline_path = workspace / 'config/generation-baseline.json'
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
        for relative, expected in baseline.get('files', {}).items():
            path = workspace / relative
            if not path.is_file() or generated_text_hash(path) != expected:
                raise SystemExit('检测到生成基线之外的人工或后续修改：停止重建，保留已保存内容。请在新的资料副本中重建。')
    else:
        existing = []
        for relative in protected:
            path = workspace / relative
            if path.is_file(): existing.append(path)
            elif path.is_dir(): existing.extend(path.rglob('*.md'))
        if existing:
            raise SystemExit('缺少生成基线且已有研究文件：停止覆盖。请在新的资料副本中创建成果。')
    if (workspace / '.git').exists() and GIT.exists():
        result = subprocess.run([str(GIT), 'diff', '--name-only', 'HEAD', '--', *protected], cwd=workspace, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0 and result.stdout.strip():
            raise SystemExit('存在尚未保存的研究或合同修改：停止生成，避免覆盖。请保留现有填写，在资料副本中重建。')
    if script_name == '05_build_workspace.py':
        for contract in (workspace / 'tasks').glob('0[1-5]-*.md'):
            text = contract.read_text(encoding='utf-8')
            for name in re.findall(r'执行人[：:]([^；\n]+)', text):
                if name.strip(' _*'):
                    raise SystemExit('合同已有执行人填写：停止重建合同，保留人工内容。')


def generated_text_hash(path):
    # Line-ending conversion by Git does not count as an authored content change.
    text = Path(path).read_text(encoding='utf-8-sig')
    return hashlib.sha256(text.replace('\r\n', '\n').encode('utf-8')).hexdigest()
