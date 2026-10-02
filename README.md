# 投资学：课程资料与研究工作空间

本仓库汇集投资学课程材料、任务合同，以及贵州茅台（600519）2020—2024年年报研究工作空间。研究过程保留原件、机器提取候选、人工核验记录、成果与可复现脚本。

## 从这里开始

1. 阅读[工作流程与文件说明](投资学工作空间/工作流程与文件说明.md)，了解各目录和成果的用途。
2. 在本机打开投资学工作空间，双击[人工核验入口.cmd](投资学工作空间/人工核验入口.cmd)。完成PDF核对后，选择记录，点击“确认所选为Fact”；记录及相关成果自动同步。
3. 查看[简洁核验指南](投资学工作空间/docs/human-review-guide.md)、[任务进度](投资学工作空间/docs/task-status.md)和[工作空间说明](投资学工作空间/README.md)。有疑问可保留Unknown或撤回确认，合同正式签署另行完成。

![工作空间构成](投资学工作空间/docs/images/workspace-structure.png)

## 目录与用途

| 位置 | 用途 |
| --- | --- |
| 课件与任务文件/ | 原始课件、附件、任务文件与压缩包，保留出处和原始字节。 |
| 投资学工作空间/sources/ | 按用途整理的课程材料、指定年报PDF及检索MD。 |
| 投资学工作空间/tasks/ | 第一次至第四次任务合同，以及Lec03任务要求。 |
| 投资学工作空间/work/ | 数据候选、口径冲突、过程记录、复算与检查结果。 |
| 投资学工作空间/evidence/ | 人工核验记录、有效Fact导出和证据账本。 |
| 投资学工作空间/outputs/ | 定位、收入结构、口径裁决、变化核验及Lec03阶段成果。 |
| 投资学工作空间/scripts/、tests/ | 自动同步、计算、原件检查与回归测试。 |
| 投资学工作空间/docs/、config/ | 图示、操作说明、文件清单、原件位置及运行配置。 |

主要成果：[第一次定位](投资学工作空间/outputs/first-analysis.md)、[收入结构](投资学工作空间/outputs/revenue-structure-table.md)、[口径卡](投资学工作空间/outputs/metric-scope-decision.md)、[变化核验](投资学工作空间/outputs/change-verification-record.md)、[Lec03矩阵](投资学工作空间/outputs/lec03-evidence-matrix.md)。

## 运行与人工核验

本机工作目录为D:/投资学，Python使用已有D:/Anaconda/python.exe。人工核验窗口、研究笔记、运行检查均可从工作空间内对应的cmd入口打开，详细环境说明见[运行指南](投资学工作空间/docs/run-guide.md)。

机器定位和自动检查保留为候选。只有本人明确确认的披露记录才形成Fact；最新有效状态以核验窗口和证据账本为准。后续程序通过ReviewStore(...).facts()检查来源版本，数据或PDF改变后必须重新核验。第四次任务的七项可比性独立确认；核验记录不代替合同复核、签署或机制判断。

复制到其他电脑或改变资料位置时，更新投资学工作空间/config/workspace.json中的original_source_root，并调整cmd入口中的Python路径。

## Git与保存范围

远程仓库：[Loyyed/Investment_yw_10-1_begin](https://github.com/Loyyed/Investment_yw_10-1_begin)，origin使用git@github.com:Loyyed/Investment_yw_10-1_begin.git。

D:/投资学的根仓库用于整包保存和推送；原投资学工作空间内部的独立Git历史继续保留在本机。根仓库按普通文件保存完整工作空间，克隆后可直接浏览其内容。后续提交与推送请从D:/投资学根目录执行，提交信息使用中文。

~~~cmd
cd /d D:\投资学
git status
git add -A
git diff --staged
git commit -m "记录人工核验与研究成果更新"
git push
~~~

课程原件、规范来源、合同、核验记录、成果、图片、脚本和配置进入版本控制。临时构建目录、自动缓存、升级备份及原件的重复解包副本留在本机；排除规则见根目录与工作空间内的.gitignore。文件位置和用途详见[全部文件清单](投资学工作空间/docs/generated-files.md)。

<!-- scope-acceptance:current-version:start -->
## 当前版本与弃用提示

第三次合同以2026-10-03重新核验版为准：3项主指标、3项结构项、1项扣非补充。旧71de2c4和e63b162已标为弃用，详见[弃用登记](投资学工作空间/docs/deprecated-versions.md)。

后续先读[会话交接](会话交接/CURRENT.md)，详细步骤见[第四次结果核验](投资学工作空间/docs/next-review.md)。
<!-- scope-acceptance:current-version:end -->
