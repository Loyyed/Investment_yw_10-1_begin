---
title: "Claude Code 的文件配置系统"
created: 2026-09-23
updated: 2026-09-23
tags:
  - Claude Code
  - Agent
  - 文件配置
  - Skills
  - MCP
  - Subagent
aliases:
  - Claude Code 文件配置
  - Claude Code 配置系统
---

# Claude Code 的文件配置系统

> **本节目标**：理解 Claude Code 如何通过一组文件，把长期规则、运行配置、任务方法、工具连接和 Agent 分工组织起来。

Claude Code 并不是只靠当前对话工作。  
一个稳定的项目，通常会把不同类型的信息放进不同的配置文件，让 Agent 知道：

- 长期应该遵守什么；
- 当前环境允许做什么；
- 某类任务应该怎么做；
- 可以连接哪些外部工具；
- 复杂任务由谁承担。

可以把 Claude Code 的文件配置理解为一个由 **用户级配置、项目级配置和功能模块** 组成的系统。

---

# 一、先看整体结构

```text
~/.claude/                         # 用户级：跨所有项目
├── CLAUDE.md                      # 用户级长期规则
├── settings.json                  # 用户级运行配置
├── skills/                        # 用户级 Skills
│   └── <skill-name>/
│       └── SKILL.md
└── agents/                        # 用户级 Subagents
    └── <agent-name>.md


project/                           # 项目根目录
│
├── CLAUDE.md                      # 项目级长期规则【核心】
├── CLAUDE.local.md                # 个人 / 本机项目规则
├── AGENTS.md -> CLAUDE.md         # 可选：兼容其他 Agent
│
├── .claude/
│   ├── settings.json              # 项目共享运行配置
│   ├── settings.local.json        # 本机私有运行配置
│   │
│   ├── rules/                     # 模块化长期规则
│   │   ├── research.md
│   │   ├── coding.md
│   │   └── git.md
│   │
│   ├── skills/                    # 项目专用 Skills
│   │   └── <skill-name>/
│   │       ├── SKILL.md
│   │       ├── scripts/
│   │       └── references/
│   │
│   └── agents/                    # 项目专用 Subagents
│       ├── researcher.md
│       └── reviewer.md
│
├── .mcp.json                      # 项目级 MCP Server 配置
│
└── .gitignore
```

这棵目录树可以先拆成三个层次理解：

| 层次 | 主要作用 | 典型文件 |
| --- | --- | --- |
| 用户级 | 跨项目复用 | `~/.claude/CLAUDE.md`、`~/.claude/settings.json` |
| 项目级 | 当前项目长期有效 | `CLAUDE.md`、`.claude/settings.json` |
| 功能模块 | 管理规则、能力、工具和分工 | `rules/`、`skills/`、`agents/`、`.mcp.json` |

---

# 二、`CLAUDE.md`：项目长期规则的核心

`CLAUDE.md` 是 Claude Code 文件配置系统中最重要的文件之一。

它主要回答：

> **在这个项目里，Agent 长期应该怎样工作？**

## 2.1 用户级与项目级

```text
~/.claude/CLAUDE.md
        ↓
跨项目长期规则

project/CLAUDE.md
        ↓
当前项目长期规则
```

### 用户级 `CLAUDE.md`

适合放跨项目通用规则，例如：

- 沟通方式；
- 编码偏好；
- Git 使用习惯；
- 通用输出规范。

### 项目级 `CLAUDE.md`

适合放项目特有规则，例如：

- 项目目标；
- 目录职责；
- 文件读写边界；
- 研究或开发规范；
- 输出要求；
- 禁止事项。

> [!NOTE]
> `CLAUDE.md` 不应简单理解为一个“大 Prompt”。  
> 更准确地说，它是 **项目级长期工作规则**。

---

# 三、`CLAUDE.local.md`：本机或个人补充规则

有些规则只适用于当前用户或当前电脑，不适合与整个团队共享。

这类内容可以放在：

```text
CLAUDE.local.md
```

适合记录：

- 本机特有路径；
- 个人临时偏好；
- 当前电脑的特殊环境；
- 不希望提交到 Git 的本地补充规则。

因此可以把它理解为：

> **项目规则之上的本地覆盖层。**

---

