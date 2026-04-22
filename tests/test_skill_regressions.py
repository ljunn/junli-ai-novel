from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


class SkillRegressionTests(unittest.TestCase):
    def test_quick_start_next_chapter_works_on_fresh_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="junli-novel-test-") as tmpdir:
            tmp_path = Path(tmpdir)
            init_result = run_cli("scripts/chapter_pipeline.py", "init", "测试小说", "--target-dir", str(tmp_path))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            project_dir = tmp_path / "测试小说"
            next_result = run_cli(
                "scripts/chapter_pipeline.py",
                "next-chapter",
                str(project_dir),
                "--chapter-title",
                "第一章",
            )
            self.assertEqual(next_result.returncode, 0, next_result.stdout + next_result.stderr)
            self.assertTrue((project_dir / "runtime" / "chapter-0001.intent.md").exists())

    def test_next_chapter_applies_runtime_overrides_before_preflight_and_plan(self) -> None:
        with tempfile.TemporaryDirectory(prefix="junli-novel-test-") as tmpdir:
            tmp_path = Path(tmpdir)
            init_result = run_cli("scripts/chapter_pipeline.py", "init", "覆盖测试", "--target-dir", str(tmp_path))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            project_dir = tmp_path / "覆盖测试"
            task_log_path = project_dir / "task_log.md"
            text = task_log_path.read_text(encoding="utf-8")
            text = text.replace("当前卷：第一卷", "当前卷：未开始")
            text = text.replace("当前阶段：阶段1", "当前阶段：未开始")
            text = text.replace("当前阶段目标：立住主线、主角处境与核心卖点", "当前阶段目标：未记录")
            text = text.replace("下一章目标：立住开篇钩子、主角困境与核心异常", "下一章目标：")
            task_log_path.write_text(text, encoding="utf-8")

            next_result = run_cli(
                "scripts/chapter_pipeline.py",
                "next-chapter",
                str(project_dir),
                "--chapter-title",
                "雨夜开局",
                "--next-goal",
                "主角在雨夜逃出生天并埋下身份疑云",
                "--current-volume",
                "第一卷",
                "--current-phase",
                "阶段1",
                "--phase-goal",
                "立住主角困境与主卖点",
            )
            self.assertEqual(next_result.returncode, 0, next_result.stdout + next_result.stderr)

            intent_text = (project_dir / "runtime" / "chapter-0001.intent.md").read_text(encoding="utf-8")
            self.assertIn("当前卷：第一卷", intent_text)
            self.assertIn("当前阶段：阶段1", intent_text)
            self.assertIn("当前阶段目标：立住主角困境与主卖点", intent_text)
            self.assertIn("coze-mcp-", intent_text)

    def test_next_chapter_json_output_is_pure_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="junli-novel-test-") as tmpdir:
            tmp_path = Path(tmpdir)
            init_result = run_cli("scripts/chapter_pipeline.py", "init", "JSON纯净", "--target-dir", str(tmp_path))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            project_dir = tmp_path / "JSON纯净"
            result = run_cli(
                "scripts/chapter_pipeline.py",
                "next-chapter",
                str(project_dir),
                "--chapter-title",
                "第一章",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["chapter"], 1)
            self.assertTrue(payload["started"])
            self.assertNotIn("项目恢复摘要", result.stdout)

    def test_marketing_gate_warns_on_placeholder_brief(self) -> None:
        with tempfile.TemporaryDirectory(prefix="junli-novel-test-") as tmpdir:
            tmp_path = Path(tmpdir)
            init_result = run_cli("scripts/chapter_pipeline.py", "init", "营销测试", "--target-dir", str(tmp_path))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            project_dir = tmp_path / "营销测试"
            brief_path = project_dir / "runtime" / "marketing-brief.md"
            marketing_result = run_cli(
                "scripts/chapter_pipeline.py",
                "marketing",
                str(project_dir),
                "--platform",
                "起点中文网",
                "--output-file",
                str(brief_path),
            )
            self.assertEqual(marketing_result.returncode, 0, marketing_result.stdout + marketing_result.stderr)

            gate_result = run_cli(
                "scripts/chapter_pipeline.py",
                "platform-gate",
                str(brief_path),
                "--platform",
                "起点中文网",
                "--kind",
                "marketing",
            )
            self.assertEqual(gate_result.returncode, 1, gate_result.stdout + gate_result.stderr)
            self.assertIn("Verdict: warn", gate_result.stdout)

    def test_review_rejects_non_chapter_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="junli-novel-test-") as tmpdir:
            tmp_path = Path(tmpdir)
            init_result = run_cli("scripts/chapter_pipeline.py", "init", "审稿校验", "--target-dir", str(tmp_path))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            project_dir = tmp_path / "审稿校验"
            result = run_cli(
                "scripts/chapter_pipeline.py",
                "review",
                str(project_dir / "docs" / "作者意图.md"),
                "--json",
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("只支持章节文件", "\n".join(payload["failures"]))
            self.assertFalse((project_dir / "审阅意见").exists())

    def test_corpus_keyword_extraction_skips_fragment_noise(self) -> None:
        sys.path.insert(0, str(REPO_ROOT))
        try:
            from scripts.corpus_index import extract_query_keywords
        finally:
            sys.path.pop(0)

        keywords = extract_query_keywords(["雨夜开局", "主角雨夜逃命，立住危机和身份疑云"])
        self.assertIn("雨夜开局", keywords)
        self.assertIn("主角雨夜逃命", keywords)
        self.assertNotIn("夜开局", keywords)
        self.assertNotIn("角雨夜逃", keywords)


if __name__ == "__main__":
    unittest.main()
