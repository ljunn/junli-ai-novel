---
name: junli-ai-novel
description: 长篇连载小说项目工作流，覆盖从零立项、主线/大纲规划优化、续写下一章、单章扩写/重写/润色、上下文恢复、三层记忆维护与章节质检；当用户需要规划长篇小说、优化主线情节结构、在已有项目上继续连载、恢复旧项目进度，或同步大纲/伏笔/时间线等项目记忆时使用
---

# 君黎 AI 写作

## 核心原则

1. 先读档，再下笔。
2. 宪法记忆优先于临场发挥。
3. 先定场景任务，再写纯正文。
4. 每章必须推进剧情、关系或风险，不能只注水。
5. 写完先检查，再做定向返修，不轻易全文推倒。
6. 结构模板晚于主角目标、起爆事件和连锁反应，不先拿模板硬套主线。

## 先判断任务类型

先把请求归进下面 4 类，只执行对应流程。

### A. 新项目 / 设定不完整

满足任一条件就按新项目处理：

- 用户说“从零开始”“帮我立项”“帮我搭世界观”
- 项目目录不存在，或没有 `docs/`、`plot/`、`task_log.md`
- 用户只有脑洞、梗概或人设碎片

默认动作：

1. 只补齐缺失的“5 问立项”信息：题材与风格、主角结构、主角核心性格、核心冲突、预计章节规模。
2. 立项时先用“主线三步法”拎直主线，再决定是否选结构模板：
   - 终点站：主角最终想要什么，为什么非要得到，不得到会怎样
   - 起爆事件：什么不可逆意外打破了主角原有生活
   - 连锁反应：意外直接触发了什么，把主角推到什么新境地，谁来制造阻碍或转机，本段危机如何解除并留下什么新问题
3. 主线清楚后，默认再用“终极锚点 -> 逆推问题链 -> 分卷锚点”补齐大纲，不顺着第一章一路瞎推：
   - 先定全书结局或终极锚点
   - 再倒推大反派、胜利路径、关键资源、关键伙伴、关键阻碍
   - 再给每一卷单独设一个阶段高潮或爽点锚点，继续逆推铺路事件
4. 如果用户明显是新手，先用“四问主线梗概”把主线拎直：
   - 主角遇到了什么问题
   - 他准备怎么做
   - 中途会遇到哪些关键变数
   - 最后问题是否解决，并且改变了什么
5. 世界观发虚时，优先用“问题清单式设定法”补逻辑，不要凭感觉堆名词；先连续追问规则、利益、代价、禁忌和日常影响，再决定要不要扩设定。
6. 只有“终点站 -> 起爆事件 -> 连锁反应”清楚后，才读取或套用结构模板，不要反过来。
7. 优先读取以下资料校正主线，而不是直接拼大纲：
   - `references/main-plot-construction.md`
   - `references/outline-template.md`
   - `references/plot-structures.md`
   - `references/worldbuilding-logic.md`
8. 优先用统一入口建档：

```bash
python3 scripts/chapter_pipeline.py init "项目名" --mode single
```

按需追加：

- 双主角：`--mode dual`
- 群像/多线：`--mode ensemble`
- 关系复杂或感情线重要：`--complex-relationships`
- 女频/言情且关系图谱重要：`--romance-focus`

9. 先输出规划摘要，等用户确认后再进入正文创作。

### B. 继续连载 / 下一章

满足任一条件就按续写处理：

- 用户说“继续写”“下一章”“接着来”“上次写到哪了”
- 新开对话继续旧项目
- 长会话后需要恢复上下文

默认动作：

1. 先恢复项目摘要：

```bash
python3 scripts/chapter_pipeline.py resume <项目目录>
```

2. 读取优先级固定：
   - `task_log.md`
   - `docs/大纲.md`
   - `plot/伏笔记录.md`
   - `plot/时间线.md`
   - 相关角色档案与设定
   - 上一章正文和结尾钩子
3. 恢复输出至少包含：当前创作阶段、最近两到三章摘要、主角当前状态、活跃伏笔、下一章目标。
4. 开写前先拆 3-5 个场景，每个场景至少写清地点、人物、核心事件、情绪走向和暗线。
5. 开写前把目标章节标记为“进行中”：

