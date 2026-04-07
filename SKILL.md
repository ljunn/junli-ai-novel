---
name: junli-ai-novel
description: 平台向长篇网文连载工程工作流，覆盖从零立项、主线/大纲规划优化、续写下一章、单章扩写/重写/润色、上下文恢复、多层记忆维护、阶段/卷治理与章节质检；当用户需要规划网文主线、优化追读与卖点兑现、在已有项目上继续连载、恢复旧项目进度，或同步大纲/伏笔/时间线等项目记忆时使用
---

# 君黎 AI 网文连载

## 核心原则

1. 最高目标是连载稳定、追读牵引、卖点兑现和长线续航。
2. 先读档，再下笔。
3. 宪法记忆优先于临场发挥。
4. 先定场景任务，再写纯正文。
5. 每章必须推进剧情、关系或风险，不能只注水。
6. 写完先检查，再做定向返修，不轻易全文推倒。
7. 结构模板晚于主角目标、起爆事件和连锁反应，不先拿模板硬套主线。
8. 默认按平台向长篇网文判断，不按出版文学或纯实验小说的标准做默认决策。

## 协议化硬门槛

命中续写、开写、返修、恢复记忆时，下面这些不是建议，而是必须动作。

1. 续写或开写正文前，必须先跑前置校验：

```bash
python3 scripts/chapter_pipeline.py preflight <项目目录>
```

2. `preflight` 返回非 0 时，禁止直接续写；必须先修记忆或补齐 `task_log.md` 的阶段/目标信息。
3. 进入正文前，必须先跑 `resume`，再读 `task_log.md`、`docs/大纲.md`、`plot/伏笔记录.md`、`plot/时间线.md`。
4. 长篇项目进入正文前，必须先跑 `plan` 和 `compose`，生成本章意图、上下文和规则栈；未生成运行时产物，视为本章尚未编排完成。
5. 开写新章节前，必须先跑 `start`；未执行 `start`，视为未进入正文创作阶段。
6. 写完后，必须先跑 `check`，再跑带 `--summary` 的 `finish`；未同步摘要，视为未完章。
7. 目标超过 100 万字，或项目已写到 20 章以上时，必须启用超长篇治理文件；未启用时先执行：

```bash
python3 scripts/chapter_pipeline.py bootstrap-longform <项目目录>
```

8. 每 10-20 章必须执行一次阶段审计；每卷结束必须执行一次卷审计：

```bash
python3 scripts/chapter_pipeline.py audit <项目目录> --scope stage
python3 scripts/chapter_pipeline.py audit <项目目录> --scope volume
```

9. 任何会影响全书终局、主角长期弧线、世界底层规则、长线关系边界的改动，必须先写入 `docs/变更日志.md`，再继续正文。
10. 如果 `preflight` 因当前卷 / 当前阶段 / 阶段目标缺失而失败，先执行：

```bash
python3 scripts/chapter_pipeline.py governance <项目目录> --current-volume "第一卷" --current-phase "阶段1" --phase-goal "目标"
```

11. 如果无法执行命令、无法读取关键文件或前置校验失败，必须明确报告阻塞；禁止假装已经恢复上下文、已经检查或已经同步进度。

## 违约信号

出现任一情况，视为没有遵守本 skill：

- 没跑 `preflight` / `resume` 就直接续写正文
- 长篇项目没跑 `plan` / `compose` 就直接进入正文
- 没跑 `start` 就直接写下一章
- 没跑 `check` / `finish --summary` 就宣称本章完成
- 记忆文件缺失时仍继续写
- 已进入超长篇规模，却没有卷纲 / 阶段规划 / 变更日志
- 跳过 `audit` 长期平推超过一个阶段
- 核心设定或终局方向改了，却没同步变更日志
- 用户明明只要求局部返修，却整章重写或并发堆多个微操作

## 先判断任务类型

先把请求归进下面 5 类，先处理前置修复，再执行主流程。

判流规则：

- 如果同时命中 D 和 B / C，先执行 D，再回到 B / C。
- 如果命中 E，优先完成 E 的审计或治理同步，再决定能不能继续写 B / C。
- 如果只是“继续写”，但记忆文件完整，就走 B，不额外起一套 D。
- 如果只是“检查某章”，但相关上下文严重缺失，先补最低限度上下文，再走 C。

### A. 新项目 / 设定不完整

满足任一条件就按新项目处理：

- 用户说“从零开始”“帮我立项”“帮我搭世界观”
- 项目目录不存在，或没有 `docs/`、`plot/`、`task_log.md`
- 用户只有脑洞、梗概或人设碎片

