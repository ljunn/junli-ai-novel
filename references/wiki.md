# References Wiki

不要从头平扫整个 `references/`。

默认顺序：

1. 先判断任务属于 `立项 / 单章执行 / 返修质检 / 长篇治理 / 平台包装` 哪一类
2. 先打开对应的 hub 页面
3. 再按 hub 提示下钻到 1-3 份原子 reference

原则：

- 先走入口页，再下钻，不要一次性加载整片方法论文档
- 优先加载“当前步骤最需要”的那几份，而不是“可能以后也会用到”的那几份
- `references/chapter/writing-quickref.md` 属于特殊文件：会由 `plan / compose` 自动注入 intent，不需要手动查

## 入口

- 立项 / 世界观 / 大纲 / 人设：`references/hubs/planning.md`
- 继续写下一章 / 单章执行 / 场景推进：`references/hubs/chapter-execution.md`
- 单章扩写 / 去 AI 味 / 对白返修 / 质检：`references/hubs/revision-quality.md`
- 长篇治理 / 分卷 / 阶段规划 / 审计：`references/hubs/governance.md`
- 营销 Brief / 平台输出 / 上架文案：`references/hubs/platform.md`

## 不要这样用

- 不要把 `references/` 当资料堆，看到什么都读
- 不要在 `SKILL.md` 里长期维护几十个平铺文件名
- 不要为了“分类更细”继续加 3-4 层目录；深度过大会让导航比内容更重

## 维护规则

- 新增 reference 时，先判断它归哪个 hub
- 先补 hub 页面的一行用途说明，再决定是否在 `SKILL.md` 里直接提它
- 只有高频、强约束、容易被模型漏掉的文档，才值得在 `SKILL.md` 里点名