```bash
python3 scripts/chapter_pipeline.py start <项目目录> <章节号> --chapter-title "标题"
```

6. 写完后先检查，再同步进度：

```bash
python3 scripts/chapter_pipeline.py finish <项目目录> <章节号> <章节文件路径> --chapter-title "标题" --summary "摘要"
```

### C. 单章扩写 / 重写 / 润色 / 质检

满足任一条件就按单章处理：

- 用户明确点名某一章
- 用户要扩字数、改节奏、修对白、减 AI 味
- 用户要检查爽点、毒点、情绪曲线或一致性

默认动作：

1. 读取目标章节。
2. 至少补读上一章、下一章或相关设定中的必要部分，避免只看单章硬改。
3. 只针对问题定向返修，不全文推倒。
4. 写后执行统一检查：

```bash
python3 scripts/chapter_pipeline.py check <章节文件路径>
```

### D. 恢复记忆 / 修复项目记忆

满足任一条件就先修记忆：

- 用户说“恢复上下文”“唤醒记忆”“整理项目文档”
- `task_log.md`、`docs/大纲.md`、`plot/伏笔记录.md`、`plot/时间线.md` 缺失
- 正文还在，但项目记忆文件断档

默认动作：

1. 先报告缺失文件，不要假装记得内容。
2. 从 `manuscript/` 已有章节重建最近进度。
3. 先补齐缺失记忆文件，再继续创作。

## 默认项目结构

```text
[项目目录]/
├── docs/
│   ├── 大纲.md
│   ├── 冲突设计.md
│   ├── 世界观.md
│   ├── 法则.md
│   ├── 关系图.md            # 关系复杂或感情线重要时可选
│   └── 群像主题拆分.md      # 双主角/群像可选
├── characters/
│   ├── 人物档案.md
│   └── [角色名].md
├── manuscript/
│   ├── 001_标题.md
│   └── ...
├── plot/
│   ├── 伏笔记录.md
│   ├── 时间线.md
│   └── POV轮转表.md         # 双主角/群像可选
└── task_log.md
```

约束：

- `task_log.md` 是运行记忆入口。
- `docs/世界观.md`、`docs/法则.md`、`characters/` 属于高优先级宪法记忆。
- `manuscript/` 只放正文，不混入说明性文档。
- `plot/时间线.md` 不只记事件顺序，也记关键出场、情感转折和主角变化。

## 三层记忆

- L1 会话工作记忆：当前章节目标、场景推进链、开头钩子、上章悬念。
- L2 项目运行记忆：`task_log.md`、`docs/大纲.md`、`plot/伏笔记录.md`、`plot/时间线.md`。
- L3 宪法记忆：`docs/世界观.md`、`docs/法则.md`、`characters/人物档案.md`、`characters/*.md`。

新内容不得与更高层级记忆硬冲突。

## 章节硬性规则

- 正文写入 `manuscript/` 时必须是纯正文，不输出 `# 第X章`、`## 正文`、`## 章节备注`、`---`。
- 章节名默认写进文件名，不写进正文首行。
- 默认目标 3000-5000 字；如果用户明确要求短章或长章，以用户要求为准。
- 开头前 20% 必须出现即时冲突、异常信息或高吸引力动作。
- 每章至少推进一条线、回应一个旧悬念、留下一个新钩子。
- 主角受挫时，正文内或紧邻章节必须给出补偿基础，不能长期纯受气拖拽。
- 默认单一主 POV；没有明确收益，不要在同章乱切视角。

## 脚本入口

优先使用统一入口 `scripts/chapter_pipeline.py`，不要手动拼多条命令，除非只需调用单个检查脚本。

### 推荐入口

```bash
python3 scripts/chapter_pipeline.py init ...
python3 scripts/chapter_pipeline.py resume <项目目录>
python3 scripts/chapter_pipeline.py start <项目目录> <章节号> ...
python3 scripts/chapter_pipeline.py check <章节文件路径>
python3 scripts/chapter_pipeline.py finish <项目目录> <章节号> <章节文件路径> ...
```

### 仍可单独调用的脚本

