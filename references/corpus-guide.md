# 本地范本检索指南

这份文件只做一件事：把“范本检索 -> 归纳 -> 回到本章执行”这条链路走顺。

默认原则：

- 不抄句子，只借结构。
- 重点看起势、信息投放、对白张力和章末停点。
- 范本结论不能压过 `Goal / Must Keep / Must Avoid`。

## 什么时候用

只要任务涉及这些内容，默认先查：

- 开头怎么抓人
- 某个题材怎么起势
- 对白怎么更有后果
- 章末怎么更像“下一章入口”
- 用户说“太平”“没钩子”“太解释”“不像这个题材”

## 先做什么

先构建索引：

```bash
python3 scripts/build_corpus_assets.py
```

常用检索：

```bash
python3 scripts/search_corpus_examples.py --list-tags
python3 scripts/search_corpus_examples.py --type '开头钩子' --tag '危机压身' --limit 5
python3 scripts/search_corpus_examples.py --type '高张力对白' --keyword '退婚' --limit 5
python3 scripts/search_corpus_examples.py --type '结尾余韵' --keyword '重逢' --limit 5
```

## 怎么用命中结果

不要只看“这一段好不好看”，要拆这四件事：

- 第几句把异常局面立起来
- 主角通过什么动作亮相
- 信息是塞进动作、对白还是结果里
- 这一段停在什么变化上

## 新样本怎么补

往 `corpus/articles/` 里新增 `.md` 或 `.txt` 文件。推荐格式：

```md
# 标题

标签：真假千金 | 身份反差
摘要：一句话说清这篇样本最值得借的地方。

## 开头钩子
...

## 主角亮相
...

## 高张力对白
...

## 结尾余韵
...

## 迁移提醒
- 只写能迁移的结构结论
```

新增后重建：

```bash
python3 scripts/build_corpus_assets.py
```

## 接入章节工作流

`plan / compose / next-chapter` 会自动尝试命中本地范本，并把结果写到：

- `runtime/chapter-XXXX.references.md`

命中不到时不会阻塞正文流程。
