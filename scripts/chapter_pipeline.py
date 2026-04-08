#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一的新建、恢复、开写、质检与完结入口。"""

from __future__ import annotations

import argparse
from datetime import date
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from chapter_text import is_chapter_file
    from check_chapter_wordcount import check_chapter
    from check_emotion_curve import analyze_chapter_emotion_curve
    from extract_thrills import analyze_thrills_and_poisons
    from new_project import create_novel_project, ensure_longform_governance_files
    from update_progress import (
        STATUS_DONE,
        STATUS_IN_PROGRESS,
        compute_manuscript_stats,
        update_governance_state,
        update_progress,
    )
except ModuleNotFoundError:
    from scripts.chapter_text import is_chapter_file
    from scripts.check_chapter_wordcount import check_chapter
    from scripts.check_emotion_curve import analyze_chapter_emotion_curve
    from scripts.extract_thrills import analyze_thrills_and_poisons
    from scripts.new_project import create_novel_project, ensure_longform_governance_files
    from scripts.update_progress import (
        STATUS_DONE,
        STATUS_IN_PROGRESS,
        compute_manuscript_stats,
        update_governance_state,
        update_progress,
    )


REQUIRED_MEMORY_FILES = (
    "task_log.md",
    "docs/大纲.md",
    "plot/伏笔记录.md",
    "plot/时间线.md",
)