必须动作：

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
7. 主线三步法清楚后，再用 `references/outline-refinement.md` 做二次校验，不把它抬到主线之前：
   - 立意是否真的落到主角缺口、选择和代价
   - 人设是否和核心冲突咬合，而不是孤立标签
   - 简纲是否写清关键节点、冲突点、行动目的和关系变化
   - 如果目前只有事件流水账，先修关键帧再扩正文
8. 优先读取以下资料校正主线，而不是直接拼大纲：
   - `references/main-plot-construction.md`
   - `references/outline-refinement.md`
   - `references/outline-template.md`
   - `references/plot-structures.md`
   - `references/worldbuilding-logic.md`
9. 优先用统一入口建档：

```bash
python3 scripts/chapter_pipeline.py init "项目名" --mode single
```

按需追加：

- 双主角：`--mode dual`
- 群像/多线：`--mode ensemble`
- 关系复杂或感情线重要：`--complex-relationships`
- 女频/言情且关系图谱重要：`--romance-focus`

10. 先输出规划摘要，等用户确认后再进入正文创作。

### B. 继续连载 / 下一章

满足任一条件就按续写处理：

- 用户说“继续写”“下一章”“接着来”“上次写到哪了”
- 新开对话继续旧项目
- 长会话后需要恢复上下文

必须动作：

1. 先执行前置校验：

```bash
python3 scripts/chapter_pipeline.py preflight <项目目录>
```

2. `preflight` 返回非 0 时，立即切到 D，先修记忆，再续写。
3. 再用统一入口恢复机器摘要：

```bash
python3 scripts/chapter_pipeline.py resume <项目目录>
```

4. `resume` 只负责快速机器摘要，不等于已经完成深读或记忆修复。
5. 如果 `task_log.md`、`docs/大纲.md`、`plot/伏笔记录.md`、`plot/时间线.md` 缺失，立即切到 D，先修记忆，再续写。
6. 读取优先级固定：
   - `task_log.md`
   - `docs/大纲.md`
   - `plot/伏笔记录.md`
   - `plot/时间线.md`
   - 相关角色档案与设定
   - 上一章正文和结尾钩子
7. 恢复输出至少包含：当前创作阶段、最近两到三章摘要、主角当前状态、活跃伏笔、下一章目标。
8. 对长篇项目，先生成本章意图：

```bash
python3 scripts/chapter_pipeline.py plan <项目目录> --chapter-num <章节号> --chapter-title "标题"
```

9. 再编排本章运行时产物：

```bash
python3 scripts/chapter_pipeline.py compose <项目目录> --chapter-num <章节号> --chapter-title "标题"
```

10. 开写前先拆 3-5 个场景，每个场景至少写清地点、人物、核心事件、情绪走向和暗线。
11. 如果细纲只剩“发生了什么”，先回查 `references/outline-refinement.md`，补齐行动目的、冲突点、关系变化和关键场景，再进入正文。
12. 开写前先明确本章前台问题、阶段回报、补偿点、结尾钩子和下一章承接点。
13. 开写前把目标章节标记为“进行中”：

```bash
python3 scripts/chapter_pipeline.py start <项目目录> <章节号> --chapter-title "标题"
```

14. 写完后先检查，再同步进度；`finish` 必须带 `--summary`：

```bash
python3 scripts/chapter_pipeline.py check <章节文件路径>
python3 scripts/chapter_pipeline.py finish <项目目录> <章节号> <章节文件路径> --chapter-title "标题" --summary "摘要"
```

15. 如果当前项目已进入超长篇治理范围，连续推进 10-20 章后不得直接继续下一阶段；必须先跑：

```bash
python3 scripts/chapter_pipeline.py audit <项目目录> --scope stage
```

### C. 单章扩写 / 重写 / 润色 / 质检

满足任一条件就按单章处理：

- 用户明确点名某一章
- 用户要扩字数、改节奏、修对白、减 AI 味
- 用户要检查爽点、毒点、情绪曲线或一致性

必须动作：

1. 读取目标章节。
2. 至少补读上一章、下一章或相关设定中的必要部分，避免只看单章硬改。
3. 只针对问题定向返修，不全文推倒。
4. 如果用户点名的是局部段落或明确问题，优先从 `references/micro-revision-ops.md` 里挑一个微操作定向修，不并发堆多个目标。
5. 如果实际问题在主线或章节层，不要假装靠润色就能解决；先回上层重查。
6. 写后执行统一检查：

```bash
python3 scripts/chapter_pipeline.py check <章节文件路径>
```

### D. 恢复记忆 / 修复项目记忆

满足任一条件就先修记忆：

- 用户说“恢复上下文”“唤醒记忆”“整理项目文档”
- `task_log.md`、`docs/大纲.md`、`plot/伏笔记录.md`、`plot/时间线.md` 缺失
- 正文还在，但项目记忆文件断档