- `scripts/new_project.py`：仅初始化项目结构
- `scripts/update_progress.py`：仅更新进度与大纲状态
- `scripts/check_chapter_wordcount.py`：检查字数
- `scripts/check_emotion_curve.py`：检查情绪曲线
- `scripts/extract_thrills.py`：检查爽点、毒点与密度

脚本输出只是辅助证据，终审以文本质量、上下文一致性和是否兑现剧情任务为准。

## 按需读取参考资料

只读与当前问题直接相关的文件，不要一次性全读。

### 立项 / 规划

- `references/main-plot-construction.md`
- `references/outline-template.md`
- `references/character-template.md`
- `references/character-building.md`
- `references/plot-structures.md`
- `references/conflict-design.md`
- `references/worldbuilding-logic.md`
- `references/worldbuilding-presentation.md`
- `references/idea-incubation.md`
- `references/golden-finger-design.md`
- `references/ensemble-writing.md`

### 章节创作 / 续写

- `references/chapter-workflow.md`
- `references/chapter-guide.md`
- `references/chapter-template.md`
- `references/hook-techniques.md`
- `references/dialogue-writing.md`
- `references/content-expansion.md`
- `references/daily-narrative.md`
- `references/nonlinear-narrative.md`
- `references/reader-compensation.md`

### 写后检查 / 风格护栏

- `references/quality-checklist.md`
- `references/consistency.md`
- `references/style-guardrails.md`

### 特殊取向

- `references/literary-opening.md`：文学性或严肃文学开篇
- `references/suspense-design.md`：钩子弱、追读弱、信息缺口驱动不够

## 题材补充规则

### 网文 / 平台向

- 规划阶段把书名当成结构问题，而不是纯审美问题。
- 书名优先承担题材识别和核心钩子传达，不优先追求文艺含混。
- 可参考同赛道成功书名的结构，不直接照抄具体书名。
- 传统文不等于没流量。只要题材契约清楚、开头够抓、骨相能撑长线、阶段回报稳定，传统文同样可以写爆，不要因为起号焦虑只会追逐空脑洞。
- 前三章默认按“短视频前三秒”标准自查：一句话噱头是否成立，是否有可切片传播的反常、悬念、情绪或冲突，读者是否能迅速看懂这本书卖什么。
- 脑洞是流量入口之一，但“系统、重生、穿越、老爷爷”这类标准配置本身不再自动构成脑洞；平台向更看重的是在金手指、剧情、设定或主角身份上能否给出真正的新奇角度。
- 不要把“影射、夹带、擦边表达、和审核斗心眼”当成创作聪明；平台向写作优先把力气放在剧情打磨、人物塑造和卖点兑现上。
- 不要默认审核和读者看不懂你的潜台词，也不要抱着“侥幸过线”的心态写高风险内容；这种自作聪明会直接毁掉长线连载和项目寿命。

### 女频 / 言情 / 大女主

- 把情感边界、主体性、补偿机制和叙事立场视为高敏感检查项。
- 警惕“设定上大女主，执行上媚男”的偏移：不要让女性议题长期靠男主教学、认证或命名，不要让女性角色集体降智抬男，也不要频繁偷走女主高光去证明男主完美。
- 如果出现“男主膈应”“女主太憋屈”“三观不适”“人设塌了”，优先读取 `references/style-guardrails.md`。

## 异常处理

### 项目为空

- 不要假装记得内容。
- 直接回到新项目流程。

### 记忆文件缺失

- 从正文重建最近进度。
- 明确告诉用户缺了哪些文件。
- 先补记忆，再继续写正文。

### 设定冲突

1. 优先遵守更高层级、更新时间更近的明确设定。
2. 在 `docs/法则.md` 或角色档案中消歧。
3. 无法自行消歧时，再向用户确认保留哪一版。

### 外部材料接入

如果用户提供创作经验、访谈摘录或方法论材料：

1. 先判断它要优化的是立项、冲突、章节推进还是风格，不额外平行起一套新流程。
2. 优先把稳定原则并入对应的既有规则或参考文件。
3. 优先吸收可操作、可复用、可验证的内容。
4. 只适用于单个项目的经验，写进项目文档，不污染通用规则。
5. 涉及“借鉴”时，先区分借的是开放框架设定，还是具体剧情、人物、关系和桥段。
