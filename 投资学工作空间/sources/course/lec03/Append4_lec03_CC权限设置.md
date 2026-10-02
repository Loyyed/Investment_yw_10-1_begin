---
title: "Claude Code：settings.json 中的权限设置"
created: 2026-09-23
updated: 2026-09-23
tags:
  - Claude Code
  - settings.json
  - Permissions
  - Agent
  - 安全
aliases:
  - Claude Code 权限配置
  - permissions 配置
---

# Claude Code：`settings.json` 中的权限设置

> **本节目标**：理解 Claude Code 如何通过 `settings.json` 控制 Agent 能做什么、哪些操作需要确认、哪些操作必须禁止，并建立一套适合项目工作的权限边界。

Claude Code 不仅要知道“应该做什么”，还必须知道：

> **哪些操作可以直接执行，哪些操作必须询问，哪些操作绝不能执行。**

这个问题主要由 `settings.json` 中的 `permissions` 配置解决。

---

# 一、权限设置解决什么问题？

如果没有明确权限边界，Agent 每次调用工具时都可能出现两个极端：

```text
过于严格
→ 每一步都弹窗询问
→ 工作流被频繁打断

过于宽松
→ Agent 可以直接修改、删除或执行高风险命令
→ 项目缺少安全边界
```

所以权限配置的目标不是“让 Claude 什么都能做”，而是：

> **让低风险、重复性操作自动执行，让高风险操作保留人工控制。**

---

# 二、权限配置放在哪里？

项目中常见两类配置文件：

```text
.claude/settings.json
.claude/settings.local.json
```

可以简单理解为：

| 文件 | 作用 |
| --- | --- |
| `.claude/settings.json` | 项目共享权限规则 |
| `.claude/settings.local.json` | 当前用户、当前电脑的本机权限规则 |

例如：

```text
project/
└── .claude/
    ├── settings.json
    └── settings.local.json
```

课堂上可以记：

> **共享规则进 `settings.json`，本机差异进 `settings.local.json`。**

---

# 三、`permissions` 的基本结构

一个典型权限配置可以写成：

```json
{
  "permissions": {
    "allow": [
      "Read(...)",
      "Edit(...)"
    ],
    "ask": [
      "Bash(...)"
    ],
    "deny": [
      "Bash(...)"
    ]
  }
}
```

三个层次分别代表：

```text
allow
↓
允许直接执行

ask
↓
执行前必须询问

deny
↓
禁止执行
```

这实际上建立了三道权限边界。

---

# 四、`allow`：哪些操作可以直接执行？

`allow` 适合放：

- 低风险；
- 高频；
- 范围明确；
- 即使执行错误，也容易恢复的操作。

例如：

```json
{
  "permissions": {
    "allow": [
      "Read(...)",
      "Edit(...)",
      "WebSearch(...)"
    ]
  }
}
```

可以理解为：

```text
Agent 判断需要调用工具
        ↓
匹配 allow
        ↓
无需再次确认
        ↓
直接执行
```

## 典型适用场景

例如一个研究项目中：

```text
允许：
- 读取 sources/
- 修改 work/
- 写入 outputs/
- 搜索网页
```

这些操作如果已经在项目规则中明确，就没有必要每一次都询问。

---

# 五、`ask`：哪些操作必须人工确认？

`ask` 用于：

> **Agent 可以提出操作，但不能自行决定执行。**

适合：

- 风险中等；
- 影响范围较大；
- 偶尔需要执行；
- 是否执行依赖人的判断。

例如：

```json
{
  "permissions": {
    "ask": [
      "Bash(git push *)",
      "Bash(rm *)"
    ]
  }
}
```

这意味着：

```text
Claude 想执行
git push

        ↓

命中 ask

        ↓

询问用户

        ↓

用户批准后执行
```

这类设置特别适合：

- Git push；
- 删除文件；
- 安装软件；
- 修改系统环境；
- 大范围移动文件；
- 涉及外部副作用的命令。

---

# 六、`deny`：哪些操作绝不能执行？

`deny` 是硬边界。