# 四、`.claude/rules/`：把长期规则模块化

随着项目变大，`CLAUDE.md` 很容易越来越长。

这时可以把不同主题的规则拆到：

```text
.claude/rules/
├── research.md
├── writing.md
├── git.md
└── security.md
```

其逻辑是：

```text
CLAUDE.md
    ↓
项目总规则

.claude/rules/
    ↓
专题规则
```

例如：

- `research.md`：研究流程与证据规范；
- `writing.md`：写作格式与表达规则；
- `git.md`：版本控制要求；
- `security.md`：安全与权限边界。

> [!IMPORTANT]
> `rules/` 解决的是 **长期、稳定、反复适用的规则**。  
> 它不是用来记录某一次具体任务要求的。

---

# 五、`settings.json`：Claude Code 怎样运行

如果说 `CLAUDE.md` 管的是“怎么工作”，那么 `settings.json` 管的就是：

> **Claude Code 怎样运行。**

典型位置包括：

```text
~/.claude/settings.json
```

和：

```text
project/.claude/settings.json
```

这里主要配置：

- Permissions；
- Hooks；
- 环境相关选项；
- 团队共享的运行规则。

课堂上可以直接记：

> `CLAUDE.md` 管“怎么工作”，`settings.json` 管“怎么运行”。

---

# 六、`settings.local.json`：这台电脑具体允许什么

项目中还可能有：

```text
.claude/settings.local.json
```

它通常用来保存本机私有配置，例如：

- 本机权限；
- 本地路径；
- 本机 MCP 配置；
- 个人环境差异。

与 `settings.json` 相比：

| 文件 | 典型用途 | 是否适合 Git 共享 |
| --- | --- | --- |
| `.claude/settings.json` | 项目共享运行配置 | 通常可以 |
| `.claude/settings.local.json` | 本机私有运行配置 | 通常不提交 |

因此：

> `settings.json` 更像团队配置，`settings.local.json` 更像本机配置。

---

# 七、Hooks：什么时候自动执行

Hooks 解决的问题不是“做什么”，而是：

> **什么时候自动做某件事？**

常见事件可以包括：

```text
SessionStart
UserPromptSubmit
PreToolUse
PostToolUse
Stop
SessionEnd
```

可以把它理解成：

```text
事件发生
   ↓
Hook 被触发
   ↓
执行一段预先定义的操作
```

例如：

```text
SessionStart
    ↓
读取项目状态

PreToolUse
    ↓
工具调用前检查

PostToolUse
    ↓
记录工具执行结果

SessionEnd
    ↓
保存状态
```

## matcher 的作用

Hook 还可以通过 matcher 进一步限定触发条件。

因此：

```text
Hook
= 什么时候执行

matcher
= 在什么条件下执行
```

> [!TIP]
> Hooks 适合自动化重复性动作，而不是替代项目规则本身。

---

# 八、Skills：某类任务怎样做

Skill 用来封装一类可以复用的任务方法。

典型目录：

```text
.claude/skills/
└── annual-report-analysis/
    ├── SKILL.md
    ├── scripts/
    └── references/
```

其中：

```text
SKILL.md
```

是核心文件。

可以把 Skill 理解为：

> **一套可复用的任务方法，由 Agent 根据任务需要按需加载。**

Skill 中除了提示词和工作流程，还可以附带：

- 脚本；
- 模板；
- 参考材料；
- 辅助文件。

---

# 九、`CLAUDE.md` 与 Skill 的区别

这是文件配置系统中最容易混淆的一组概念。

```text
CLAUDE.md
长期存在
↓
这个项目始终遵守什么规则


Skill
按需加载
↓
遇到这类任务具体怎么做
```

例如：

```text
CLAUDE.md
→ 所有分析必须区分 Fact 与 Interpretation

Skill
→ 如何从年度报告中提取营业收入证据
```

因此：

> `CLAUDE.md` 是长期约束，Skill 是任务方法。

---

# 十、Agents / Subagents：谁来做

项目中还可以定义专门的 Subagent，例如：

```text
.claude/agents/
├── researcher.md
├── reviewer.md
└── data-analyst.md
```

Subagent 解决的是：

> **复杂任务由谁承担？**

例如：

