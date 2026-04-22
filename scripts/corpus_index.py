#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build and search local pattern references for webnovel drafting."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


ROOT_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT_DIR / "corpus"
ARTICLES_DIR = CORPUS_DIR / "articles"
ANALYSIS_DIR = CORPUS_DIR / "analysis"
ARTICLE_PROFILES_CSV = ANALYSIS_DIR / "article_profiles.csv"
EXCERPTS_CSV = ANALYSIS_DIR / "excerpts.csv"
IMITATION_INDEX_MD = ANALYSIS_DIR / "imitation_index.md"
STATS_JSON = ANALYSIS_DIR / "stats.json"

EXCERPT_TYPES = ("开头钩子", "主角亮相", "高张力对白", "结尾余韵")
NOTE_SECTIONS = ("迁移提醒", "借鉴点", "适用场景")

KEYWORD_TAGS: list[tuple[str, list[str]]] = [
    ("真假千金", [r"真千金", r"假千金", r"认亲"]),
    ("都市婚恋", [r"离婚", r"退婚", r"前夫", r"联姻", r"未婚夫", r"总裁", r"豪门"]),
    ("古言/宫廷", [r"侯府", r"王府", r"宫", r"和离", r"太子", r"将军", r"圣旨"]),
    ("校园", [r"校园", r"学校", r"大学", r"班主任", r"社团", r"学神", r"教室"]),
    ("仙侠/修仙", [r"修仙", r"宗门", r"灵根", r"飞升", r"仙门", r"剑修", r"灵气"]),
    ("系统/外挂", [r"系统", r"面板", r"提示", r"外挂", r"寿命", r"弹幕", r"任务"]),
    ("危机压身", [r"献祭", r"追杀", r"灭口", r"债", r"血契", r"威胁", r"抄家", r"牢里"]),
    ("身份反差", [r"穿成", r"重生", r"冒名", r"失忆", r"真假", r"马甲", r"身份"]),
    ("重逢修罗场", [r"重逢", r"旧爱", r"前任", r"再见", r"多年后", r"回国"]),
    ("甜虐关系", [r"喜欢", r"爱", r"心动", r"告白", r"失望", r"冷战", r"婚约"]),
]

STRUCTURAL_TAG_RULES: list[tuple[str, list[str]]] = [
    ("关系破裂", [r"退婚", r"分手", r"离婚", r"断绝", r"翻脸"]),
    ("情感拉扯", [r"喜欢", r"不敢", r"心软", r"试探", r"对视", r"拥抱"]),
    ("轻喜反差", [r"笑", r"忍不住", r"反差", r"嘴硬", r"装", r"憋"]),
    ("信息外挂", [r"系统", r"弹幕", r"面板", r"提示", r"寿命", r"听见心声"]),
    ("危机感", [r"危险", r"威胁", r"追来", r"炸", r"死", r"血", r"抄家", r"抓"]),
]

SUGGESTED_KEYWORDS = [
    "真假千金",
    "退婚",
    "联姻",
    "校园重逢",
    "修仙",
    "宗门",
    "系统",
    "寿命",
    "危机",
    "章末钩子",
]