例如：

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)"
    ]
  }
}
```

其含义不是：

> “最好不要执行。”

而是：

> **即使 Agent 判断这一步有必要，也不允许执行。**

适合放：

- 高风险删除命令；
- 敏感目录；
- 凭据文件；
- 不允许 Agent 接触的数据；
- 明确禁止的工具。

---

# 七、权限不是只针对 Bash

权限规则实际上是在控制 **工具调用**。

常见类型包括：

```text
Read(...)
Write(...)
Edit(...)
Bash(...)
WebSearch(...)
WebFetch(...)
Skill(...)
MCP(...)
```

可以把它理解为：

```text
工具名称
+
匹配范围
=
权限规则
```

例如：

```text
Read(...)
```

表示控制读取文件。

```text
Bash(...)
```

表示控制 Shell 命令。

```text
WebFetch(...)
```

表示控制网页读取。

```text
Skill(...)
```

表示控制 Skill 调用。

---

# 八、文件权限：不要只写“允许 Edit”

真正有意义的权限设置，通常不是：

```json
"Edit(...)"
```

而是限定作用范围。

例如研究工作台中，可以采用：

```text
sources/
→ 只读

tasks/
→ 可以读取，任务目标不允许 Agent 擅自修改

work/
→ 允许写入和修改

evidence/
→ 只有核验后才能写入

outputs/
→ 可以生成阶段成果
```

这样权限系统就与项目目录职责结合起来。

---

# 九、权限设计的核心不是工具，而是“作用范围”

例如：

```text
Edit
```

本身并不危险。

真正决定风险的是：

```text
Edit 什么？
```

同理：

```text
Bash
```

也不是一律危险。

关键是：

```text
执行什么命令？
作用在哪些文件？
有没有不可逆副作用？
```

所以权限规则应该尽量遵循：

> **工具 + 范围 + 操作对象**

而不是只给工具一个笼统的“允许”。

---

# 十、`Bash(...)` 为什么最需要谨慎？

Shell 命令能力非常强。

通过 Bash，Agent 可以间接完成：

```text
创建文件
删除文件
移动文件
修改文件
运行脚本
安装软件
Git 操作
网络请求
修改系统设置
```

所以：

> **Bash 权限本质上是一种能力放大器。**

如果 Bash 权限写得过宽，即使 `Edit`、`Write` 很严格，Agent 仍可能通过 Shell 绕过原有边界。

---

# 十一、Bash 权限应该尽量匹配具体命令

不推荐：

```json
{
  "permissions": {
    "allow": [
      "Bash(*)"
    ]
  }
}
```

它接近于：

```text
所有 Shell 命令
↓
全部自动批准
```

更合理的是：

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff *)"
    ]
  }
}
```

这样只把明确的低风险命令加入白名单。

例如：

```text
git status
→ 查看状态
→ 低风险

git diff
→ 查看差异
→ 低风险

git push
→ 修改远程仓库
→ 风险更高
```

因此可以采用：

```text
git status
git diff
        ↓
allow

git commit
        ↓
按项目规则决定

git push
        ↓
ask
```

---

# 十二、通配符 `*` 是权限配置中最容易出问题的地方

例如曾经出现这样的规则：

```text
Bash(mv '某个目录'/* ./)
```

表面上看，它似乎只是允许：

> 把这个目录中的文件移动出来。

但 `*` 如果出现在命令中间，就可能匹配额外参数。

可以抽象成：

```text
Bash(command PREFIX * SUFFIX)
```

如果 `*` 可以匹配任意内容，那么实际获批的命令范围可能比视觉上看到的更大。

---

# 十三、为什么“中间的 `*`”危险？

假设权限规则：

```text
Bash(mv source/* ./)
```

人的理解通常是：

```text
source/*
= source 目录里的文件
```

但权限匹配关注的是命令字符串。

如果通配符位于命令中间，它可能匹配：

```text
文件名
参数
选项
其他命令片段
```

于是原本看起来很窄的规则，实际可能放宽权限。

> [!WARNING]
> **在 Bash 权限中，通配符不是简单的“文件列表”。它同时也是权限匹配模式的一部分。**

---