必须动作：

1. 先报告缺失文件，不要假装记得内容。
2. 先运行 `python3 scripts/chapter_pipeline.py resume <项目目录>` 快速确认现状，但不能把它当成已完成重建。
3. 从 `manuscript/` 已有章节、`docs/` 现有资料和 `characters/` 档案中手动重建最近进度。
4. 先补齐缺失记忆文件，再继续创作。

### E. 超长篇治理 / 阶段审计 / 卷审计 / 结构变更

满足任一条件就按超长篇治理处理：

- 目标字数超过 100 万字
- 已写到 20 章以上
- 用户说“分卷”“阶段”“审计”“卷末结算”“结构变更”
- 需要修改终局、主角长期弧线、世界底层规则、长线关系边界

必须动作：

1. 先确认以下文件存在；缺失时先补齐：
   - `docs/全书宪法.md`
   - `docs/卷纲.md`
   - `docs/阶段规划.md`
   - `docs/变更日志.md`
2. 对已有项目，缺文件就先执行：

```bash
python3 scripts/chapter_pipeline.py bootstrap-longform <项目目录>
```

3. 阶段切换前必须跑阶段审计：

```bash
python3 scripts/chapter_pipeline.py audit <项目目录> --scope stage
```

4. 卷末结算前必须跑卷审计：

```bash
python3 scripts/chapter_pipeline.py audit <项目目录> --scope volume
```

5. 如果要改全书终局、主角长期弧线、世界底层规则、长线关系边界，先更新 `docs/变更日志.md`，再同步 `全书宪法 / 卷纲 / 阶段规划`，最后才能继续正文。
6. 审计失败时，禁止继续正文创作；先修结构，再回到 B。

## 默认项目结构

```text
[项目目录]/
├── docs/
│   ├── 大纲.md
│   ├── 作者意图.md
│   ├── 当前焦点.md
│   ├── 全书宪法.md
│   ├── 卷纲.md
│   ├── 阶段规划.md
│   ├── 变更日志.md
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
├── runtime/
│   ├── chapter-0001.intent.md
│   ├── chapter-0001.context.json
│   ├── chapter-0001.rule-stack.yaml
│   └── chapter-0001.trace.json
└── task_log.md
```

约束：

- `task_log.md` 是运行记忆入口。
- `docs/全书宪法.md`、`docs/世界观.md`、`docs/法则.md`、`characters/` 属于高优先级宪法记忆。
- `manuscript/` 只放正文，不混入说明性文档。
- `plot/时间线.md` 不只记事件顺序，也记关键出场、情感转折和主角变化。
- `docs/卷纲.md`、`docs/阶段规划.md`、`docs/变更日志.md` 是 100 万字以上长篇的强制治理层。
- `docs/作者意图.md`、`docs/当前焦点.md` 是输入治理层。
- `runtime/` 只放本章运行时产物，不手写正文。

## 四层记忆

- L1 会话工作记忆：当前章节目标、场景推进链、开头钩子、上章悬念。
- L2 项目运行记忆：`task_log.md`、`docs/大纲.md`、`plot/伏笔记录.md`、`plot/时间线.md`。
- L3 长篇治理记忆：`docs/卷纲.md`、`docs/阶段规划.md`、`docs/变更日志.md`。
- L4 宪法记忆：`docs/全书宪法.md`、`docs/世界观.md`、`docs/法则.md`、`characters/人物档案.md`、`characters/*.md`。

新内容不得与更高层级记忆硬冲突。

消歧顺序：

- 先看层级：L4 > L3 > L2 > L1。
- 只有同层冲突时，才优先更新时间更近、表述更明确的一版。
- 无法自行消歧时，再向用户确认，不要擅自混编。

## 章节硬性规则

- 正文写入 `manuscript/` 时必须是纯正文，不输出 `# 第X章`、`## 正文`、`## 章节备注`、`---`。
- 章节名默认写进文件名，不写进正文首行。
- 默认目标 3000-5000 字；如果用户明确要求短章或长章，以用户要求为准。
- 平台向默认开头：前 20% 必须出现即时冲突、异常信息、强认知钩子或高吸引力动作。
- 如果用户明确要求文学感较强的网文开篇，可不立刻“打起来”，但前几段仍必须同时建立认知钩子和情感钩子，不能把慢误当深。
- 每章至少推进一条前台线、回应一个旧悬念、留下一个新钩子或升级旧钩子。
- 每章至少给出一种可感知回报：爽点、情绪爆点、关系爆点、信息收益或阶段性反制。
- 主角受挫时，正文内或紧邻章节必须给出补偿基础，不能长期纯受气拖拽。
- 默认单一主 POV；群像或多线章没有明确收益时，不要在同章乱切视角。

