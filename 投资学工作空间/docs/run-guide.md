# 环境、复现与Git使用

实际环境：D:/Anaconda/python.exe，Python3.12.4；依赖具体版本见config/dependencies.json。D:/Py是另一个Python，不作为本项目执行环境。环境文件environment.yml用于未来复建，本次未创建额外conda环境或修改全局包。

在本目录的cmd中运行：

~~~cmd
D:/Anaconda/python.exe scripts/03_extract.py
D:/Anaconda/python.exe scripts/08_validate.py
D:/Anaconda/python.exe -m jupyter lab research.ipynb
~~~

前两命令为抽取和检查，第三命令打开本机JupyterLab。Notebook可以读取51条结构候选及21组核对记录；运行不意味着人工核验完成。Notebook实际内核执行副本在work/notebook-executed.ipynb。

日常人工确认与第四次可比性统一使用人工核验入口.cmd，配置和记录由程序维护。正式变化复算也可在确认后运行scripts/07_compute_changes.py。缺确认、零基数或明确重述/口径变化必须保持阻断。2022重述不能仅用“no_restatement=true”绕过；应先另建同口径调整记录，当前脚本只服务2024对2023。

重建顺序为00清点解包→01全文读取→03结构提取→04原页渲染→05建立目录合同→06/06b成果→07b图片笔记→09文档。原件一直保持不变。已有人工修改或核验事件时05、06、06b、07b、09会停止重建；先保留版本，在新的资料副本重建。核验事件和生成基线共同保护人工修改，已提交的填写也不会被旧生成脚本覆盖。

本地工作台.html可由你在浏览器打开，Markdown链接可用编辑器阅读。内置浏览器安全策略拒绝本地file://页面，本轮只验证HTML链接、结构和图片，未验证其浏览器渲染。

Git可执行文件：C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe。系统未将Git加入公共PATH时，可运行本目录Git.cmd代理入口，例如：

~~~cmd
Git.cmd status
Git.cmd diff
Git.cmd log --oneline
Git.cmd add outputs evidence work tasks
Git.cmd diff --staged
Git.cmd commit -m "verify annual report evidence"
~~~

使用项目本地作者身份Investment Workbench Agent / workbench@localhost.invalid保存本轮Agent生成记录；可以在本仓库修改user.name/user.email为你真实身份，不影响全局。没有远程仓库，本地init/add/commit/log/diff/fsck可用；未测试push或GitHub登录。

sources/annual_reports、course、toolkit规范副本和核心产物进Git。原目录副本、重复解包、可重提的PDF全文、Notebook执行缓存、机器环境信息不重复进Git；它们仍保存在本地且清单可追溯。PNG与PDF作为二进制记录，敏感token/env/key排除。

迁移位置由脚本所在目录自动确定；原件位置在config/workspace.json单独配置。运行检查器已允许合同的正常填空、签署栏及验收勾选，同时检查实质条款。