# 十四、一个重要原则：`*` 尽量放在命令末尾

例如：

```text
Bash(git diff *)
```

它表达的是：

> 允许所有以 `git diff` 开头的命令。

这种写法虽然仍然有范围，但边界比较容易理解。

而：

```text
Bash(command * fixed-part)
```

通常更难推断实际允许了什么。

课堂上可以记：

> **通配符越靠前，权限越难控制；通配符越多，匹配范围越难判断。**

---

# 十五、不要把“能匹配”误认为“应该允许”

权限规则的目标不是尽可能少弹窗。

例如：

```json
"allow": [
  "Bash(git *)"
]
```

操作很方便。

但它可能同时包括：

```text
git status
git diff
git add
git commit
git reset
git checkout
git clean
git push
...
```

这些命令的风险完全不同。

更好的方法是：

```text
低风险命令
→ 单独 allow

有副作用命令
→ ask

危险命令
→ deny
```

---

# 十六、用“副作用”而不是“工具名称”判断风险

可以用下面的三层分类来设计权限。

## 第一层：只读

例如：

```text
Read
git status
git diff
WebSearch
```

特点：

> 不改变项目状态。

通常可以优先进入 `allow`。

---

## 第二层：可恢复修改

例如：

```text
Edit work/
Write outputs/
git add
git commit
```

特点：

> 会改变状态，但影响范围明确，通常可以通过 Git 等方式恢复。

是否 `allow` 要结合项目边界。

---

## 第三层：外部或不可逆副作用

例如：

```text
rm
git push
删除目录
覆盖原始材料
修改系统环境
调用外部写入 API
```

特点：

> 影响可能不可逆，或者超出当前项目。

通常应该使用：

```text
ask
或
deny
```

---

# 十七、一套适合研究项目的权限思路

例如证券研究工作台：

```text
project/
├── sources/
├── tasks/
├── work/
├── evidence/
└── outputs/
```

可以设计为：

| 目录 | Agent 权限 |
| --- | --- |
| `sources/` | Read |
| `tasks/` | Read，修改需确认 |
| `work/` | Read / Write / Edit |
| `evidence/` | Read，写入受控 |
| `outputs/` | Read / Write / Edit |

对应的逻辑是：

```text
原始材料
→ 不动

任务定义
→ 不擅自改变

工作过程
→ Agent 自由工作

证据
→ 经过核验再进入

最终输出
→ 可以生成和修改
```

这比简单地设置“Claude 可以 Edit 文件”更加专业。

---

# 十八、Permissions 与 `CLAUDE.md` 的区别

这两个经常被混淆。

例如在 `CLAUDE.md` 中写：

```text
不要修改 sources/ 中的原始材料。
```

这是：

```text
行为规则
```

而在权限系统中禁止修改 `sources/`：

```text
permissions
```

这是：

```text
执行边界
```

两者的区别是：

```text
CLAUDE.md
→ 告诉 Agent 不应该做什么

Permissions
→ 让 Agent 实际不能直接做什么
```

因此，对重要边界最好采用：

> **规则约束 + 权限约束**

而不是只写一句自然语言提醒。

---

# 十九、Permissions 与 Hooks 的区别

两者也解决不同问题。

```text
Permissions
→ 能不能做

Hooks
→ 什么时候自动做
```

例如：

```text
Permissions
→ 是否允许 Bash(git diff *)

Hook
→ 每次修改文件后自动运行 git diff
```

因此：

```text
Permissions = capability boundary
Hooks       = event automation
```

---

# 二十、项目级与本机级权限应该怎样分工？

推荐逻辑：

## `.claude/settings.json`

放：

```text
团队共同认可的权限边界
```

例如：

- 原始数据不能修改；
- 可以读取项目文件；
- 可以执行低风险 Git 命令。

## `.claude/settings.local.json`

放：

```text
当前电脑特有的权限
```

例如：

- 当前机器上的某个目录；
- 本地工具路径；
- 某个个人 MCP；
- 当前用户愿意额外开放的权限。

因此：

```text
项目规则
→ settings.json

本机例外
→ settings.local.json
```

---

