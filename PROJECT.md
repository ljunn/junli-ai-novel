# 君黎 AI 网文连载项目宪法索引

这是本仓库的总入口。先看这里，再去看分散文档。

本项目现在按 3 层暴露能力：

1. Rule：定义什么不能错、什么优先级最高。
2. Workflow：把高频任务包成可直接执行的工作流。
3. Command：保留底层原子命令，给需要拆解调试的人用。

默认顺序不是“先记命令”，而是：

1. 先判定自己现在处于哪个 Workflow。
2. 再确认会受哪些 Rule 约束。
3. 只有需要拆开排查时，才回到底层 Command。

## Rule

- 宪法层：`docs/全书宪法.md`、`docs/世界观.md`、`docs/法则.md`、`characters/*.md`
- 结构治理层：`docs/项目总纲.md`、`docs/卷纲.md`、`docs/阶段规划.md`、`docs/变更日志.md`
- 项目运行层：`task_log.md`、`docs/章节规划.md`、`plot/伏笔记录.md`、`plot/时间线.md`
- 规则巡检层：`rules/novel-lint/*.yaml`、`references/rule-linting.md`
- 连贯性与质检层：`references/consistency.md`、`references/quality-checklist.md`

优先级固定：`宪法层 > 结构治理层 > 项目运行层 > 当前章节临时意图`

兼容说明：旧项目如果仍使用 `docs/大纲.md`，默认把它同时视作 `docs/项目总纲.md + docs/章节规划.md` 的兼容入口。

查看 Rule 层索引：

```bash
python3 scripts/chapter_pipeline.py rules
```

## Workflow

### 1. 续写下一章

默认入口：

```bash
python3 scripts/chapter_pipeline.py next-chapter <项目目录> --chapter-title "标题"
```

这个入口会串起：

`preflight -> resume -> plan -> compose -> start`

正文写完后，还是用同一条命令闭环，不再回忆命令链：

```bash
python3 scripts/chapter_pipeline.py next-chapter <项目目录> \
  --chapter-num <章节号> \
  --chapter-path <章节文件路径> \
  --summary "本章摘要"
```

### 2. 单章预审与审稿稿本

默认入口：

```bash
python3 scripts/chapter_pipeline.py review <章节文件路径> --project-path <项目目录>
```

它会合并：

`check + lint + dialogue-pass + consistency`

但现在它不再假装“已经完成语义审稿”。

它会输出两层结果：

- 静态预审：规则、对白、字数、情绪、连贯性硬信号
- 审稿稿本：带证据摘录和必答问题的语义审稿提纲

### 3. 长篇治理

用于超长篇、分卷、阶段切换、治理补档：

```bash
python3 scripts/chapter_pipeline.py bootstrap-longform <项目目录>
python3 scripts/chapter_pipeline.py governance <项目目录> --current-volume "第一卷" --current-phase "阶段1" --phase-goal "目标"
python3 scripts/chapter_pipeline.py audit <项目目录> --scope stage
```

### 4. 商业化包装

默认入口：

```bash
python3 scripts/chapter_pipeline.py marketing <项目目录> --platform 起点中文网 --audience 男频读者
```

这个入口会把作者意图、当前焦点、项目总纲、章节规划、最近剧情、活跃伏笔，连同补充提示词、AI 味词汇、参考材料，一起编译成可复用的营销 Brief / Prompt Pack。

相关方法说明：`references/marketing.md`

查看 Workflow 层索引：

```bash
python3 scripts/chapter_pipeline.py workflows
```

## Command

底层原子命令还都保留，适合排查、拆解、精细控制：

- `init`
- `preflight`
- `resume`
- `plan`
- `compose`
- `start`
- `check`
- `lint`
- `dialogue-pass`
- `consistency`
- `finish`
- `bootstrap-longform`
- `governance`
- `audit`

查看 Command 层索引：

```bash
python3 scripts/chapter_pipeline.py commands
```

## 推荐用法

- 不知道从哪里进：先看 `python3 scripts/chapter_pipeline.py workflows`
- 要继续写下一章：优先用 `next-chapter`
- 要做章节质检：优先用 `review`
- 要补商业化包装：优先用 `marketing`
- 只有 Workflow 失败或需要精细控制时，才拆回原子命令

## 文件地图

- `PROJECT.md`：项目总入口
- `SKILL.md`：对 agent 的操作宪法
- `references/`：方法论文档
- `rules/novel-lint/`：规则化巡检资产
- `scripts/chapter_pipeline.py`：统一命令入口