## 脚本入口

优先使用统一入口 `scripts/chapter_pipeline.py`，不要手动拼多条命令，除非只需调用单个检查脚本。

### 推荐入口

```bash
python3 scripts/chapter_pipeline.py init ...
python3 scripts/chapter_pipeline.py bootstrap-longform <项目目录>
python3 scripts/chapter_pipeline.py governance <项目目录> --current-volume ... --current-phase ... --phase-goal ...
python3 scripts/chapter_pipeline.py resume <项目目录>
python3 scripts/chapter_pipeline.py plan <项目目录> --chapter-num ... --chapter-title ...
python3 scripts/chapter_pipeline.py compose <项目目录> --chapter-num ... --chapter-title ...
python3 scripts/chapter_pipeline.py start <项目目录> <章节号> ...
python3 scripts/chapter_pipeline.py check <章节文件路径>
python3 scripts/chapter_pipeline.py finish <项目目录> <章节号> <章节文件路径> ...
python3 scripts/chapter_pipeline.py audit <项目目录> --scope stage
python3 scripts/chapter_pipeline.py audit <项目目录> --scope volume
```

### 仍可单独调用的脚本

- `scripts/new_project.py`：仅初始化项目结构
- `scripts/update_progress.py`：仅更新进度与大纲状态
- `scripts/check_chapter_wordcount.py`：检查字数
- `scripts/check_emotion_curve.py`：检查情绪曲线
- `scripts/extract_thrills.py`：检查爽点、毒点与密度

脚本输出只是辅助证据，终审以文本质量、上下文一致性、追读牵引和卖点兑现为准。

使用说明：

- `resume` 是机器摘要，不替代深读，不自动帮你修好记忆文件。
- `preflight` 是硬门槛校验；非 0 返回时，禁止继续正文创作。
- `bootstrap-longform` 会给旧项目补齐超长篇治理文件，并升级 `task_log.md`。
- `governance` 用于同步目标总字数、目标卷数、当前卷、当前阶段、阶段目标和待同步设定变更。
- `plan` 生成本章意图文件；`compose` 生成上下文、规则栈和轨迹文件。
- `audit` 会做阶段或卷审计，并把结果写回 `task_log.md`。
- `check_chapter_wordcount.py`、`check_emotion_curve.py`、`extract_thrills.py` 只负责报警，不负责判死刑。
- `extract_thrills.py` 对升级流、爽文、反转型章节更有参考价值；现实向、关系拉扯向、氛围压迫向章节若低分，只说明它不是该脚本偏好的类型，不等于写得差。

## 按需读取参考资料

只读与当前问题直接相关的文件，不要一次性全读。

### 立项 / 规划

- `references/main-plot-construction.md`
- `references/longform-governance.md`
- `references/outline-template.md`
- `references/outline-refinement.md`
- `references/tooling-adoption-roadmap.md`
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
- `references/micro-revision-ops.md`
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

- `references/literary-opening.md`：文学感较强但仍服务平台追读的网文开篇
- `references/suspense-design.md`：钩子弱、追读弱、信息缺口驱动不够

## 题材补充规则

### 网文 / 平台向

- 这是本 skill 的默认模式。除非用户明确指定其他目标，否则一律优先追读、兑现、续航和连载稳定。

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

1. 优先遵守更高层级的明确设定；只有同层冲突时，才取更新时间更近的一版。
2. 在 `docs/法则.md` 或角色档案中消歧。
3. 无法自行消歧时，再向用户确认保留哪一版。

### 外部材料接入

如果用户提供创作经验、访谈摘录或方法论材料：

1. 先判断它要优化的是立项、冲突、章节推进还是风格，不额外平行起一套新流程。
2. 如果它主要优化超长篇治理、分卷、阶段复盘或结构变更协议，优先并入 `references/longform-governance.md`。
3. 如果它主要优化大纲修整、立意-人设咬合或细纲颗粒度，优先并入 `references/outline-refinement.md`，不要改写“主线三步法 -> 逆推问题链”的主顺序。
4. 如果它主要优化提示词工作台、拆书导入、知识面板或局部返修交互，先记到 `references/tooling-adoption-roadmap.md`，再决定是否值得落脚本或 UI。
5. 如果它主要属于局部返修方法，优先并入 `references/micro-revision-ops.md`，不要散写在多个文档里。
6. 优先把稳定原则并入对应的既有规则或参考文件。
7. 优先吸收可操作、可复用、可验证的内容。
8. 只适用于单个项目的经验，写进项目文档，不污染通用规则。
9. 涉及“借鉴”时，先区分借的是开放框架设定，还是具体剧情、人物、关系和桥段。