- `researcher`：负责检索和初步研究；
- `reviewer`：负责检查结果；
- `data-analyst`：负责数据处理。

它与 Skill 的区别可以压缩成一句话：

```text
Skill
→ 怎么做

Subagent
→ 谁来做
```

---

# 十一、`.mcp.json`：Claude 可以连接什么

MCP 用来连接 Claude Code 与外部工具、数据和服务。

项目中常见配置文件为：

```text
.mcp.json
```

逻辑可以表示为：

```text
.mcp.json
    ↓
MCP Server
    ↓
外部工具 / 数据源
```

例如可以连接：

- 数据库；
- 文件系统；
- 浏览器；
- 外部 API；
- 搜索工具；
- 专业研究工具。

因此课堂上可以概括为：

> **MCP 决定 Agent 能接触哪些外部工具和数据。**

---

# 十二、`AGENTS.md`：兼容其他 Agent

如果同一个项目不仅使用 Claude Code，还可能使用其他 Coding Agent，可以增加：

```text
AGENTS.md
```

一种做法是让它与 `CLAUDE.md` 保持一致，例如建立软链接：

```bash
ln -s CLAUDE.md AGENTS.md
```

这样：

```text
CLAUDE.md
   ↑
   │ 同一套项目规则
   ↓
AGENTS.md
```

可以避免维护两份重复规则。

> [!NOTE]
> `AGENTS.md` 是兼容性设计，不是 Claude Code 项目必须存在的核心文件。

---

# 十三、把这些文件放在一起理解

Claude Code 的配置系统并不是一堆孤立文件，而是各自解决不同问题。

| 配置 | 它回答的问题 |
| --- | --- |
| Session | 现在做什么？ |
| `CLAUDE.md` | 长期遵守什么？ |
| `.claude/rules/` | 哪些专题规则长期生效？ |
| `settings.json` | Claude Code 怎样运行？ |
| Hooks | 什么时候自动做？ |
| Skills | 这类任务怎么做？ |
| MCP | 可以调用什么？ |
| Subagent | 谁来做？ |

---

# 十四、一张图建立完整心智模型

```text
                         Claude Code
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       Session            CLAUDE.md            Skills
          │                   │                   │
      当前任务             稳定规则            可复用流程
                              │
                        .claude/rules/
                         模块化规则


settings.json
      │
      ├── Permissions ───── 能不能做
      └── Hooks ─────────── 什么时候做


.mcp.json
      ↓
连接什么工具


agents/
      ↓
由谁来做
```

---

# 十五、课堂收束：七个问题

学习 Claude Code 的文件配置系统，不必先记住所有文件名。

先记住下面七个问题：

```text
Session        → 现在做什么？
CLAUDE.md      → 长期遵守什么？
Rules          → 哪些规则长期生效？
Skills         → 这类任务怎么做？
MCP            → 可以调用什么？
Subagent       → 谁来做？
settings.json  → Claude Code 怎样运行？
```

如果学生能把一个配置文件放回这七个问题中的某一个位置，就已经建立了基本的配置系统心智模型。

---

# 十六、进一步理解：从 Prompt 到配置系统

初学者往往把 Agent 使用理解成：

```text
写 Prompt
    ↓
得到回答
```

但进入项目型工作以后，更稳定的方式是：

```text
当前任务
    ↓
Session

长期项目规则
    ↓
CLAUDE.md / rules/

运行权限与自动化
    ↓
settings.json / Hooks

可复用任务方法
    ↓
Skills

外部工具与数据
    ↓
MCP

复杂任务分工
    ↓
Subagents
```

这意味着 Claude Code 的核心变化并不是“把 Prompt 写得更长”，而是：

> **把不同性质的信息放进不同的配置层，让 Agent 在正确的时间读取正确的规则、方法和工具。**

---

# 十七、本节结论

Claude Code 的文件配置系统可以压缩成四个层面：

1. **规则层**：`CLAUDE.md`、`.claude/rules/`
2. **运行层**：`settings.json`、`settings.local.json`、Hooks
3. **能力层**：Skills、MCP
4. **分工层**：Subagents

最终目标不是增加配置文件数量，而是建立清楚的边界：

> **稳定规则长期保存，任务方法按需加载，运行权限单独配置，外部能力明确连接，复杂任务合理分工。**