# 二十一、最小权限原则

权限配置最重要的原则之一是：

> **只开放完成任务所需要的最小权限。**

不要因为 Agent “可能会用到”就一次性开放所有能力。

推荐过程：

```text
先不给
  ↓
任务真正需要
  ↓
确认风险
  ↓
开放最小范围
  ↓
观察是否足够
  ↓
再决定是否扩大
```

这和传统系统安全中的 **Principle of Least Privilege** 是同一个思想。

---

# 二十二、课堂案例：为什么这个配置有问题？

假设：

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Edit(...)"
    ]
  }
}
```

问题在哪里？

```text
表面：
Agent 可以方便工作

实际：
Bash(*) 已经给了非常宽的 Shell 权限
```

即使 Edit 有边界：

```text
Bash
↓
仍可能通过 sed / mv / rm / cp / python 等方式
修改大量文件
```

所以权限不能只看：

```text
Edit 是否安全
```

还要看：

```text
有没有其他工具可以绕过这个边界
```

---

# 二十三、一个更合理的思路

例如：

```json
{
  "permissions": {
    "allow": [
      "Read(...)",
      "WebSearch(...)",
      "Bash(git status)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(rm *)"
    ]
  }
}
```

这里表达的是：

```text
读取
→ 自动

搜索
→ 自动

查看 Git 状态
→ 自动

查看 diff
→ 自动

向远程仓库写入
→ 人工确认

删除
→ 人工确认
```

它不是唯一正确方案，但体现了正确的权限设计思路：

> **按照风险和副作用分层，而不是把所有命令一起放开。**

---

# 二十四、课堂上可以用“四问法”检查权限

看到一条权限规则时，先问：

### 1. 它允许哪个工具？

```text
Read？
Edit？
Bash？
MCP？
```

### 2. 它允许作用在哪里？

```text
整个电脑？
整个项目？
某个目录？
某个文件？
```

### 3. 它允许做什么动作？

```text
读取？
修改？
删除？
执行？
上传？
```

### 4. 失败以后能不能恢复？

```text
可以 Git revert？
还是已经产生外部副作用？
```

如果这四个问题回答不清楚，说明权限规则通常写得太宽。

---

# 二十五、权限设计的一个基本矩阵

| 操作 | 风险 | 默认策略 |
| --- | --- | --- |
| 读取项目文件 | 低 | Allow |
| 搜索 / 查看状态 | 低 | Allow |
| 修改工作区文件 | 中 | 按目录 Allow |
| Git commit | 中 | 视工作流决定 |
| 删除文件 | 中高 | Ask |
| Git push | 高 | Ask |
| 修改系统配置 | 高 | Ask / Deny |
| 大范围删除 | 极高 | Deny |

这不是固定答案，而是一种设计框架。

---

# 二十六、最终心智模型

```text
CLAUDE.md
    ↓
Agent 应该怎么做


permissions.allow
    ↓
可以直接做


permissions.ask
    ↓
做之前必须问


permissions.deny
    ↓
不能做


Hooks
    ↓
什么时候自动做
```

把它们放在一起：

```text
                     Claude Code
                          │
              ┌───────────┴───────────┐
              │                       │
          行为规则                  执行边界
              │                       │
         CLAUDE.md               permissions
                                      │
                          ┌───────────┼───────────┐
                          │           │           │
                        allow        ask         deny
                          │           │           │
                      自动执行      人工确认      禁止
```

---

# 二十七、本节结论

`settings.json` 中的权限系统，本质上是在回答：

> **Agent 可以把“想做”变成“实际执行”到什么程度？**

最重要的不是记住 JSON 语法，而是建立四条原则：

1. **按照风险分层**：低风险自动，高风险确认；
2. **按照作用范围授权**：尽量限制到具体工具、目录和命令；
3. **谨慎使用 Bash 通配符**：尤其避免过宽的 `*` 匹配；
4. **遵循最小权限原则**：只开放完成当前项目所必需的能力。

最终目标不是减少所有权限弹窗，而是：

> **让 Agent 在明确边界内自主工作，同时把真正重要的决定留给人。**
