# 投资学工作空间

日常核验：双击[人工核验入口.cmd](人工核验入口.cmd)，选择记录，点“确认所选为Fact”。系统自动记录并同步相关文件；操作方法见[简洁核验指南](docs/human-review-guide.md)。

贵州茅台（600519），指定2020—2024年年报，2026秋金融专硕投资学任务。建立日期2026-10-02。

资料与自动化研究准备已完成。人工核验状态以核验入口和证据账本为准；学生本人承担口径与判断，人员及正式签署可以以后补齐。

[带图片的工作流程与文件说明](工作流程与文件说明.md) · [本地工作台](工作台.html) · [任务进度](docs/task-status.md) · [本人核验入口](docs/human-review-guide.md) · [全部文件位置](docs/generated-files.md)

![工作台构成](docs/images/workspace-structure.png)

| 位置 | 内容与用途 |
| --- | --- |
| sources/annual_reports/ | 五份原PDF与五份检索MD；保持原样，SHA-256见manifest.json |
| sources/course/ | 按正文用途整理的Lec01—03课件、附件、模板与原图片，副本原字节不变 |
| sources/toolkit/ | MinerU工具参考源码与说明；只读取，不安装或调用API |
| sources/original-tree/、sources/unpacked/ | 原目录副本与六个ZIP解包结果，保留出处；重复内容不重复进Git |
| tasks/ | 00本次执行说明、01—04合同和05Lec03合同 |
| work/ | 原页全文、检索、候选、口径冲突、修正、Unknown、计算与检查 |
| evidence/ | 本人核验后的证据日志、统一核验账本及人工表 |
| outputs/ | 六份合同成果准备稿与课件补充成果 |
| docs/ | 图片、核验指南、资料用途、运行与Git说明、文件清单 |
| scripts/ | 实际使用的解包、提取、生成、核验和计算脚本 |
| config/ | Python版本、依赖锁定及本人可比性确认配置 |
| .git/ | 本地版本库，无远程服务，无Token |

常用成果：[第一次定位](outputs/first-analysis.md)、[收入结构](outputs/revenue-structure-table.md)、[口径卡](outputs/metric-scope-decision.md)、[变化记录准备](outputs/change-verification-record.md)、[Lec03矩阵](outputs/lec03-evidence-matrix.md)、[Lec03五项成果](outputs/lec03-stage-deliverables.md)。

运行环境为本机D:/Anaconda/python.exe。双击“打开研究笔记.cmd”使用已有JupyterLab；双击“运行检查.cmd”执行验证。也可以用支持Python的编辑器打开投资学工作空间.code-workspace。详细说明见docs/run-guide.md。

<!-- review-store:progress:start -->
## 人工核验进度

当前有效Fact为2条；Unknown为61条；已撤回0条；需重新核验0条。共63条候选。 日期自动按Asia/Shanghai记录。合同验收、复核人与正式签署另行完成。
<!-- review-store:progress:end -->
