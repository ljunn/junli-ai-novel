#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化长篇小说项目结构。"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
REFERENCES_DIR = ROOT_DIR / "references"


def load_template(filename: str, fallback: str) -> str:
    path = REFERENCES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def build_task_log(project_name: str) -> str:
    return f"""# 创作进度日志

## 当前状态
- 创作阶段：规划中
- 书名：{project_name}
- 最新章节：无
- 当前视角：
- 主角位置：
- 主角状态：
- 下一章目标：
- 累计完成章节：0
- 累计完成字数：0

## 最近三章摘要
- 暂无

## 活跃伏笔
| 伏笔名称 | 埋设章节 | 当前状态 |
|----------|----------|----------|

## 待处理
- [ ] 待回收伏笔
- [ ] 待出场角色
- [ ] 未解决矛盾
"""


def build_worldview_template() -> str:
    return """# 世界观

## 前台逻辑层级
- 当前主要由哪一层逻辑驱动：
- 其他层级如何作为背景支撑：

## 题材基石
- 当前题材更偏：现实 / 历史 / 虚构
- 这一题材最需要优先研究或搭牢的规则：

## 空间尺度
- 当前故事主要发生在哪个尺度：
- 暂时不展开的更大空间：
- 当前更适合：扩展 / 升级 / 维持现状
- 当前世界更偏：开放 / 封闭 / 局部封闭远处开放

## 自然层

### 自然形态
- 地理环境：
- 关键资源：
- 生命形态：

### 自然规则
- 底层铁律：
- 可突破的表层规则：
- 打破表层规则的代价：

## 文明层

### 文明形态
- 势力结构：
- 社会结构：
- 制度与工具：

### 文明规则
- 权力逻辑：
- 分配逻辑：
- 价值观排序：
- 禁忌：

## 历史沉淀
- 旧战争 / 旧站队 / 旧恩怨：
- 这些历史如何塑造今天：

## 动态循环
- 自然如何限制文明：
- 文明如何改造自然：
- 当前系统最脆弱的地方：

## 从世界生长出的故事
- 最稀缺的资源/名额：
- 谁在控制它：
- 谁被排除在外：
- 主角当前站位：
- 主角一旦打破规则，世界会如何反应：
- 升级或成长的代价与天花板：

## 验证顺序
- 底层逻辑：
- 天然矛盾：
- 核心人物：
- 冲突升级路径：

## 扩展与升级规划
- 下一步是横向扩展还是纵向升级：
- 新空间将带来什么新规则或新矛盾：
- 如何自然过渡到新空间：
"""


def build_conflict_template() -> str:
    return """# 冲突设计

## 核心冲突
- [主角想要什么？什么阻止了他？]

## 冲突土壤

### 资源稀缺
- 稀缺的是什么：
- 谁在争：
- 为什么不够分：

### 规则压力
- 自然法则：
- 文明规则：
- 谁受益：
- 谁受损：

### 历史积怨
- 过去发生过什么：
- 现在谁还在承担后果：

## 三层冲突
| 层级 | 当前冲突 | 主要角色/势力 | 代价 |
|------|----------|----------------|------|
| 宏观 |  |  |  |
| 中观 |  |  |  |
| 微观 |  |  |  |
"""


def build_rules_template() -> str:
    return """# 法则

## 境界 / 等级体系

## 能力限制

## 冲突红线

## 不可违背规则
"""


def build_foreshadow_template() -> str:
    return """# 伏笔记录

## 活跃伏笔
| 伏笔名称 | 埋设章节 | 伏笔类型 | 关联章节 |
|----------|----------|----------|----------|

## 已回收伏笔
| 伏笔名称 | 埋设章节 | 回收章节 | 备注 |
|----------|----------|----------|------|
"""


def build_timeline_template() -> str:
    return """# 剧情时间线

## 第一卷

| 时间点 | 事件 | 章节 |
|--------|------|------|
"""


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_novel_project(project_name: str, target_dir: str | None = None, force: bool = False) -> Path:
    base_dir = Path(target_dir).expanduser().resolve() if target_dir else Path.cwd()
    project_dir = base_dir / project_name

    for folder in ("docs", "characters", "manuscript", "plot"):
        (project_dir / folder).mkdir(parents=True, exist_ok=True)

    outline = load_template("outline-template.md", "# 大纲\n")
    outline = outline.replace("[小说名称]", project_name)
    character = load_template("character-template.md", "# 人物档案\n")

    files = {
        project_dir / "docs" / "大纲.md": outline,
        project_dir / "docs" / "冲突设计.md": build_conflict_template(),
        project_dir / "docs" / "世界观.md": build_worldview_template(),
        project_dir / "docs" / "法则.md": build_rules_template(),
        project_dir / "characters" / "人物档案.md": character,
        project_dir / "plot" / "伏笔记录.md": build_foreshadow_template(),
        project_dir / "plot" / "时间线.md": build_timeline_template(),
        project_dir / "task_log.md": build_task_log(project_name),
    }

    for path, content in files.items():
        write_file(path, content, force=force)

    print(f"项目创建成功：{project_dir}")
    return project_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="创建长篇小说项目结构")
    parser.add_argument("project_name", nargs="?", default="my-novel", help="项目目录名")
    parser.add_argument("--target-dir", help="项目创建到哪个目录下，默认当前目录")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的模板文件")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_novel_project(args.project_name, target_dir=args.target_dir, force=args.force)
