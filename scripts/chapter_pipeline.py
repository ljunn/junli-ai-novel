#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一的新建、恢复、开写、质检与完结入口。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from chapter_text import is_chapter_file
    from check_chapter_wordcount import check_chapter
    from check_emotion_curve import analyze_chapter_emotion_curve
    from extract_thrills import analyze_thrills_and_poisons
    from new_project import create_novel_project
    from update_progress import STATUS_DONE, STATUS_IN_PROGRESS, update_progress
except ModuleNotFoundError:
    from scripts.chapter_text import is_chapter_file
    from scripts.check_chapter_wordcount import check_chapter
    from scripts.check_emotion_curve import analyze_chapter_emotion_curve
    from scripts.extract_thrills import analyze_thrills_and_poisons
    from scripts.new_project import create_novel_project
    from scripts.update_progress import STATUS_DONE, STATUS_IN_PROGRESS, update_progress


REQUIRED_MEMORY_FILES = (
    "task_log.md",
    "docs/大纲.md",
    "plot/伏笔记录.md",
    "plot/时间线.md",
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


def collect_missing_memory_files(project_dir: Path) -> list[str]:
    return [relative for relative in REQUIRED_MEMORY_FILES if not (project_dir / relative).exists()]


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
        "viewpoint": extract_state_field(task_log, "当前视角：", "未记录"),
        "protagonist_location": extract_state_field(task_log, "主角位置：", "未记录"),
        "protagonist_state": extract_state_field(task_log, "主角状态：", "未记录"),
        "next_goal": extract_state_field(task_log, "下一章目标：", "未记录"),
        "recent_summaries": recent_summaries[:3],
        "active_plots": active_plots[:6],
        "recent_chapter_files": [str(path) for path in recent_chapter_files],
    }


def print_resume_summary(summary: dict) -> None:
    print("\n" + "=" * 60)
    print("项目恢复摘要")
    print("=" * 60)
    print(f"项目目录: {summary['project_dir']}")
    print(f"创作阶段: {summary['stage']}")
    print(f"最新章节: {summary['latest_chapter']}")
    print(f"当前处理章节: {summary['current_chapter']}")
    print(f"当前视角: {summary['viewpoint']}")
    print(f"主角位置: {summary['protagonist_location']}")
    print(f"主角状态: {summary['protagonist_state']}")
    print(f"下一章目标: {summary['next_goal']}")

    if summary["missing_files"]:
        print("\n缺失记忆文件:")
        for item in summary["missing_files"]:
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


def build_check_report(chapter_path: Path) -> dict:
    return {
        "wordcount": check_chapter(str(chapter_path)),
        "emotion": analyze_chapter_emotion_curve(str(chapter_path)),
        "thrills": analyze_thrills_and_poisons(str(chapter_path)),
    }


def print_check_summary(report: dict) -> None:
    wordcount = report["wordcount"]
    emotion = report["emotion"]
    thrills = report["thrills"]

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
    parser.add_argument("--plot-note", help="新增伏笔备注")


def handle_init(args: argparse.Namespace) -> int:
    create_novel_project(
        args.project_name,
        target_dir=args.target_dir,
        force=args.force,
        mode=args.mode,
        complex_relationships=args.complex_relationships,
        romance_focus=args.romance_focus,
    )
    return 0


def handle_resume(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_path).expanduser().resolve()
    print_resume_summary(summarize_project(project_dir))
    return 0


def handle_start(args: argparse.Namespace) -> int:
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
        status=STATUS_IN_PROGRESS,
    )
    return 0


def handle_check(args: argparse.Namespace) -> int:
    chapter_path = Path(args.chapter_path).expanduser().resolve()
    print_check_summary(build_check_report(chapter_path))
    return 0


def handle_finish(args: argparse.Namespace) -> int:
    chapter_path = Path(args.chapter_path).expanduser().resolve()
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
        plot_note=args.plot_note,
        status=STATUS_DONE,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="小说项目统一工作流入口")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化小说项目")
    init_parser.add_argument("project_name", help="项目名称")
    init_parser.add_argument("--target-dir", help="项目创建目录，默认当前目录")
    init_parser.add_argument("--mode", choices=("single", "dual", "ensemble"), default="single")
    init_parser.add_argument("--complex-relationships", action="store_true", help="创建关系图模板")
    init_parser.add_argument("--romance-focus", action="store_true", help="感情线重要时创建关系图模板")
    init_parser.add_argument("--force", action="store_true", help="覆盖已存在模板")
    init_parser.set_defaults(handler=handle_init)

    resume_parser = subparsers.add_parser("resume", help="恢复项目摘要")
    resume_parser.add_argument("project_path", help="项目根目录")
    resume_parser.set_defaults(handler=handle_resume)

    start_parser = subparsers.add_parser("start", help="将目标章节标记为进行中")
    add_progress_arguments(start_parser)
    start_parser.set_defaults(handler=handle_start)

    check_parser = subparsers.add_parser("check", help="汇总检查单章")
    check_parser.add_argument("chapter_path", help="章节文件路径")
    check_parser.set_defaults(handler=handle_check)

    finish_parser = subparsers.add_parser("finish", help="检查并同步章节完成状态")
    add_progress_arguments(finish_parser)
    finish_parser.add_argument("chapter_path", help="章节文件路径")
    finish_parser.add_argument("--summary", help="本章摘要")
    finish_parser.add_argument("--word-count", type=int, help="手动指定章节字数")
    finish_parser.add_argument("--skip-checks", action="store_true", help="跳过写后检查")
    finish_parser.set_defaults(handler=handle_finish)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