LONGFORM_GOVERNANCE_FILES = (
    "docs/全书宪法.md",
    "docs/卷纲.md",
    "docs/阶段规划.md",
    "docs/变更日志.md",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_state_field(text: str, label: str, default: str = "无") -> str:
    match = re.search(rf"(?m)^- {re.escape(label)}(.*)$", text)
    if not match:
        return default
    value = match.group(1).strip()
    return value or default


def extract_section_lines(text: str, header: str) -> list[str]:
    match = re.search(rf"(?ms)^## {re.escape(header)}\n(.*?)(?=^## |\Z)", text)
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def extract_active_plot_rows(text: str) -> list[str]:
    rows = []
    for line in extract_section_lines(text, "活跃伏笔"):
        if not line.startswith("|"):
            continue
        if set(line.replace("|", "").replace("-", "").strip()) == set():
            continue
        if "伏笔名称" in line:
            continue
        rows.append(line)
    return rows


def list_recent_chapters(project_dir: Path, limit: int = 3) -> list[Path]:
    manuscript_dir = project_dir / "manuscript"
    if not manuscript_dir.exists():
        return []
    chapters = [path for path in sorted(manuscript_dir.glob("*.md")) if is_chapter_file(path)]
    return chapters[-limit:]


def parse_chapter_number_from_text(raw: str) -> int | None:
    match = re.search(r"第(\d+)章", raw)
    if match:
        return int(match.group(1))
    return None


def parse_chapter_number_from_path(path: Path) -> int | None:
    match = re.match(r"^(\d{3,4})[_-]", path.name)
    if match:
        return int(match.group(1))
    return parse_chapter_number_from_text(path.stem)


def collect_missing_memory_files(project_dir: Path) -> list[str]:
    return [relative for relative in REQUIRED_MEMORY_FILES if not (project_dir / relative).exists()]


def collect_missing_longform_files(project_dir: Path) -> list[str]:
    return [relative for relative in LONGFORM_GOVERNANCE_FILES if not (project_dir / relative).exists()]


def parse_count_value(raw_value: str) -> int | None:
    if not raw_value or raw_value in {"未记录", "无", "待定", "未知"}:
        return None
    raw_value = raw_value.replace(",", "").replace("，", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", raw_value)
    if not match:
        return None
    value = float(match.group(1))
    if "万" in raw_value:
        value *= 10000
    return int(value)


def task_log_update_field(text: str, label: str, value: str) -> str:
    pattern = rf"(?m)^- {re.escape(label)}.*$"
    replacement = f"- {label}{value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    current_state = "## 当前状态\n"
    if current_state in text:
        return text.replace(current_state, current_state + replacement + "\n", 1)
    return text.rstrip() + "\n\n## 当前状态\n" + replacement + "\n"


def append_section_bullet(text: str, header: str, line: str) -> str:
    pattern = rf"(?ms)(^## {re.escape(header)}\n)(.*?)(?=^## |\Z)"
    match = re.search(pattern, text)
    if match:
        lines = [item for item in match.group(2).splitlines() if item.strip() and item.strip() != "- 暂无"]
        lines.insert(0, line)
        body = "\n".join(lines[:10]).rstrip() + "\n"
        return text[: match.start(2)] + body + text[match.end(2) :]
    return text.rstrip() + f"\n\n## {header}\n{line}\n"


def update_task_log_audit(project_dir: Path, scope: str, status: str, summary_line: str) -> None:
    task_log_path = project_dir / "task_log.md"
    if not task_log_path.exists():
        return
    text = task_log_path.read_text(encoding="utf-8")
    today = date.today().isoformat()
    label = "最近阶段审计：" if scope == "stage" else "最近卷审计："
    chapter_label = "最近阶段审计章节：" if scope == "stage" else "最近卷审计章节："
    header = "阶段审计记录" if scope == "stage" else "卷审计记录"
    chapter_count, _ = compute_manuscript_stats(project_dir)
    text = task_log_update_field(text, label, f"{today} {status}")
    text = task_log_update_field(text, chapter_label, str(chapter_count))
    text = append_section_bullet(text, header, f"- {today} | {status} | {summary_line}")
    task_log_path.write_text(text, encoding="utf-8")


def requires_longform_governance(project_dir: Path, summary: dict) -> bool:
    chapter_count, total_words = compute_manuscript_stats(project_dir)
    target_words = parse_count_value(summary.get("planned_total_words", ""))
    if target_words and target_words >= 500000:
        return True
    if total_words >= 100000:
        return True
    if chapter_count >= 20:
        return True
    return False


def stage_audit_is_stale(summary: dict, chapter_count: int, interval: int = 20) -> bool:
    last_audit_chapter = parse_count_value(summary.get("last_stage_audit_chapter", "")) or 0
    if chapter_count < interval:
        return False
    return chapter_count - last_audit_chapter >= interval


def summarize_project(project_dir: Path) -> dict:
    task_log_path = project_dir / "task_log.md"
    task_log = read_text(task_log_path)
    recent_chapter_files = list_recent_chapters(project_dir)

    recent_summaries = extract_section_lines(task_log, "最近三章摘要")
    if not recent_summaries:
        recent_summaries = [f"- {path.stem}" for path in recent_chapter_files]

    active_plots = extract_active_plot_rows(task_log)
    if not active_plots:
        plot_log = read_text(project_dir / "plot" / "伏笔记录.md")
        active_plots = extract_active_plot_rows(plot_log)

    return {
        "project_dir": str(project_dir),
        "missing_files": collect_missing_memory_files(project_dir),
        "stage": extract_state_field(task_log, "创作阶段：", "未知"),
        "latest_chapter": extract_state_field(task_log, "最新章节：", "无"),
        "current_chapter": extract_state_field(task_log, "当前处理章节：", "无"),
        "planned_total_words": extract_state_field(task_log, "目标总字数：", "未记录"),
        "target_volumes": extract_state_field(task_log, "目标卷数：", "未记录"),
        "current_volume": extract_state_field(task_log, "当前卷：", "未记录"),
        "current_phase": extract_state_field(task_log, "当前阶段：", "未记录"),
        "phase_goal": extract_state_field(task_log, "当前阶段目标：", "未记录"),
        "last_stage_audit": extract_state_field(task_log, "最近阶段审计：", "未记录"),
        "last_stage_audit_chapter": extract_state_field(task_log, "最近阶段审计章节：", "0"),
        "last_volume_audit": extract_state_field(task_log, "最近卷审计：", "未记录"),
        "last_volume_audit_chapter": extract_state_field(task_log, "最近卷审计章节：", "0"),
        "pending_setting_sync": extract_state_field(task_log, "设定变更待同步：", "未记录"),
        "viewpoint": extract_state_field(task_log, "当前视角：", "未记录"),
        "protagonist_location": extract_state_field(task_log, "主角位置：", "未记录"),
        "protagonist_state": extract_state_field(task_log, "主角状态：", "未记录"),
        "next_goal": extract_state_field(task_log, "下一章目标：", "未记录"),
        "recent_summaries": recent_summaries[:3],
        "active_plots": active_plots[:6],
        "active_plot_count": len(active_plots),
        "missing_longform_files": collect_missing_longform_files(project_dir),
        "recent_chapter_files": [str(path) for path in recent_chapter_files],
    }


def determine_target_chapter_num(project_dir: Path, summary: dict, explicit: int | None = None) -> int:
    if explicit is not None:
        return explicit

    current_num = parse_chapter_number_from_text(summary.get("current_chapter", ""))
    if current_num is not None:
        return current_num

    latest_num = parse_chapter_number_from_text(summary.get("latest_chapter", ""))
    if latest_num is not None:
        return latest_num + 1

    recent_files = list_recent_chapters(project_dir, limit=1)
    if recent_files:
        recent_num = parse_chapter_number_from_path(recent_files[-1])
        if recent_num is not None:
            return recent_num + 1

    return 1


def read_guidance(args: argparse.Namespace) -> str:
    guidance = (getattr(args, "guidance", None) or "").strip()
    guidance_file = getattr(args, "guidance_file", None)
    if guidance_file:
        file_text = Path(guidance_file).expanduser().resolve().read_text(encoding="utf-8").strip()
        if guidance and file_text:
            return guidance + "\n" + file_text
        if file_text:
            return file_text
    return guidance


def first_meaningful_value(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized and normalized not in {"未记录", "无", "待定", "未知", "未开始"}:
            return normalized
    return None


def runtime_prefix(chapter_num: int) -> str:
    return f"chapter-{chapter_num:04d}"


def runtime_paths(project_dir: Path, chapter_num: int) -> dict[str, Path]:
    prefix = runtime_prefix(chapter_num)
    runtime_dir = project_dir / "runtime"
    return {
        "runtime_dir": runtime_dir,
        "intent": runtime_dir / f"{prefix}.intent.md",
        "context": runtime_dir / f"{prefix}.context.json",
        "scenes": runtime_dir / f"{prefix}.scenes.md",
        "rule_stack": runtime_dir / f"{prefix}.rule-stack.yaml",
        "trace": runtime_dir / f"{prefix}.trace.json",
    }


def excerpt_text(text: str, keyword: str | None = None, max_chars: int = 600) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if keyword and keyword in cleaned:
        index = cleaned.index(keyword)
        start = max(0, index - max_chars // 3)
        end = min(len(cleaned), index + (max_chars * 2 // 3))
        cleaned = cleaned[start:end]
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip() + "..."
    return cleaned


def count_keyword_hits(text: str, keywords: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for keyword in keywords:
        count = text.count(keyword)
        if count > 0:
            hits.append({"keyword": keyword, "count": count})
    return hits


def load_lint_rules(project_dir: Path, rule_set: str = "novel-lint") -> list[dict[str, Any]]:
    rule_dir = project_dir / "rules" / rule_set
    if not rule_dir.exists():
        return []

    rules: list[dict[str, Any]] = []
    for path in sorted(rule_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            continue
        data["path"] = str(path)
        rules.append(data)
    return rules


def scoped_text_for_rule(text: str, scope: str) -> str:
    if scope == "dialogue":
        dialogue_chunks: list[str] = []
        for pattern in (r"“([^”]{1,200})”", r"\"([^\"]{1,200})\""):
            dialogue_chunks.extend(re.findall(pattern, text))
        return "\n".join(chunk.strip() for chunk in dialogue_chunks if chunk.strip())
    if scope == "ending":
        stripped = text.strip()
        if not stripped:
            return stripped
        segment = max(400, len(stripped) // 5)
        return stripped[-segment:]
    return text


def lint_chapter_text(text: str, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for rule in rules:
        if rule.get("type") != "keywords":
            continue
        scope = str(rule.get("scope", "full"))
        threshold = int(rule.get("threshold", 1))
        scoped = scoped_text_for_rule(text, scope)
        hits = count_keyword_hits(scoped, list(rule.get("keywords", [])))
        total = sum(item["count"] for item in hits)
        if total < threshold:
            continue
        findings.append({
            "id": rule.get("id"),
            "name": rule.get("name"),
            "severity": rule.get("severity", "warning"),
            "scope": scope,
            "message": rule.get("message", ""),
            "total_hits": total,
            "hits": hits,
            "rule_path": rule.get("path"),
        })
    return findings


def load_context_source(path: Path, reason: str, keyword: str | None = None, max_chars: int = 600) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    excerpt = excerpt_text(text, keyword=keyword, max_chars=max_chars)
    if not excerpt:
        return None
    return {
        "source": str(path),
        "reason": reason,
        "excerpt": excerpt,
    }


def build_chapter_intent(summary: dict, chapter_num: int, chapter_title: str | None, guidance: str, selected_sources: list[dict]) -> str:
    goal = first_meaningful_value(guidance, summary.get("phase_goal"), summary.get("next_goal")) or "推进当前主线"

    must_keep: list[str] = []
    if summary.get("current_volume") not in {"未记录", "未开始", "无", ""}:
        must_keep.append(f"本章仍属于{summary['current_volume']}，不要写成跨卷结算。")
    if summary.get("current_phase") not in {"未记录", "未开始", "无", ""}:
        must_keep.append(f"本章必须服务{summary['current_phase']}。")
    if summary.get("phase_goal") not in {"未记录", "无", ""}:
        must_keep.append(f"阶段目标：{summary['phase_goal']}")
    if summary.get("protagonist_state") not in {"未记录", "无", ""}:
        must_keep.append(f"主角当前状态：{summary['protagonist_state']}")
    if summary.get("viewpoint") not in {"未记录", "无", ""}:
        must_keep.append(f"当前视角优先贴紧：{summary['viewpoint']}")

    must_avoid: list[str] = []
    if summary.get("pending_setting_sync") not in {"未记录", "无", ""}:
        must_avoid.append(f"不要跳过待同步设定变更：{summary['pending_setting_sync']}")
    must_avoid.append("不要让本章把主线、支线和阶段问题同时清零。")
    must_avoid.append("不要无计划新增大量新设定或新伏笔。")

    conflicts: list[str] = []
    if summary.get("next_goal") not in {"未记录", "无", ""}:
        conflicts.append(f"推进目标：{summary['next_goal']}")
    for hook_row in summary.get("active_plots", [])[:3]:
        conflicts.append(f"伏笔压力：{hook_row}")

    hook_lines = summary.get("active_plots", [])[:3]
    if not hook_lines:
        hook_lines = ["- 暂无高优先级伏笔推进"]
    else:
        hook_lines = [f"- {row}" if not str(row).startswith("-") else str(row) for row in hook_lines]

    source_lines = [f"- {Path(item['source']).name}: {item['reason']}" for item in selected_sources]
    if not source_lines:
        source_lines = ["- 暂无"]

    must_keep_lines = [f"- {item}" for item in must_keep] or ["- 暂无"]
    must_avoid_lines = [f"- {item}" for item in must_avoid] or ["- 暂无"]
    conflict_lines = [f"- {item}" for item in conflicts] or ["- 暂无"]

    lines = [
        "# Chapter Intent",
        "",
        f"## Chapter",
        f"第{chapter_num}章" + (f"：{chapter_title}" if chapter_title else ""),
        "",
        "## Goal",
        goal,
        "",
        "## Scope",
        f"- 当前卷：{summary.get('current_volume', '未记录')}",
        f"- 当前阶段：{summary.get('current_phase', '未记录')}",
        f"- 当前阶段目标：{summary.get('phase_goal', '未记录')}",
        "",
        "## Must Keep",
        *must_keep_lines,
        "",
        "## Must Avoid",
        *must_avoid_lines,
        "",
        "## Conflicts",
        *conflict_lines,
        "",
        "## Hook Agenda",
        "### Must Advance",
        *hook_lines,
        "",
        "## Inputs",
        *source_lines,
        "",
    ]
    return "\n".join(lines)


def build_runtime_sources(project_dir: Path, summary: dict, chapter_num: int, guidance: str) -> list[dict]:
    sources: list[dict] = []

    def add(path_str: str, reason: str, keyword: str | None = None, max_chars: int = 600) -> None:
        source = load_context_source(project_dir / path_str, reason, keyword=keyword, max_chars=max_chars)
        if source:
            sources.append(source)

    current_volume = summary.get("current_volume")
    current_phase = summary.get("current_phase")
    add("docs/全书宪法.md", "最高优先级硬约束", keyword="## 全书终局")
    add("docs/卷纲.md", "当前卷推进约束", keyword=current_volume if current_volume not in {"未记录", "未开始", "无", ""} else None)
    add("docs/阶段规划.md", "当前阶段推进约束", keyword=current_phase if current_phase not in {"未记录", "未开始", "无", ""} else None)
    add("docs/作者意图.md", "长期作者意图")
    add("docs/当前焦点.md", "最近 1-3 章焦点")
    add("docs/大纲.md", "章节与主线总览", keyword="## 章节规划")
    add("task_log.md", "当前运行状态与最近摘要", keyword="## 当前状态")
    add("plot/伏笔记录.md", "活跃伏笔与回收债务", keyword="## 活跃伏笔")
    add("plot/时间线.md", "时间线与出场顺序")
    add("characters/人物档案.md", "人物档案与关系记忆")

    recent_files = list_recent_chapters(project_dir, limit=1)
    if recent_files:
        previous = recent_files[-1]
        prev = load_context_source(previous, "上一章正文结尾与承接", max_chars=800)
        if prev:
            sources.append(prev)

    if guidance:
        sources.append({
            "source": "cli:guidance",
            "reason": "本次人工补充指令",
            "excerpt": excerpt_text(guidance, max_chars=400),
        })

    return sources


def render_rule_stack_yaml(summary: dict, chapter_num: int, chapter_title: str | None) -> str:
    hard_rules = [
        "遵守 docs/全书宪法.md 的终局、法则和关系边界",
        "不得与 docs/世界观.md / docs/法则.md / characters/*.md 冲突",
        "本章必须服务当前卷、当前阶段和当前阶段目标",
        "正文必须写入纯正文，不输出章节壳",
    ]
    soft_rules = [
        f"目标章节：第{chapter_num}章" + (f"《{chapter_title}》" if chapter_title else ""),
        f"当前卷：{summary.get('current_volume', '未记录')}",
        f"当前阶段：{summary.get('current_phase', '未记录')}",
        f"当前阶段目标：{summary.get('phase_goal', '未记录')}",
        f"下一章目标：{summary.get('next_goal', '未记录')}",
    ]
    diagnostic_rules = [
        "检查是否缺少前台问题、阶段回报和结尾钩子",
        "检查是否出现视角越权、设定污染和伏笔债务堆积",
        "检查是否新增了与当前阶段无关的支线负担",
    ]

    lines = [
        "chapter:",
        f"  number: {chapter_num}",
        f"  title: \"{chapter_title or ''}\"",
        "layers:",
        "  - id: constitution",
        "    scope: L4",
        "    precedence: 400",
        "  - id: longform-governance",
        "    scope: L3",
        "    precedence: 300",
        "  - id: project-runtime",
        "    scope: L2",
        "    precedence: 200",
        "  - id: chapter-execution",
        "    scope: L1",
        "    precedence: 100",
        "sections:",
        "  hard:",
        *(f"    - {item}" for item in hard_rules),
        "  soft:",
        *(f"    - {item}" for item in soft_rules),
        "  diagnostic:",
        *(f"    - {item}" for item in diagnostic_rules),
        "",
    ]
    return "\n".join(lines)


def build_scene_cards(summary: dict, chapter_num: int, chapter_title: str | None, guidance: str) -> str:
    pov = first_meaningful_value(summary.get("viewpoint")) or "主 POV"
    location = first_meaningful_value(summary.get("protagonist_location")) or "当前主要场域"
    goal = first_meaningful_value(guidance, summary.get("phase_goal"), summary.get("next_goal")) or "推进当前主线"
    state = first_meaningful_value(summary.get("protagonist_state")) or "带着未结问题入场"
    hook_pressure = summary.get("active_plots", [])[:2]
    hook_note = "；".join(str(item) for item in hook_pressure) if hook_pressure else "暂无高优先级伏笔压力"

    scenes = [
        {
            "title": "场景一：承接与入场",
            "function": "承接上章钩子，迅速把主角推回当前前台问题",
            "want": goal,
            "block": "立刻出现的规则压力、资源压力或关系阻力",
            "relation": "至少让一组人物关系出现轻微错位、试探或拉扯",
            "info": "补足本章必须知道但此前未说透的信息",
            "handoff": "把局势推进到必须正面对抗或做选择",
        },
        {
            "title": "场景二：正面对抗",
            "function": "让人物围绕目标发生真正对抗，而不是信息复述",
            "want": "拿到、守住、证明、隐瞒或逃离某件事",
            "block": "来自人物、规则或现实条件的直接阻拦",
            "relation": "关系发生可感知变化，不能只是态度重复",
            "info": f"给出本章最重要的信息增量，并注意伏笔压力：{hook_note}",
            "handoff": "形成新的失衡、误判或代价",
        },
        {
            "title": "场景三：结算与钩子",
            "function": "给阶段性回报，同时把读者送进下一章问题",
            "want": "让本章至少兑现一项回报：爽点、情绪点、关系点或信息收益",
            "block": "不能把主线、支线和阶段问题同时清零",
            "relation": "让本章关系变化固定下来，留下下一步张力",
            "info": "明确本章结尾的新问题、新危险或新选择",
            "handoff": "结尾停在动作、发现、选择或危险上",
        },
    ]

    lines = [
        "# Scene Cards",
        "",
        "## Chapter",
        f"第{chapter_num}章" + (f"：{chapter_title}" if chapter_title else ""),
        "",
        "## Runtime Summary",
        f"- 当前卷：{summary.get('current_volume', '未记录')}",
        f"- 当前阶段：{summary.get('current_phase', '未记录')}",
        f"- 当前阶段目标：{summary.get('phase_goal', '未记录')}",
        f"- 主 POV：{pov}",
        f"- 主角位置：{location}",
        f"- 主角状态：{state}",
        f"- 本章总目标：{goal}",
        "",
    ]

    for scene in scenes:
        lines.extend([
            scene["title"],
            f"- 地点：{location}",
            f"- POV：{pov}",
            f"- 场景功能：{scene['function']}",
            f"- 谁想要什么：{scene['want']}",
            f"- 谁阻止谁：{scene['block']}",
            f"- 关系怎么变：{scene['relation']}",
            f"- 信息增量：{scene['info']}",
            f"- 推向下一场：{scene['handoff']}",
            "",
        ])

    return "\n".join(lines)


def materialize_plan(project_dir: Path, summary: dict, chapter_num: int, chapter_title: str | None, guidance: str) -> dict:
    paths = runtime_paths(project_dir, chapter_num)
    paths["runtime_dir"].mkdir(parents=True, exist_ok=True)
    selected_sources = build_runtime_sources(project_dir, summary, chapter_num, guidance)
    intent_content = build_chapter_intent(summary, chapter_num, chapter_title, guidance, selected_sources)
    paths["intent"].write_text(intent_content, encoding="utf-8")
    return {
        "chapter": chapter_num,
        "intent_path": str(paths["intent"]),
        "goal": first_meaningful_value(guidance, summary.get("phase_goal"), summary.get("next_goal")) or "推进当前主线",
        "selected_sources": selected_sources,
    }


def materialize_runtime_package(project_dir: Path, summary: dict, chapter_num: int, chapter_title: str | None, guidance: str) -> dict:
    plan_result = materialize_plan(project_dir, summary, chapter_num, chapter_title, guidance)
    paths = runtime_paths(project_dir, chapter_num)
    selected_sources = plan_result["selected_sources"]
    context_payload = {
        "chapter": chapter_num,
        "title": chapter_title or "",
        "goal": plan_result["goal"],
        "current_volume": summary.get("current_volume", "未记录"),
        "current_phase": summary.get("current_phase", "未记录"),
        "phase_goal": summary.get("phase_goal", "未记录"),
        "selectedContext": selected_sources,
    }
    trace_payload = {
        "chapter": chapter_num,
        "plannerInputs": [item["source"] for item in selected_sources],
        "composerInputs": [
            "docs/全书宪法.md",
            "docs/卷纲.md",
            "docs/阶段规划.md",
            "docs/作者意图.md",
            "docs/当前焦点.md",
            "docs/大纲.md",
            "task_log.md",
            "plot/伏笔记录.md",
            "plot/时间线.md",
            "characters/人物档案.md",
        ],
        "selectedSources": [item["source"] for item in selected_sources],
        "notes": [
            "本章运行时产物由本地项目记忆编译生成，不依赖在线 LLM。",
            "如果本章目标或上下文变化，应重新执行 plan / compose。",
        ],
    }

    paths["context"].write_text(json.dumps(context_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["scenes"].write_text(build_scene_cards(summary, chapter_num, chapter_title, guidance), encoding="utf-8")
    paths["trace"].write_text(json.dumps(trace_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["rule_stack"].write_text(render_rule_stack_yaml(summary, chapter_num, chapter_title), encoding="utf-8")

    return {
        "chapter": chapter_num,
        "intent_path": str(paths["intent"]),
        "context_path": str(paths["context"]),
        "scenes_path": str(paths["scenes"]),
        "rule_stack_path": str(paths["rule_stack"]),
        "trace_path": str(paths["trace"]),
        "goal": plan_result["goal"],
        "selected_sources": selected_sources,
    }


def print_resume_summary(summary: dict) -> None:
    print("\n" + "=" * 60)
    print("项目恢复摘要")
    print("=" * 60)
    print(f"项目目录: {summary['project_dir']}")
    print(f"创作阶段: {summary['stage']}")
    print(f"目标总字数: {summary['planned_total_words']}")
    print(f"目标卷数: {summary['target_volumes']}")
    print(f"最新章节: {summary['latest_chapter']}")
    print(f"当前处理章节: {summary['current_chapter']}")
    print(f"当前卷: {summary['current_volume']}")
    print(f"当前阶段: {summary['current_phase']}")
    print(f"当前阶段目标: {summary['phase_goal']}")
    print(f"当前视角: {summary['viewpoint']}")
    print(f"主角位置: {summary['protagonist_location']}")
    print(f"主角状态: {summary['protagonist_state']}")
    print(f"下一章目标: {summary['next_goal']}")
    print(f"最近阶段审计: {summary['last_stage_audit']}")
    print(f"最近阶段审计章节: {summary['last_stage_audit_chapter']}")
    print(f"最近卷审计: {summary['last_volume_audit']}")
    print(f"最近卷审计章节: {summary['last_volume_audit_chapter']}")

    if summary["missing_files"]:
        print("\n缺失记忆文件:")
        for item in summary["missing_files"]:
            print(f"- {item}")

    if summary["missing_longform_files"]:
        print("\n缺失超长篇治理文件:")
        for item in summary["missing_longform_files"]:
            print(f"- {item}")

    print("\n最近两到三章摘要:")
    if summary["recent_summaries"]:
        for line in summary["recent_summaries"]:
            print(line if line.startswith("-") else f"- {line}")
    else:
        print("- 暂无")

    print("\n活跃伏笔:")
    if summary["active_plots"]:
        for row in summary["active_plots"]:
            print(f"- {row}")
    else:
        print("- 暂无")

    if summary["recent_chapter_files"]:
        print("\n最近章节文件:")
        for path in summary["recent_chapter_files"]:
            print(f"- {path}")


def print_gate_failures(title: str, failures: list[str]) -> None:
    print("\n" + "!" * 60)
    print(title)
    print("!" * 60)
    for item in failures:
        print(f"- {item}")


def handle_preflight(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    summary = summarize_project(project_dir)
    chapter_count, _ = compute_manuscript_stats(project_dir)
    print_resume_summary(summary)

    failures: list[str] = []
    if summary["missing_files"]:
        failures.append("缺失项目记忆文件，禁止直接续写或开写正文")
    if summary["stage"] == "未知":
        failures.append("task_log.md 未记录创作阶段")
    if summary["next_goal"] in {"未记录", "无", ""}:
        failures.append("task_log.md 未记录下一章目标")
    if requires_longform_governance(project_dir, summary) and summary["missing_longform_files"]:
        failures.append("已进入长篇治理范围，但缺失全书宪法/卷纲/阶段规划/变更日志；先执行 bootstrap-longform")
    if requires_longform_governance(project_dir, summary) and summary["current_volume"] in {"未记录", "未开始", "无", ""}:
        failures.append("长篇项目未记录当前卷，禁止继续推进")
    if requires_longform_governance(project_dir, summary) and summary["current_phase"] in {"未记录", "未开始", "无", ""}:
        failures.append("长篇项目未记录当前阶段，禁止继续推进")
    if requires_longform_governance(project_dir, summary) and stage_audit_is_stale(summary, chapter_count):
        failures.append("阶段审计已过期，先执行 audit --scope stage 再继续正文")

    if failures:
        print_gate_failures("前置校验失败: preflight 未通过", failures)
        return 2

    print("\n前置校验通过，可继续执行 resume / start / 正文创作。")
    return 0


def build_check_report(chapter_path: Path) -> dict:
    rules = load_lint_rules(Path.cwd())
    chapter_text = chapter_path.read_text(encoding="utf-8") if chapter_path.exists() else ""
    return {
        "wordcount": check_chapter(str(chapter_path)),
        "emotion": analyze_chapter_emotion_curve(str(chapter_path)),
        "thrills": analyze_thrills_and_poisons(str(chapter_path)),
        "lint": lint_chapter_text(chapter_text, rules) if chapter_text else [],
    }


def print_check_summary(report: dict) -> None:
    wordcount = report["wordcount"]
    emotion = report["emotion"]
    thrills = report["thrills"]
    lint_findings = report.get("lint", [])

    print("\n" + "=" * 60)
    print(f"章节检查摘要: {Path(wordcount['file']).name}")
    print("=" * 60)

    if not wordcount.get("exists"):
        print(f"- 文件错误: {wordcount.get('message', '未知错误')}")
        return

    print(f"- 字数: {wordcount['word_count']} ({wordcount['status']})")
    print(f"- 情绪走向: {emotion.get('transition', 'unknown')}")
    print(
        f"- 爽点/毒点: thrill={thrills.get('thrill_score', 0)}, "
        f"poison={thrills.get('poison_score', 0)}, overall={thrills.get('overall', 'unknown')}"
    )
    print(f"- 规则检查: {len(lint_findings)} 条命中")

    issues: list[str] = []
    if wordcount["status"] != "pass":
        issues.append("字数未达默认下限")
    if thrills.get("overall") == "negative":
        issues.append("毒点高于爽点，优先做定向返修")
    if emotion.get("opening_emotion") == "neutral" and emotion.get("ending_emotion") == "neutral":
        issues.append("情绪曲线过平，检查是否缺少冲突或钩子")

    if issues:
        print("- 警告:")
        for item in issues:
            print(f"  - {item}")
    if lint_findings:
        print("- 规则命中:")
        for item in lint_findings[:5]:
            print(f"  - {item['name']} ({item['severity']}): {item['message']}")


def handle_lint(args: argparse.Namespace) -> int:
    chapter_path = Path(args.chapter_path).expanduser().resolve()
    if not chapter_path.exists():
        print(json.dumps({"error": f"文件不存在: {chapter_path}"}, ensure_ascii=False, indent=2))
        return 2

    rules = load_lint_rules(Path.cwd(), rule_set=args.rule_set)
    content = chapter_path.read_text(encoding="utf-8")
    findings = lint_chapter_text(content, rules)

    if args.json:
        print(json.dumps({"file": str(chapter_path), "findings": findings}, ensure_ascii=False, indent=2))
        return 0

    print("\n" + "=" * 60)
    print(f"规则检查: {chapter_path.name}")
    print("=" * 60)
    if not findings:
        print("- 未命中规则")
        return 0

    for item in findings:
        print(f"- {item['name']} [{item['severity']}]")
        print(f"  {item['message']}")
        for hit in item["hits"][:5]:
            print(f"  - {hit['keyword']} x{hit['count']}")
    return 0


def extract_dialogue_stats(text: str) -> dict[str, Any]:
    dialogue_chunks: list[str] = []
    for pattern in (r"“([^”]{1,400})”", r"\"([^\"]{1,400})\""):
        dialogue_chunks.extend(re.findall(pattern, text))
    total_lines = len(dialogue_chunks)
    total_chars = sum(len(chunk) for chunk in dialogue_chunks)
    avg_chars = round(total_chars / total_lines, 1) if total_lines else 0
    long_lines = [chunk for chunk in dialogue_chunks if len(chunk) >= 30]
    return {
        "dialogue_lines": total_lines,
        "dialogue_chars": total_chars,
        "avg_chars_per_line": avg_chars,
        "long_lines": long_lines[:5],
    }


def handle_dialogue_pass(args: argparse.Namespace) -> int:
    chapter_path = Path(args.chapter_path).expanduser().resolve()
    if not chapter_path.exists():
        print(json.dumps({"error": f"文件不存在: {chapter_path}"}, ensure_ascii=False, indent=2))
        return 2

    content = chapter_path.read_text(encoding="utf-8")
    stats = extract_dialogue_stats(content)
    rules = [
        rule
        for rule in load_lint_rules(Path.cwd(), rule_set=args.rule_set)
        if str(rule.get("scope", "")) == "dialogue"
    ]
    findings = lint_chapter_text(content, rules)
    result = {
        "file": str(chapter_path),
        "stats": stats,
        "findings": findings,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print("\n" + "=" * 60)
    print(f"对白专审: {chapter_path.name}")
    print("=" * 60)
    print(f"- 对白行数: {stats['dialogue_lines']}")
    print(f"- 对白总字数: {stats['dialogue_chars']}")
    print(f"- 平均每句长度: {stats['avg_chars_per_line']}")
    if stats["long_lines"]:
        print("- 过长对白示例:")
        for item in stats["long_lines"]:
            print(f"  - {excerpt_text(item, max_chars=60)}")
    if findings:
        print("- 规则命中:")
        for item in findings:
            print(f"  - {item['name']} [{item['severity']}] {item['message']}")
    else:
        print("- 规则命中: 无")
    return 0


def add_progress_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("project_path", help="项目根目录")
    parser.add_argument("chapter_num", type=int, help="章节号")
    parser.add_argument("--chapter-title", help="章节标题")
    parser.add_argument("--core-event", help="本章核心事件")
    parser.add_argument("--hook", help="本章悬念钩子")
    parser.add_argument("--next-goal", help="下一章目标")
    parser.add_argument("--viewpoint", help="当前视角人物")
    parser.add_argument("--protagonist-location", help="主角位置")
    parser.add_argument("--protagonist-state", help="主角状态")
    parser.add_argument("--stage", help="创作阶段")
    parser.add_argument("--target-total-words", help="目标总字数，例如 3000000 或 300万")
    parser.add_argument("--target-volumes", help="目标卷数")
    parser.add_argument("--current-volume", help="当前卷，例如 第一卷")
    parser.add_argument("--current-phase", help="当前阶段，例如 阶段1")
    parser.add_argument("--phase-goal", help="当前阶段目标")
    parser.add_argument("--pending-setting-sync", help="待同步的设定变更摘要")
    parser.add_argument("--plot-note", help="新增伏笔备注")


def handle_init(args: argparse.Namespace) -> int:
    create_novel_project(
        args.project_name,
        book_title=args.book_title,
        target_dir=args.target_dir,
        force=args.force,
        mode=args.mode,
        complex_relationships=args.complex_relationships,
        romance_focus=args.romance_focus,
        in_place=not args.subdir,
    )
    return 0


def handle_resume(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    print_resume_summary(summarize_project(project_dir))
    return 0


def handle_plan(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    summary = summarize_project(project_dir)
    chapter_num = determine_target_chapter_num(project_dir, summary, explicit=args.chapter_num)
    guidance = read_guidance(args)
    result = materialize_plan(project_dir, summary, chapter_num, args.chapter_title, guidance)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_resume_summary(summary)
        print("\n" + "=" * 60)
        print("章节意图已生成")
        print("=" * 60)
        print(f"章节: 第{chapter_num}章")
        print(f"意图文件: {result['intent_path']}")
        print(f"目标: {result['goal']}")
    return 0


def handle_compose(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    summary = summarize_project(project_dir)
    chapter_num = determine_target_chapter_num(project_dir, summary, explicit=args.chapter_num)
    guidance = read_guidance(args)
    result = materialize_runtime_package(project_dir, summary, chapter_num, args.chapter_title, guidance)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_resume_summary(summary)
        print("\n" + "=" * 60)
        print("章节运行时产物已生成")
        print("=" * 60)
        print(f"章节: 第{chapter_num}章")
        print(f"意图文件: {result['intent_path']}")
        print(f"上下文文件: {result['context_path']}")
        print(f"场景卡文件: {result['scenes_path']}")
        print(f"规则栈文件: {result['rule_stack_path']}")
        print(f"轨迹文件: {result['trace_path']}")
    return 0


def handle_start(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    summary = summarize_project(project_dir)
    target_label = f"第{args.chapter_num}章"
    effective_next_goal = args.next_goal or summary["next_goal"]
    effective_current_volume = args.current_volume or summary["current_volume"]
    effective_current_phase = args.current_phase or summary["current_phase"]

    failures: list[str] = []
    if summary["missing_files"]:
        failures.append("缺失项目记忆文件，先修记忆，再标记章节进行中")
    if requires_longform_governance(project_dir, summary) and summary["missing_longform_files"]:
        failures.append("缺失超长篇治理文件，先执行 bootstrap-longform")
    if effective_next_goal in {"未记录", "无", ""}:
        failures.append("未记录下一章目标，start 前必须先补 task_log.md 或传入 --next-goal")
    if summary["current_chapter"] not in {"无", target_label}:
        failures.append(f"当前已有进行中章节：{summary['current_chapter']}，不要并发开写多个章节")
    if requires_longform_governance(project_dir, summary) and effective_current_volume in {"未记录", "未开始", "无", ""}:
        failures.append("start 前必须先明确当前卷")
    if requires_longform_governance(project_dir, summary) and effective_current_phase in {"未记录", "未开始", "无", ""}:
        failures.append("start 前必须先明确当前阶段")

    if failures:
        print_resume_summary(summary)
        print_gate_failures("前置校验失败: start 未通过", failures)
        return 2

    update_progress(
        project_path=args.project_path,
        chapter_num=args.chapter_num,
        chapter_title=args.chapter_title,
        core_event=args.core_event,
        hook=args.hook,
        next_goal=args.next_goal,
        viewpoint=args.viewpoint,
        protagonist_location=args.protagonist_location,
        protagonist_state=args.protagonist_state,
        stage=args.stage or "正文创作中",
        target_total_words=args.target_total_words,
        target_volumes=args.target_volumes,
        current_volume=args.current_volume,
        current_phase=args.current_phase,
        phase_goal=args.phase_goal,
        pending_setting_sync=args.pending_setting_sync,
        status=STATUS_IN_PROGRESS,
    )
    return 0


def handle_check(args: argparse.Namespace) -> int:
    chapter_path = Path(args.chapter_path).expanduser().resolve()
    print_check_summary(build_check_report(chapter_path))
    return 0


def handle_finish(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    chapter_path = Path(args.chapter_path).expanduser().resolve()
    summary = summarize_project(project_dir)
    target_label = f"第{args.chapter_num}章"

    failures: list[str] = []
    if summary["missing_files"]:
        failures.append("缺失项目记忆文件，finish 前必须先恢复项目记忆")
    if requires_longform_governance(project_dir, summary) and summary["missing_longform_files"]:
        failures.append("缺失超长篇治理文件，finish 前必须先补齐")
    if summary["current_chapter"] != target_label:
        failures.append(f"当前处理章节不是 {target_label}，请先执行 start 并保持章节状态一致")
    if not chapter_path.exists():
        failures.append(f"章节文件不存在：{chapter_path}")
    if not args.summary:
        failures.append("finish 必须提供 --summary，用于同步章节摘要和项目记忆")

    if failures:
        print_resume_summary(summary)
        print_gate_failures("前置校验失败: finish 未通过", failures)
        return 2

    report = None
    if not args.skip_checks:
        report = build_check_report(chapter_path)
        print_check_summary(report)

    word_count = args.word_count
    if word_count is None:
        result = report["wordcount"] if report else check_chapter(str(chapter_path))
        word_count = result.get("word_count")

    update_progress(
        project_path=args.project_path,
        chapter_num=args.chapter_num,
        word_count=word_count,
        chapter_title=args.chapter_title,
        summary=args.summary,
        core_event=args.core_event,
        hook=args.hook,
        next_goal=args.next_goal,
        viewpoint=args.viewpoint,
        protagonist_location=args.protagonist_location,
        protagonist_state=args.protagonist_state,
        stage=args.stage or "正文创作中",
        target_total_words=args.target_total_words,
        target_volumes=args.target_volumes,
        current_volume=args.current_volume,
        current_phase=args.current_phase,
        phase_goal=args.phase_goal,
        pending_setting_sync=args.pending_setting_sync,
        plot_note=args.plot_note,
        status=STATUS_DONE,
    )
    return 0


def handle_governance(args: argparse.Namespace) -> int:
    update_governance_state(
        args.project_path,
        target_total_words=args.target_total_words,
        target_volumes=args.target_volumes,
        current_volume=args.current_volume,
        current_phase=args.current_phase,
        phase_goal=args.phase_goal,
        pending_setting_sync=args.pending_setting_sync,
        clear_pending_setting_sync=args.clear_pending_setting_sync,
    )
    print_resume_summary(summarize_project(Path(args.project_path).expanduser().resolve()))
    return 0


def build_audit_payload(project_dir: Path, scope: str) -> tuple[dict, list[str], list[str], tuple[int, int]]:
    summary = summarize_project(project_dir)
    chapter_count, total_words = compute_manuscript_stats(project_dir)

    issues: list[str] = []
    warnings: list[str] = []

    if summary["missing_files"]:
        issues.append("项目记忆文件缺失")
    if summary["missing_longform_files"]:
        issues.append("超长篇治理文件缺失")
    if summary["pending_setting_sync"] not in {"无", "未记录", ""}:
        warnings.append(f"存在待同步的设定变更：{summary['pending_setting_sync']}")
    if summary["active_plot_count"] >= 12:
        warnings.append(f"活跃伏笔较多（{summary['active_plot_count']}），检查伏笔债务")
    if chapter_count > 0 and total_words > 0 and total_words / chapter_count < 2500:
        warnings.append("平均章字数偏低，检查是否切章过碎或阶段回报过短")

    if scope == "stage":
        if summary["current_phase"] in {"未记录", "未开始", "无", ""}:
            issues.append("未记录当前阶段")
        if summary["phase_goal"] in {"未记录", "无", ""}:
            issues.append("未记录当前阶段目标")
        phase_plan = read_text(project_dir / "docs" / "阶段规划.md")
        current_phase = summary["current_phase"]
        if current_phase not in {"未记录", "未开始", "无", ""} and current_phase not in phase_plan:
            warnings.append("当前阶段未在 docs/阶段规划.md 中显式出现")
    else:
        if summary["current_volume"] in {"未记录", "未开始", "无", ""}:
            issues.append("未记录当前卷")
        volume_plan = read_text(project_dir / "docs" / "卷纲.md")
        current_volume = summary["current_volume"]
        if current_volume not in {"未记录", "未开始", "无", ""} and current_volume not in volume_plan:
            warnings.append("当前卷未在 docs/卷纲.md 中显式出现")

    return summary, issues, warnings, (chapter_count, total_words)


def handle_bootstrap_longform(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    ensure_longform_governance_files(project_dir, force=args.force)
    summary = summarize_project(project_dir)
    print_resume_summary(summary)
    print("\n已补齐超长篇治理文件。")
    return 0


def handle_audit(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    scope = args.scope
    summary, issues, warnings, stats = build_audit_payload(project_dir, scope)
    chapter_count, total_words = stats
    print_resume_summary(summary)

    print("\n" + "=" * 60)
    print(f"{'阶段' if scope == 'stage' else '卷'}审计")
    print("=" * 60)
    print(f"累计章节: {chapter_count}")
    print(f"累计字数: {total_words}")

    if issues:
        print("\n阻塞问题:")
        for item in issues:
            print(f"- {item}")
    else:
        print("\n阻塞问题: 无")

    if warnings:
        print("\n风险提示:")
        for item in warnings:
            print(f"- {item}")
    else:
        print("\n风险提示: 无")

    status = "pass" if not issues else "fail"
    scope_name = "阶段" if scope == "stage" else "卷"
    summary_line = (
        f"{scope_name}审计 | 章节={chapter_count} | 字数={total_words} | "
        f"阻塞={len(issues)} | 风险={len(warnings)}"
    )
    update_task_log_audit(project_dir, scope, status, summary_line)

    if issues:
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="小说项目统一工作流入口")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化小说项目")
    init_parser.add_argument("project_name", nargs="?", help="项目目录名；默认原地初始化时可不传，使用 --subdir 时作为子目录名")
    init_parser.add_argument("--book-title", help="书名；默认取 project_name，原地初始化且未传时取当前目录名")
    init_parser.add_argument("--target-dir", required=True, help="目标项目目录；必须显式传入")
    init_parser.add_argument("--in-place", action="store_true", default=True, help="直接在目标目录/当前目录初始化（默认行为）")
    init_parser.add_argument("--subdir", action="store_true", help="在目标目录下额外创建一个子目录作为项目根目录")
    init_parser.add_argument("--mode", choices=("single", "dual", "ensemble"), default="single")
    init_parser.add_argument("--complex-relationships", action="store_true", help="创建关系图模板")
    init_parser.add_argument("--romance-focus", action="store_true", help="感情线重要时创建关系图模板")
    init_parser.add_argument("--force", action="store_true", help="覆盖已存在模板")
    init_parser.set_defaults(handler=handle_init)

    resume_parser = subparsers.add_parser("resume", help="恢复项目摘要")
    resume_parser.add_argument("project_path", help="项目根目录")
    resume_parser.set_defaults(handler=handle_resume)

    bootstrap_parser = subparsers.add_parser("bootstrap-longform", help="为已有项目补齐超长篇治理文件")
    bootstrap_parser.add_argument("project_path", help="项目根目录")
    bootstrap_parser.add_argument("--force", action="store_true", help="覆盖已存在的治理文件")
    bootstrap_parser.set_defaults(handler=handle_bootstrap_longform)

    plan_parser = subparsers.add_parser("plan", help="生成本章意图文件")
    plan_parser.add_argument("project_path", help="项目根目录")
    plan_parser.add_argument("--chapter-num", type=int, help="目标章节号；默认自动推断")
    plan_parser.add_argument("--chapter-title", help="目标章节标题")
    plan_parser.add_argument("--guidance", help="本章额外引导")
    plan_parser.add_argument("--guidance-file", help="从文件读取本章引导")
    plan_parser.add_argument("--json", action="store_true", help="输出 JSON")
    plan_parser.set_defaults(handler=handle_plan)

    compose_parser = subparsers.add_parser("compose", help="生成本章运行时上下文/规则栈/轨迹")
    compose_parser.add_argument("project_path", help="项目根目录")
    compose_parser.add_argument("--chapter-num", type=int, help="目标章节号；默认自动推断")
    compose_parser.add_argument("--chapter-title", help="目标章节标题")
    compose_parser.add_argument("--guidance", help="本章额外引导")
    compose_parser.add_argument("--guidance-file", help="从文件读取本章引导")
    compose_parser.add_argument("--json", action="store_true", help="输出 JSON")
    compose_parser.set_defaults(handler=handle_compose)

    governance_parser = subparsers.add_parser("governance", help="同步超长篇治理状态")
    governance_parser.add_argument("project_path", help="项目根目录")
    governance_parser.add_argument("--target-total-words", help="目标总字数，例如 3000000 或 300万")
    governance_parser.add_argument("--target-volumes", help="目标卷数")
    governance_parser.add_argument("--current-volume", help="当前卷，例如 第一卷")
    governance_parser.add_argument("--current-phase", help="当前阶段，例如 阶段1")
    governance_parser.add_argument("--phase-goal", help="当前阶段目标")
    governance_parser.add_argument("--pending-setting-sync", help="待同步的设定变更摘要")
    governance_parser.add_argument("--clear-pending-setting-sync", action="store_true", help="清空待同步设定变更")
    governance_parser.set_defaults(handler=handle_governance)

    preflight_parser = subparsers.add_parser("preflight", help="续写/开写前的硬门槛校验")
    preflight_parser.add_argument("project_path", help="项目根目录")
    preflight_parser.set_defaults(handler=handle_preflight)

    start_parser = subparsers.add_parser("start", help="将目标章节标记为进行中")
    add_progress_arguments(start_parser)
    start_parser.set_defaults(handler=handle_start)

    check_parser = subparsers.add_parser("check", help="汇总检查单章")
    check_parser.add_argument("chapter_path", help="章节文件路径")
    check_parser.set_defaults(handler=handle_check)

    lint_parser = subparsers.add_parser("lint", help="按规则检查单章")
    lint_parser.add_argument("chapter_path", help="章节文件路径")
    lint_parser.add_argument("--rule-set", default="novel-lint", help="规则集目录名，默认 novel-lint")
    lint_parser.add_argument("--json", action="store_true", help="输出 JSON")
    lint_parser.set_defaults(handler=handle_lint)

    dialogue_parser = subparsers.add_parser("dialogue-pass", help="对白专审")
    dialogue_parser.add_argument("chapter_path", help="章节文件路径")
    dialogue_parser.add_argument("--rule-set", default="novel-lint", help="规则集目录名，默认 novel-lint")
    dialogue_parser.add_argument("--json", action="store_true", help="输出 JSON")
    dialogue_parser.set_defaults(handler=handle_dialogue_pass)

    finish_parser = subparsers.add_parser("finish", help="检查并同步章节完成状态")
    add_progress_arguments(finish_parser)
    finish_parser.add_argument("chapter_path", help="章节文件路径")
    finish_parser.add_argument("--summary", help="本章摘要")
    finish_parser.add_argument("--word-count", type=int, help="手动指定章节字数")
    finish_parser.add_argument("--skip-checks", action="store_true", help="跳过写后检查")
    finish_parser.set_defaults(handler=handle_finish)

    audit_parser = subparsers.add_parser("audit", help="阶段/卷审计")
    audit_parser.add_argument("project_path", help="项目根目录")
    audit_parser.add_argument("--scope", choices=("stage", "volume"), default="stage", help="审计范围")
    audit_parser.set_defaults(handler=handle_audit)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
