#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search generated local pattern references by tag, type, and keyword."""

from __future__ import annotations

import argparse

try:
    from corpus_index import SUGGESTED_KEYWORDS, available_tags, available_types, search_corpus_examples
except ModuleNotFoundError:
    from scripts.corpus_index import SUGGESTED_KEYWORDS, available_tags, available_types, search_corpus_examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检索本地网文范本索引。")
    parser.add_argument("--tag", help="按标签检索，例如：真假千金 / 危机压身 / 校园")
    parser.add_argument("--type", help="按摘录类型检索，例如：开头钩子 / 高张力对白")
    parser.add_argument("--keyword", help="按关键词模糊检索")
    parser.add_argument("--limit", type=int, default=10, help="最多返回多少条，默认 10")
    parser.add_argument("--list-tags", action="store_true", help="列出当前可用标签")
    parser.add_argument("--list-types", action="store_true", help="列出当前可用摘录类型")
    parser.add_argument("--list-keyword-examples", action="store_true", help="列出建议关键词示例")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_tags:
        print("可用标签：")
        for tag in available_tags():
            print(f"- {tag}")
        return 0

    if args.list_types:
        print("可用摘录类型：")
        for item in available_types():
            print(f"- {item}")
        return 0

    if args.list_keyword_examples:
        print("推荐关键词示例：")
        for keyword in SUGGESTED_KEYWORDS:
            print(f"- {keyword}")
        return 0

    results = search_corpus_examples(
        tag=args.tag,
        excerpt_type=args.type,
        keyword=args.keyword,
        limit=args.limit,
    )

    if not results:
        print("未命中本地范本。")
        print("建议：先用 `--list-tags` 看覆盖范围，或补充样本后执行 `python3 scripts/build_corpus_assets.py`。")
        return 0

    for row in results:
        if row["kind"] == "article":
            print(f"[ARTICLE] {row['article_id']} 《{row['title']}》")
            print(f"标签: {row['tags']}")
            print(f"路径: {row['file_path']}")
            print(f"摘要: {row['summary_le_200']}")
            print(f"迁移提醒: {row['notes'] or '无'}")
            print()
            continue

        print(f"[EXCERPT] {row['excerpt_id']} 《{row['title']}》")
        print(f"类型: {row['excerpt_type']}")
        print(f"标签: {row['tags']}")
        print(f"路径: {row['file_path']}")
        print(f"迁移提醒: {row['notes'] or '无'}")
        print(row["text"])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

