# 平台输出门禁

用于把“平台差异”压缩成轻量后处理检查，而不是把整套仓库扩成多平台大系统。

当前默认命令：

```bash
python3 scripts/chapter_pipeline.py platform-gate <文件路径> --platform 起点中文网
```

支持两种检查类型：

- `--kind chapter`：检查章节稿
- `--kind marketing`：检查营销 Brief

## 默认能力

### 章节稿门禁

自动检查：

- 单章字数是否落在平台建议区间
- 开头前三段是否有足够可见钩子信号
- 结尾是否停在动作、危险、发现或未决选择上
- 对白平均长度是否偏高
- 是否命中 AI 套语 / 解释腔 / 抽象心理 / POV 越权等静态风险

### 营销 Brief 门禁

自动检查：

- 核心 Section 是否齐全
- Brief 体量是否足够支撑平台改写
- 是否明确写出目标平台

## 当前内置平台

- 起点中文网
- 番茄小说网
- 七猫小说
- 知乎盐选
- 微信订阅号
- 豆瓣阅读
- WebNovel
- 出版社稿

## 与 `marketing` 的关系

- `marketing --platform <平台>`：生成营销 Brief 时自动附带平台输出门禁清单
- `platform-gate`：对已经生成的章节稿或 Brief 做后处理检查

推荐顺序：

1. 先跑 `marketing --platform ...`
2. 再对输出稿跑 `platform-gate`
3. 按报告里的“建议下一轮动作”做定向返修

## 常用示例

章节稿：

```bash
python3 scripts/chapter_pipeline.py platform-gate ./我的小说/manuscript/0007_夜审.md \
  --platform 起点中文网 \
  --kind chapter
```

营销 Brief：

```bash
python3 scripts/chapter_pipeline.py marketing ./我的小说 \
  --platform 番茄小说网 \
  --output-file ./我的小说/runtime/marketing-brief.md

python3 scripts/chapter_pipeline.py platform-gate ./我的小说/runtime/marketing-brief.md \
  --platform 番茄小说网 \
  --kind marketing
```

写入文件：

```bash
python3 scripts/chapter_pipeline.py platform-gate ./我的小说/manuscript/0007_夜审.md \
  --platform 起点中文网 \
  --output-file ./我的小说/runtime/platform-gate-0007.md
```

## 使用原则

1. 平台门禁只做后处理检查，不替代正文创作和人工判断。
2. 平台适配不能改坏作品真正的题材承诺和长期卖点。
3. 门禁命中后优先定向返修，不要默认全文重写。
4. 如果平台未内置，先回到 `docs/作者意图.md` 的平台与商业约束做人判。
