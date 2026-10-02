import unittest, sys, json, tempfile
from pathlib import Path
W = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(W/'scripts'))
from workspace_utils import contract_intact, original_source_root, guard_generated_writes, generated_text_hash
class ContractTests(unittest.TestCase):
    def test_filled_contract_and_formatting_are_allowed(self):
        original=(W/'sources/unpacked/03_学生材料(2)/03_学生材料/年报研究工作台模板/tasks/第一次任务合同.md').read_text(encoding='utf-8')
        actual=(W/'tasks/01-first-task.md').read_text(encoding='utf-8')
        self.assertTrue(contract_intact(actual, original))
        filled=actual.replace('- **执行人**：','- **执行人**：Leo').replace('- [ ] 已核对表格单位。','- [x] 已核对表格单位。')
        self.assertTrue(contract_intact(filled, original))
    def test_substantive_boundary_cannot_be_removed(self):
        original=(W/'sources/unpacked/03_学生材料(2)/03_学生材料/年报研究工作台模板/tasks/第一次任务合同.md').read_text(encoding='utf-8')
        changed=original.replace('不能直接成为','可以直接成为')
        self.assertFalse(contract_intact(changed, original))
    def test_normal_signature_fields_are_allowed(self):
        p=W/'sources/original-tree/学生用/第四次任务合同_年报指标变化核验.md'
        original=p.read_text(encoding='utf-8').replace('- **研究公司**：','- **研究公司**：贵州茅台酒股份有限公司（600519）')
        filled=original.replace('**执行人签署**：__________','**执行人签署**：Leo').replace('**复核人签署**：__________','**复核人签署**：Review').replace('**日期**：__________','**日期**：2026-10-02')
        self.assertTrue(contract_intact(filled, original))
    def test_source_root_is_independent_of_workspace_move(self):
        with tempfile.TemporaryDirectory(dir=W/'work') as folder:
            fixture=Path(folder);(fixture/'config').mkdir()
            (fixture/'config/workspace.json').write_text(json.dumps({'original_source_root':'D:/投资学/课件与任务文件'}),encoding='utf-8')
            self.assertEqual(original_source_root(fixture), Path('D:/投资学/课件与任务文件').resolve())
    def test_generation_stops_before_overwriting_review_history(self):
        with tempfile.TemporaryDirectory(dir=W/'work') as folder:
            fixture=Path(folder);(fixture/'evidence').mkdir()
            (fixture/'evidence/review-state.json').write_text(json.dumps({'events':[{'state':'Unknown'}]}),encoding='utf-8')
            with self.assertRaises(SystemExit): guard_generated_writes(fixture,'06_build_tasks.py')
    def test_committed_or_portable_manual_changes_are_protected(self):
        with tempfile.TemporaryDirectory(dir=W/'work') as folder:
            fixture=Path(folder);(fixture/'config').mkdir();(fixture/'work').mkdir()
            notes=fixture/'work/notes.md';notes.write_text('机器底稿\n',encoding='utf-8')
            (fixture/'config/generation-baseline.json').write_text(json.dumps({'files':{'work/notes.md':generated_text_hash(notes)}}),encoding='utf-8')
            notes.write_text('机器底稿\n本人补充核验经过\n',encoding='utf-8')
            with self.assertRaises(SystemExit): guard_generated_writes(fixture,'06_build_tasks.py')
if __name__=='__main__': unittest.main()
