#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build local webnovel pattern reference assets."""

from __future__ import annotations

import argparse
import json

try:
    from corpus_index import build_corpus_assets
except ModuleNotFoundError:
    from scripts.corpus_index import build_corpus_assets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建本地范本检索资产。")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stats = build_corpus_assets()
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    print("本地范本资产已构建")
    print(f"- 文章数: {stats['articles']}")
    print(f"- 摘录数: {stats['excerpts']}")
    print(f"- 类型: {' / '.join(stats['types'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