GENERIC_STOPWORDS = {
    "本章",
    "当前",
    "阶段",
    "目标",
    "问题",
    "推进",
    "主线",
    "章节",
    "最近",
    "必须",
    "不要",
    "还有",
    "已经",
    "就是",
    "然后",
    "因为",
    "所以",
    "什么",
    "如何",
    "这个",
    "那个",
    "一下",
    "一下子",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u3000", " ").replace("\xa0", " ")).strip()


def split_tags(raw: str) -> list[str]:
    normalized = raw.replace("｜", "|").replace("，", "|").replace("、", "|")
    tags: list[str] = []
    seen: set[str] = set()
    for item in normalized.split("|"):
        tag = item.strip()
        if tag and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return tags


def trim_to_limit(text: str, limit: int = 180) -> str:
    compact = normalize_text(text)
    if len(compact) <= limit:
        return compact

    sentences = re.split(r"(?<=[。！？!?])", compact)
    result = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(result) + len(sentence) > limit:
            break
        result += sentence
    if result and len(result) >= 60:
        return result
    return compact[:limit].rstrip("，,、；; ") + "……"


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def clean_block(lines: Iterable[str]) -> str:
    return "\n".join(line.rstrip() for line in lines).strip()


def clean_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_text(raw_line)
        if not line or line.startswith("#"):
            continue
        paragraphs.append(line)
    return paragraphs


def detect_tags(text: str) -> list[str]:
    tags: list[str] = []
    for tag, patterns in KEYWORD_TAGS:
        if any(re.search(pattern, text) for pattern in patterns):
            tags.append(tag)
    if not tags:
        tags.append("其他")
    return tags


def detect_structural_tags(text: str) -> list[str]:
    tags: list[str] = []
    for tag, patterns in STRUCTURAL_TAG_RULES:
        if any(re.search(pattern, text) for pattern in patterns):
            tags.append(tag)
    return tags


def dedupe(items: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)
    return ordered


def parse_markdown_article(path: Path) -> dict[str, str | list[str] | dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    title = ""
    preamble: list[str] = []
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()
            sections[current_section] = []
            continue
        if current_section is None:
            preamble.append(raw_line)
        else:
            sections[current_section].append(raw_line)

    metadata: dict[str, str] = {}
    remaining_preamble: list[str] = []
    for raw_line in preamble:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not title:
            title = stripped.lstrip("#").strip()
            continue
        if stripped.startswith("标签：") or stripped.startswith("标签:"):
            metadata["tags"] = stripped.split("：", 1)[-1].split(":", 1)[-1].strip()
            continue
        if stripped.startswith("摘要：") or stripped.startswith("摘要:"):
            metadata["summary"] = stripped.split("：", 1)[-1].split(":", 1)[-1].strip()
            continue
        remaining_preamble.append(stripped)

    title = title or path.stem
    rendered_sections = {name: clean_block(lines) for name, lines in sections.items()}

    body_text = rendered_sections.get("正文", "")
    if not body_text:
        body_chunks = [rendered_sections.get(name, "") for name in EXCERPT_TYPES if rendered_sections.get(name, "")]
        body_text = "\n\n".join(chunk for chunk in body_chunks if chunk)
    if not body_text and remaining_preamble:
        body_text = "\n".join(remaining_preamble)

    notes = ""
    for section_name in NOTE_SECTIONS:
        notes = rendered_sections.get(section_name, "")
        if notes:
            break

    full_text = "\n".join([title, metadata.get("summary", ""), body_text, notes])
    tags = split_tags(metadata.get("tags", "")) or detect_tags(full_text)
    summary = metadata.get("summary") or trim_to_limit(body_text or notes or title)

    return {
        "title": title,
        "summary": summary,
        "tags": tags,
        "body_text": body_text,
        "notes": notes,
        "sections": rendered_sections,
    }


def derive_article_id(index: int, path: Path) -> str:
    match = re.match(r"^(A\d+|\d{3,4})[-_]", path.stem)
    if match:
        token = match.group(1)
        if token.startswith("A"):
            return token
        return f"A{int(token):03d}"
    return f"A{index:03d}"


def score_dialogue(line: str) -> int:
    score = 0
    if "“" in line or "\"" in line:
        score += 2
    if re.search(r"[！？!?]", line):
        score += 2
    if re.search(r"滚|退婚|嫁|离|杀|敢|疯|别碰|闭嘴|求你|威胁", line):
        score += 2
    if 10 <= len(line) <= 120:
        score += 1
    return score


def fallback_opening(paragraphs: list[str]) -> str:
    return "\n".join(paragraphs[: min(3, len(paragraphs))]).strip()


def fallback_intro(paragraphs: list[str]) -> str:
    for paragraph in paragraphs[:12]:
        if re.match(r"^(我|他|她|少年|少女|主角|那天|回家那天|重生后|被押上来时)", paragraph):
            return paragraph
    return paragraphs[0] if paragraphs else ""


def fallback_dialogue(paragraphs: list[str]) -> str:
    best_line = ""
    best_score = 0
    for paragraph in paragraphs[:24]:
        score = score_dialogue(paragraph)
        if score > best_score:
            best_line = paragraph
            best_score = score
    return best_line if best_score >= 3 else ""


def fallback_ending(paragraphs: list[str]) -> str:
    return "\n".join(paragraphs[-2:]).strip()


def build_excerpt_text(article: dict[str, str | list[str] | dict[str, str]], excerpt_type: str) -> str:
    sections = article["sections"]
    assert isinstance(sections, dict)
    explicit = normalize_text(str(sections.get(excerpt_type, "")))
    if explicit:
        return explicit

    body_text = str(article.get("body_text", ""))
    paragraphs = clean_paragraphs(body_text)
    if not paragraphs:
        return ""

    if excerpt_type == "开头钩子":
        return fallback_opening(paragraphs)
    if excerpt_type == "主角亮相":
        return fallback_intro(paragraphs)
    if excerpt_type == "高张力对白":
        return fallback_dialogue(paragraphs)
    if excerpt_type == "结尾余韵":
        return fallback_ending(paragraphs)
    return ""


def write_csv(path: Path, headers: Sequence[str], rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_index_markdown(article_rows: Sequence[dict[str, str]], excerpt_rows: Sequence[dict[str, str]]) -> None:
    lines = [
        "# Local Pattern Reference Index",
        "",
        f"- 文章数：{len(article_rows)}",
        f"- 摘录数：{len(excerpt_rows)}",
        f"- 摘录类型：{' / '.join(EXCERPT_TYPES)}",
        "",
        "## Articles",
        "",
    ]
    for row in article_rows:
        lines.extend(
            [
                f"### {row['article_id']} 《{row['title']}》",
                f"- 标签：{row['tags']}",
                f"- 路径：{row['file_path']}",
                f"- 摘要：{row['summary_le_200']}",
                f"- 迁移提醒：{row['notes'] or '无'}",
                "",
            ]
        )

    lines.append("## Excerpts")
    lines.append("")
    for row in excerpt_rows:
        lines.extend(
            [
                f"### {row['excerpt_id']}",
                f"- 标题：《{row['title']}》",
                f"- 类型：{row['excerpt_type']}",
                f"- 标签：{row['tags']}",
                f"- 迁移提醒：{row['notes'] or '无'}",
                "",
                row["text"],
                "",
            ]
        )

    IMITATION_INDEX_MD.write_text("\n".join(lines), encoding="utf-8")


def build_corpus_assets() -> dict[str, object]:
    article_rows: list[dict[str, str]] = []
    excerpt_rows: list[dict[str, str]] = []

    article_paths = sorted([path for path in ARTICLES_DIR.glob("*") if path.suffix.lower() in {".md", ".txt"}])
    for index, path in enumerate(article_paths, start=1):
        article = parse_markdown_article(path)
        article_id = derive_article_id(index, path)
        title = str(article["title"])
        summary = str(article["summary"])
        tags = dedupe(article["tags"])
        notes = trim_to_limit(str(article["notes"]), limit=140) if str(article["notes"]) else ""

        article_rows.append(
            {
                "article_id": article_id,
                "title": title,
                "file_path": str(path.relative_to(ROOT_DIR)),
                "summary_le_200": summary,
                "tags": "|".join(tags),
                "notes": notes,
            }
        )

        for excerpt_type in EXCERPT_TYPES:
            excerpt_text = build_excerpt_text(article, excerpt_type)
            if not excerpt_text:
                continue
            excerpt_tags = dedupe([*tags, excerpt_type, *detect_structural_tags(excerpt_text)])
            excerpt_rows.append(
                {
                    "excerpt_id": f"{article_id}-{excerpt_type}",
                    "article_id": article_id,
                    "title": title,
                    "file_path": str(path.relative_to(ROOT_DIR)),
                    "excerpt_type": excerpt_type,
                    "tags": "|".join(excerpt_tags),
                    "text": excerpt_text,
                    "notes": notes,
                }
            )

    write_csv(
        ARTICLE_PROFILES_CSV,
        ("article_id", "title", "file_path", "summary_le_200", "tags", "notes"),
        article_rows,
    )
    write_csv(
        EXCERPTS_CSV,
        ("excerpt_id", "article_id", "title", "file_path", "excerpt_type", "tags", "text", "notes"),
        excerpt_rows,
    )
    write_index_markdown(article_rows, excerpt_rows)

    stats = {
        "articles": len(article_rows),
        "excerpts": len(excerpt_rows),
        "types": list(EXCERPT_TYPES),
        "tags": sorted({tag for row in article_rows for tag in split_tags(row["tags"])}),
    }
    STATS_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def collect_tags(rows: Sequence[dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        for tag in split_tags(row.get("tags", "")):
            counter[tag] += 1
    return counter


def available_tags() -> list[str]:
    merged: Counter[str] = Counter()
    merged.update(collect_tags(load_csv_rows(ARTICLE_PROFILES_CSV)))
    merged.update(collect_tags(load_csv_rows(EXCERPTS_CSV)))
    return [tag for tag, _count in sorted(merged.items(), key=lambda item: (-item[1], item[0]))]


def available_types() -> list[str]:
    rows = load_csv_rows(EXCERPTS_CSV)
    counter = Counter(row["excerpt_type"] for row in rows)
    return [item for item, _count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))]


def matches_tag(value: str, target: str | None) -> bool:
    if not target:
        return True
    return target in split_tags(value)


def search_corpus_examples(
    *,
    tag: str | None = None,
    excerpt_type: str | None = None,
    keyword: str | None = None,
    limit: int = 10,
) -> list[dict[str, str]]:
    profiles = load_csv_rows(ARTICLE_PROFILES_CSV)
    excerpts = load_csv_rows(EXCERPTS_CSV)
    results: list[dict[str, str]] = []

    if excerpt_type is None:
        for row in profiles:
            haystack = "\n".join([row["title"], row["summary_le_200"], row["tags"], row["notes"]])
            if not matches_tag(row.get("tags", ""), tag):
                continue
            if keyword and keyword not in haystack:
                continue
            results.append({"kind": "article", **row})

    for row in excerpts:
        haystack = "\n".join([row["title"], row["tags"], row["text"], row["notes"], row["excerpt_type"]])
        if not matches_tag(row.get("tags", ""), tag):
            continue
        if excerpt_type and row["excerpt_type"] != excerpt_type:
            continue
        if keyword and keyword not in haystack:
            continue
        results.append({"kind": "excerpt", **row})

    return results[:limit]


def extract_query_keywords(query_texts: Sequence[str], limit: int = 10) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(piece: str) -> bool:
        normalized_piece = piece.strip()
        if not normalized_piece:
            return False
        if len(normalized_piece) < 2 or len(normalized_piece) > 18:
            return False
        if normalized_piece in GENERIC_STOPWORDS or normalized_piece.isdigit() or normalized_piece in seen:
            return False
        candidates.append(normalized_piece)
        seen.add(normalized_piece)
        return len(candidates) >= limit

    for raw_text in query_texts:
        normalized = normalize_text(raw_text)
        if not normalized:
            continue
        if add(normalized):
            return candidates
        pieces = re.split(r"[\s,，。；;、:：/|（）()《》【】\[\]“”\"'!?！？]+", normalized)
        for piece in pieces:
            if add(piece):
                return candidates
    return candidates[:limit]


def infer_preferred_excerpt_types(query_texts: Sequence[str]) -> list[str]:
    joined = "\n".join(query_texts)
    preferred: list[str] = []
    if any(token in joined for token in ("开头", "入场", "起势", "前三段", "承接")):
        preferred.append("开头钩子")
    if any(token in joined for token in ("对白", "对话", "拉扯", "摊牌", "退婚", "争执")):
        preferred.append("高张力对白")
    if any(token in joined for token in ("章末", "结尾", "钩子", "下章", "余波", "收尾")):
        preferred.append("结尾余韵")
    if any(token in joined for token in ("亮相", "出场", "人设")):
        preferred.append("主角亮相")

    for excerpt_type in EXCERPT_TYPES:
        if excerpt_type not in preferred:
            preferred.append(excerpt_type)
    return preferred


def select_corpus_examples(
    query_texts: Sequence[str],
    *,
    preferred_types: Sequence[str] | None = None,
    limit: int = 4,
) -> dict[str, object]:
    excerpts = load_csv_rows(EXCERPTS_CSV)
    keywords = extract_query_keywords(query_texts)
    preferred = list(preferred_types or infer_preferred_excerpt_types(query_texts))

    scored: list[dict[str, object]] = []
    for row in excerpts:
        haystack = "\n".join([row["title"], row["tags"], row["text"], row["notes"], row["excerpt_type"]])
        matched_keywords = [keyword for keyword in keywords if keyword in haystack]
        if keywords and not matched_keywords:
            continue
        score = sum(min(len(keyword), 6) for keyword in matched_keywords)
        if row["excerpt_type"] in preferred:
            score += max(1, len(preferred) - preferred.index(row["excerpt_type"]))
        scored.append({**row, "matched_keywords": matched_keywords, "score": score})

    scored.sort(
        key=lambda item: (
            int(item["score"]),
            -preferred.index(str(item["excerpt_type"])) if str(item["excerpt_type"]) in preferred else 0,
            str(item["title"]),
        ),
        reverse=True,
    )

    selected: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for excerpt_type in preferred:
        for item in scored:
            identity = (str(item["article_id"]), str(item["excerpt_type"]))
            if identity in seen or str(item["excerpt_type"]) != excerpt_type:
                continue
            selected.append(item)
            seen.add(identity)
            break
        if len(selected) >= limit:
            break

    for item in scored:
        if len(selected) >= limit:
            break
        identity = (str(item["article_id"]), str(item["excerpt_type"]))
        if identity in seen:
            continue
        selected.append(item)
        seen.add(identity)

    return {
        "keywords": keywords,
        "preferred_types": preferred,
        "matches": selected[:limit],
        "analysis_dir": str(ANALYSIS_DIR),
    }


def render_reference_markdown(reference_bundle: dict[str, object]) -> str:
    keywords = reference_bundle.get("keywords", [])
    preferred_types = reference_bundle.get("preferred_types", [])
    matches = reference_bundle.get("matches", [])

    lines = [
        "# Local Pattern References",
        "",
        f"- 查询词：{' / '.join(str(item) for item in keywords) if keywords else '未生成'}",
        f"- 优先摘录类型：{' / '.join(str(item) for item in preferred_types) if preferred_types else '未设置'}",
        f"- 分析目录：{reference_bundle.get('analysis_dir', ANALYSIS_DIR)}",
        "",
    ]

    if not matches:
        lines.extend(
            [
                "## 命中结果",
                "- 当前本地范本库没有命中。",
                "- 可先运行 `python3 scripts/search_corpus_examples.py --list-tags` 查看现有覆盖。",
                "- 新增样本后执行 `python3 scripts/build_corpus_assets.py` 重建索引。",
                "",
            ]
        )
        return "\n".join(lines)

    for index, match in enumerate(matches, start=1):
        matched_keywords = match.get("matched_keywords", [])
        lines.extend(
            [
                f"## {index}. 《{match['title']}》 / {match['excerpt_type']}",
                f"- 标签：{match['tags']}",
                f"- 命中词：{' / '.join(str(item) for item in matched_keywords) if matched_keywords else '默认命中'}",
                f"- 来源：{match['file_path']}",
                f"- 迁移提醒：{match['notes'] or '重点看冲突起势、信息投放和收尾位置。'}",
                "",
                str(match["text"]),
                "",
            ]
        )
    return "\n".join(lines)
