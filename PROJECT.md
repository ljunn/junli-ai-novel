# 君黎 AI 网文连载项目入口

收到任务后，先对号入座选 Workflow，再跑命令，不用先背架构。

## 任务 → Workflow 对照

| 任务 | 用这个 |
|------|--------|
| 继续写下一章 | `next-chapter` |
| 章节质检 / 审稿 | `review` |
| 超长篇 / 分卷 / 阶段治理 | `bootstrap-longform` + `governance` + `audit` |
| 商业化包装 / 平台上架文案 | `marketing` |
| 平台输出门禁 / 后处理检查 | `platform-gate` |
| 查同类开头 / 对白 / 章末范本 | `corpus-search` |

拿不准入口：`python3 scripts/chapter_pipeline.py workflows`

## 项目规则文件用途

读这些文件是为了弄清楚"当前状态"和"不能踩的红线"，不是为了背设定。

- **什么不能改**：`docs/全书宪法.md`、`docs/世界观.md`、`docs/法则.md`、`characters/*.md`
- **当前写到哪了**：`task_log.md`、`docs/章节规划.md`、`plot/伏笔记录.md`、`plot/时间线.md`
- **全书结构怎么分**：`docs/项目总纲.md`、`docs/卷纲.md`、`docs/阶段规划.md`、`docs/变更日志.md`
- **本章写作约束**：`rules/novel-lint/*.yaml`、`references/rule-linting.md`
- **本地同类范本**：`runtime/chapter-XXXX.references.md`、`corpus/articles/`、`references/corpus-guide.md`
- **一致性和质检**：`references/consistency.md`、`references/quality-checklist.md`

优先级：全书宪法 > 结构文件 > 运行记忆 > 本章临时意图

旧项目如果只有 `docs/大纲.md`，把它同时视作 `项目总纲 + 章节规划`。

## Workflow 详情

### 续写下一章

```bash
python3 scripts/chapter_pipeline.py next-chapter <项目目录> --chapter-title "标题"
```

串联：`preflight → resume → plan → compose → start`

`init` 创建的新项目默认就是可直接自动生成长篇连载的状态；如果导入旧项目且想立刻按长篇治理规则执行，可额外加 `--require-longform-governance`。

正文写完后，同一条命令闭环：

```bash
python3 scripts/chapter_pipeline.py next-chapter <项目目录> \
  --chapter-num <章节号> \
  --chapter-path <章节文件路径> \
  --summary "本章摘要"
```

### 章节预审与审稿稿本

```bash
python3 scripts/chapter_pipeline.py review <章节文件路径> --project-path <项目目录>
```

输出两层：静态预审（规则/字数/情绪/对白硬信号）+ 审稿稿本（带证据摘录的语义审稿提纲）。
默认会把审稿稿本落成 `审阅意见/*.md`。需要只看终端摘要时加 `--no-write-report`；需要改路径时加 `--report-path`。

### 本地范本检索

```bash
python3 scripts/chapter_pipeline.py corpus-build
python3 scripts/chapter_pipeline.py corpus-search --type '高张力对白' --keyword '退婚'
```

`plan / compose / next-chapter` 会自动把命中结果写进 `runtime/chapter-XXXX.references.md`。

### 长篇治理

```bash
python3 scripts/chapter_pipeline.py bootstrap-longform <项目目录>
python3 scripts/chapter_pipeline.py governance <项目目录> --current-volume "第一卷" --current-phase "阶段1" --phase-goal "目标"
python3 scripts/chapter_pipeline.py audit <项目目录> --scope stage
```

说明：
- `init` 创建的新项目会预置治理模板和默认治理状态，开箱即可自动续写。
- `bootstrap-longform` 会为旧项目补齐治理模板，并恢复自动生成所需的默认卷/阶段/阶段目标。
- 如果旧项目尚未达到阈值，但你想立刻按长篇治理执行，可在 `preflight / start / next-chapter / finish` 上加 `--require-longform-governance`。
- 阶段审计会在超过 20 章未执行时自动阻塞；卷审计目前不自动推断卷末，卷末/换卷时要手动执行 `audit --scope volume`。

### 商业化包装

```bash
python3 scripts/chapter_pipeline.py marketing <项目目录> --platform 起点中文网 --audience 男频读者
```

把作者意图、当前焦点、项目总纲、近期剧情、活跃伏笔编译成营销 Brief / Prompt Pack。

### 平台输出门禁

```bash
python3 scripts/chapter_pipeline.py platform-gate <文件路径> --platform 起点中文网
```

适用两类文件：

- 章节稿：`--kind chapter`
- 营销 Brief：`--kind marketing`

## 文件地图

- `PROJECT.md`：本文件，任务分流入口
- `SKILL.md`：AI 操作宪法（含写法原则）
- `references/`：写作方法论
- `corpus/`：本地范本与检索索引
- `rules/novel-lint/`：规则化文本巡检
- `审阅意见/`：`review` 自动生成的章节审阅报告
- `references/platform-output-gate.md`：平台输出门禁说明
- `scripts/chapter_pipeline.py`：统一命令入口
