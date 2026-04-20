# 君黎 AI 网文连载

> 平台向长篇网文 AI 写作技能包。覆盖从脑洞立项到超长篇连载全流程，内置章节/场景/语言三层写法原则，支持多层项目记忆与长篇治理。

## 能做什么

- **立项**：5 问快速建项，主线三步法锁定终点与起爆事件
- **续写**：自动恢复项目上下文，生成章节意图文件和场景卡，按写法原则约束正文
- **质检**：静态预审（字数/情绪曲线/爽毒点/AI 套语检测）+ 语义审稿稿本
- **长篇治理**：卷纲 / 阶段规划 / 变更日志 / 定期审计，防止超长篇失控平推
- **商业化包装**：生成平台上架用的营销 Brief / Prompt Pack

## 安装

```bash
npx skills add ljunn/junli-ai-novel
```

或者手动复制导入。

## 快速开始

### 新建项目

```bash
python3 scripts/chapter_pipeline.py init "我的小说" --mode single
```

`--mode` 可选：`single`（单主角）/ `dual`（双主角/双视角）/ `ensemble`（群像多线）

### 续写下一章

```bash
# 准备阶段（生成 intent 文件和场景卡）
python3 scripts/chapter_pipeline.py next-chapter ./我的小说 --chapter-title "第一战"

# 正文写完后闭环
python3 scripts/chapter_pipeline.py next-chapter ./我的小说 \
  --chapter-num 1 \
  --chapter-path ./我的小说/manuscript/0001_第一战.md \
  --summary "主角赢下擂台赛，震慑外门弟子"
```

### 章节质检

```bash
python3 scripts/chapter_pipeline.py review ./我的小说/manuscript/0001_第一战.md \
  --project-path ./我的小说
```

### 长篇治理

```bash
# 初始化治理文件（超过 20 章或 30 万字后触发）
python3 scripts/chapter_pipeline.py bootstrap-longform ./我的小说

# 同步当前卷/阶段状态
python3 scripts/chapter_pipeline.py governance ./我的小说 \
  --current-volume "第一卷" \
  --current-phase "阶段1" \
  --phase-goal "主角立足"
```

## 项目结构

```
junli-ai-novel/
├── scripts/
│   └── chapter_pipeline.py   # 统一命令入口
├── references/               # 写作方法论（32 篇，含写法速查）
├── rules/novel-lint/         # 规则化文本巡检（AI 套语 / 对白 / 视角越权等）
├── agents/                   # Agent 接入配置
├── SKILL.md                  # AI 操作宪法（含写法原则）
└── PROJECT.md                # 任务分流入口
```

## 写法内置原则

每次续写时，`plan` 命令生成的章节意图文件会自动注入三层写法提示：

| 层级 | 核心约束 |
|------|--------|
| 章节层 | 一章一件事 / 章尾造压 / 每章必有实感回报 |
| 场景层 | 状态必须转移 / 高能前放慢 / 对白只推冲突或暴露性格 |
| 语言层 | 情绪写行为不命名 / 具体优于抽象 / 规避 AI 套语 |

## 查看所有命令

```bash
python3 scripts/chapter_pipeline.py commands
```

---

更多内容关注抖音 **@君黎**
