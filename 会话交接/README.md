# 会话交接的使用方法

本目录保存精简的项目状态和稳定约定，供下次直接接着做。下次可说：**“先读 D:/投资学/会话交接/CURRENT.md，然后继续本次任务。”**

| 文件/目录 | 用途 | 何时读取 |
| --- | --- | --- |
| [CURRENT.md](CURRENT.md) | 当前完成状态、待办和权威证据入口 | 每次进入项目先读 |
| [DECISIONS.md](DECISIONS.md) | 用户长期偏好与已经明确的选择 | 相关任务需要时读 |
| logs/ | 有必要留存的本地操作摘要；不复制完整聊天 | 排查具体问题时按条读取 |
| tmp/ | 临时脚本输出与中间材料，按需创建 | 当前操作需要时读取 |

CURRENT 保持约 1000 汉字以内，完成一个工作节点后覆盖更新；历史由 Git 保留。DECISIONS 只在偏好或明确决定变化时更新。logs/、tmp/ 在仓库根 .gitignore 中排除，不随成果推送。已有正式证据、采用声明和真实修正过程继续保存于投资学工作空间的 evidence/、work/ 和合同文件，不移到临时日志。

仓库根 AGENTS.md 提供短入口；工作空间的 AGENTS.md 保留原有来源保护、人工核验与签署规则。依据 [OpenAI Docs：AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)，项目指引按项目根至工作目录发现；依据 [OpenAI：按任务需要读取](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)，入口只指向必要文件，细节按需读取。

这些文件不会自动清除已有聊天上下文。新会话从 CURRENT 开始，可以减少重复寻找资料和读取长历史；实际上下文用量仍取决于应用管理及本次需要读取的材料。CURRENT 是导航摘要，不能作为数值 Fact 的证明；使用事实前仍须检查原始核验记录及当前来源绑定。
