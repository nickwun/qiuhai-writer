#!/usr/bin/env python3
"""
Discover running-topic material candidates for Xiaohongshu knowledge posts.

The script intentionally avoids paid search APIs. It combines:
- DuckDuckGo HTML search for web, YouTube, forums, and site-specific queries
- Reddit public JSON search endpoints

Outputs Markdown, CSV, and JSON reports under running-materials/.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


DEFAULT_KEYWORDS = [
    "running zone 2 training",
    "zone 2 running beginners",
    "low heart rate running",
    "MAF running training",
    "marathon training aerobic base",
    "5K 10K running training",
    "half marathon training threshold",
    "easy run heart rate",
    "lactate threshold running",
    "VO2max running intervals",
]

YOUTUBE_CREATOR_QUERIES = [
    # User-followed sources.
    "Floris Gierman running training",
    "The Extramilest Show running training",
    "Floris Gierman zone 2 low heart rate running",
    "Nicklas Rossner running training",
    "Nicklas Rossner marathon training",
    "豹大王 run 跑步 训练",
    "豹大王 run 马拉松 训练",
    # Similar running creators/channels with training-oriented content.
    "The Running Channel running training",
    "Ben Parkes marathon training",
    "Ben is Running marathon training",
    "Stephen Scullion marathon training",
    "Sage Running VO2maxProductions running training",
    "The Run Experience running form training",
    "Strength Running Jason Fitzgerald running training",
    "Steve Magness running training",
    "Kofuzi marathon training",
    "Phily Bowden running training",
    "James Dunne running technique",
    "Sweat Elite running training",
]

PREFERRED_YOUTUBE_CHANNEL_TERMS = {
    "floris gierman": "Floris Gierman",
    "extramilest": "The Extramilest Show",
    "nicklas rossner": "Nicklas Rossner",
    "豹大王": "豹大王 run",
    "the running channel": "The Running Channel",
    "ben parkes": "Ben Parkes",
    "ben is running": "Ben is Running",
    "stephen scullion": "Stephen Scullion",
    "sage running": "Sage Running",
    "vo2maxproductions": "VO2maxProductions / Sage Running",
    "the run experience": "The Run Experience",
    "strength running": "Strength Running",
    "jason fitzgerald": "Strength Running / Jason Fitzgerald",
    "steve magness": "Steve Magness",
    "kofuzi": "Kofuzi",
    "phily bowden": "Phily Bowden",
    "james dunne": "James Dunne",
    "sweat elite": "Sweat Elite",
}

SITE_QUERIES = [
    "site:reddit.com/r/running",
    "site:reddit.com/r/AdvancedRunning",
    "site:reddit.com/r/Marathon_Training",
    "site:youtube.com/watch",
    "site:scienceofrunning.com running",
    "site:trainingpeaks.com running",
    "site:strengthrunning.com running",
    "site:themorningshakeout.com running",
    "site:marathonhandbook.com running",
    "site:letsrun.com/forum running",
    "site:philmaffetone.com MAF running",
]

X_ACCOUNT_QUERIES = [
    "site:x.com/stevemagness",
    "site:twitter.com/stevemagness",
    "site:x.com/mariofraioli",
    "site:twitter.com/mariofraioli",
    "site:x.com/JDruns",
    "site:twitter.com/JDruns",
]

X_ACCOUNT_LABELS = {
    "stevemagness": "X @stevemagness",
    "mariofraioli": "X @mariofraioli",
    "jdruns": "X @JDruns",
}

REDDIT_SUBREDDITS = [
    "running",
    "AdvancedRunning",
    "Marathon_Training",
    "beginnerrunning",
    "trailrunning",
    "XXRunning",
]

GOOD_TERMS = {
    "zone 2": 8,
    "zone2": 8,
    "low heart rate": 8,
    "maf": 8,
    "aerobic base": 7,
    "heart rate": 6,
    "marathon": 5,
    "half marathon": 5,
    "5k": 4,
    "10k": 4,
    "threshold": 6,
    "lactate": 6,
    "easy run": 5,
    "long run": 5,
    "vo2": 5,
    "interval": 4,
    "recovery": 4,
    "training zones": 5,
    "durability": 4,
}

BAD_TERMS = {
    "shoe": 6,
    "shoes": 6,
    "sale": 6,
    "discount": 5,
    "coupon": 5,
    "watch review": 4,
    "best treadmill": 5,
    "gear": 3,
    "injury lawyer": 10,
    "incontinence": 12,
    "product": 4,
}

TITLE_RELEVANCE_TERMS = [
    "zone",
    "heart rate",
    "low heart rate",
    "maf",
    "aerobic",
    "base",
    "threshold",
    "lactate",
    "tempo",
    "easy run",
    "long run",
    "marathon training",
    "half marathon",
    "5k",
    "10k",
    "vo2",
    "interval",
    "recovery",
    "fatigue",
    "mileage",
    "running volume",
    "pace",
    "endurance",
    "beginner",
]

SOURCE_LABELS = [
    ("reddit.com", "Reddit"),
    ("youtube.com", "YouTube"),
    ("youtu.be", "YouTube"),
    ("scienceofrunning.com", "Science of Running"),
    ("trainingpeaks.com", "TrainingPeaks"),
    ("runnersworld.com", "Runner's World"),
    ("strengthrunning.com", "Strength Running"),
    ("themorningshakeout.com", "The Morning Shakeout"),
    ("marathonhandbook.com", "Marathon Handbook"),
    ("letsrun.com", "LetsRun"),
    ("extramilest.com", "Extramilest"),
    ("philmaffetone.com", "MAF / Phil Maffetone"),
]


@dataclass
class Candidate:
    url: str
    title: str
    snippet: str = ""
    source: str = ""
    query: str = ""
    channel: str = ""
    created_utc: float | None = None
    score: int = 0
    topic_tags: list[str] = field(default_factory=list)
    chinese_title: str = ""
    chinese_summary: str = ""
    xhs_angle: str = ""
    recommendation: str = ""


class DDGParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_title = False
        self._in_snippet = False
        self._current_url = ""
        self._current_title: list[str] = []
        self._current_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k: v or "" for k, v in attrs}
        cls = attrs_dict.get("class", "")
        if tag == "a" and "result__a" in cls:
            self._flush()
            self._in_title = True
            self._current_url = attrs_dict.get("href", "")
            self._current_title = []
            self._current_snippet = []
        elif tag in {"a", "div"} and "result__snippet" in cls:
            self._in_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title:
            self._in_title = False
        elif tag in {"a", "div"} and self._in_snippet:
            self._in_snippet = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._current_title.append(data)
        elif self._in_snippet:
            self._current_snippet.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        title = clean_text(" ".join(self._current_title))
        if not title or not self._current_url:
            return
        url = normalize_duckduckgo_url(self._current_url)
        snippet = clean_text(" ".join(self._current_snippet))
        self.results.append({"title": title, "url": url, "snippet": snippet})
        self._current_url = ""
        self._current_title = []
        self._current_snippet = []


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_duckduckgo_url(url: str) -> str:
    url = html.unescape(url)
    if url.startswith("//duckduckgo.com/l/?") or url.startswith("https://duckduckgo.com/l/?"):
        parsed = urllib.parse.urlparse("https:" + url if url.startswith("//") else url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs:
            return qs["uddg"][0]
    return url


def request_text(url: str, *, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) qiuhai-material-research/1.0",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def ddg_search(query: str, max_results: int) -> list[Candidate]:
    params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
    url = f"https://duckduckgo.com/html/?{params}"
    try:
        body = request_text(url)
    except Exception as exc:
        print(f"[warn] DuckDuckGo failed for {query!r}: {exc}", file=sys.stderr)
        return []
    parser = DDGParser()
    parser.feed(body)
    parser.close()
    candidates: list[Candidate] = []
    for item in parser.results[:max_results]:
        candidates.append(
            Candidate(
                url=item["url"],
                title=item["title"],
                snippet=item["snippet"],
                source=source_label(item["url"]),
                query=query,
                channel="web-search",
            )
        )
    return candidates


def reddit_search(query: str, subreddits: Iterable[str], max_results: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    for subreddit in subreddits:
        params = urllib.parse.urlencode(
            {"q": query, "restrict_sr": "1", "sort": "relevance", "t": "year", "limit": max_results}
        )
        url = f"https://www.reddit.com/r/{subreddit}/search.json?{params}"
        try:
            raw = request_text(url)
            data = json.loads(raw)
        except Exception as exc:
            print(f"[warn] Reddit failed for r/{subreddit} {query!r}: {exc}", file=sys.stderr)
            continue
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            permalink = post.get("permalink") or ""
            if not permalink:
                continue
            snippet = clean_text(post.get("selftext", ""))
            if len(snippet) > 320:
                snippet = snippet[:317] + "..."
            candidates.append(
                Candidate(
                    url=f"https://www.reddit.com{permalink}",
                    title=clean_text(post.get("title", "")),
                    snippet=snippet,
                    source=f"Reddit r/{subreddit}",
                    query=query,
                    channel="reddit",
                    created_utc=post.get("created_utc"),
                )
            )
        time.sleep(0.3)
    return candidates


def youtube_search(query: str, max_results: int) -> list[Candidate]:
    params = urllib.parse.urlencode({"search_query": query})
    url = f"https://www.youtube.com/results?{params}"
    try:
        body = request_text(url, timeout=25)
    except Exception as exc:
        print(f"[warn] YouTube failed for {query!r}: {exc}", file=sys.stderr)
        return []

    candidates: list[Candidate] = []
    seen_video_ids: set[str] = set()
    marker = '"videoRenderer":'
    start = 0
    while len(candidates) < max_results:
        idx = body.find(marker, start)
        if idx < 0:
            break
        obj_start = body.find("{", idx + len(marker))
        if obj_start < 0:
            break
        obj_text, end = extract_json_object(body, obj_start)
        start = end
        if not obj_text:
            continue
        try:
            video = json.loads(obj_text)
        except json.JSONDecodeError:
            continue
        video_id = video.get("videoId")
        if not video_id or video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)
        title = youtube_text(video.get("title", {}))
        if not title:
            continue
        snippets = []
        for key in ("descriptionSnippet", "detailedMetadataSnippets"):
            value = video.get(key)
            if isinstance(value, list):
                snippets.extend(youtube_text(item.get("snippetText", {})) for item in value if isinstance(item, dict))
            else:
                snippets.append(youtube_text(value or {}))
        channel_name = youtube_text(video.get("ownerText", {}))
        snippet = clean_text(" ".join(x for x in snippets if x))
        if channel_name:
            snippet = clean_text(f"频道：{channel_name}。{snippet}")
        source = "YouTube"
        preferred_label = preferred_youtube_label(f"{channel_name} {title} {query}")
        if preferred_label:
            source = f"YouTube / {preferred_label}"
        candidates.append(
            Candidate(
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=title,
                snippet=snippet,
                source=source,
                query=query,
                channel="youtube",
            )
        )
    return candidates


def preferred_youtube_label(text: str) -> str:
    lower = text.lower()
    for term, label in PREFERRED_YOUTUBE_CHANNEL_TERMS.items():
        if term in lower:
            return label
    return ""


def extract_json_object(text: str, obj_start: int) -> tuple[str, int]:
    depth = 0
    in_string = False
    escaped = False
    for i in range(obj_start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[obj_start : i + 1], i + 1
    return "", obj_start + 1


def youtube_text(value: dict[str, object]) -> str:
    if not isinstance(value, dict):
        return ""
    if isinstance(value.get("simpleText"), str):
        return clean_text(str(value["simpleText"]))
    runs = value.get("runs")
    if isinstance(runs, list):
        return clean_text("".join(str(run.get("text", "")) for run in runs if isinstance(run, dict)))
    return ""


def source_label(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if host in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
        handle = parsed.path.strip("/").split("/", 1)[0].lower()
        if handle in X_ACCOUNT_LABELS:
            return X_ACCOUNT_LABELS[handle]
        if handle:
            return f"X @{handle}"
    for needle, label in SOURCE_LABELS:
        if needle in host:
            return label
    return host.replace("www.", "") or "Web"


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/")
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    keep = []
    for key, value in query:
        if key.lower().startswith("utm_") or key.lower() in {"fbclid", "gclid"}:
            continue
        keep.append((key, value))
    return urllib.parse.urlunparse((parsed.scheme, host, path, "", urllib.parse.urlencode(keep), ""))


def tag_topics(text: str) -> list[str]:
    lower = text.lower()
    tags = []
    mapping = [
        ("Zone 2", ["zone 2", "zone2", "aerobic base", "easy run"]),
        ("低心率/MAF", ["low heart rate", "maf", "maffetone"]),
        ("马拉松", ["marathon", "half marathon", "long run"]),
        ("5K/10K", ["5k", "10k"]),
        ("阈值/乳酸", ["threshold", "lactate", "tempo"]),
        ("VO2max/间歇", ["vo2", "interval", "sprint"]),
        ("恢复/伤病", ["recovery", "injury", "fatigue"]),
        ("心率区间", ["heart rate", "training zones", "zone"]),
    ]
    for tag, needles in mapping:
        if any(needle in lower for needle in needles):
            tags.append(tag)
    return tags or ["跑步训练"]


def score_candidate(candidate: Candidate) -> int:
    title = candidate.title.lower()
    text = f"{candidate.title} {candidate.snippet} {candidate.url}".lower()
    score = 10
    for term, points in GOOD_TERMS.items():
        if term in title:
            score += points * 2
        elif term in text:
            score += points
    for term, points in BAD_TERMS.items():
        if term in title:
            score -= points * 2
        elif term in text:
            score -= points
    if "reddit" in candidate.source.lower():
        score += 4
    if "youtube" in candidate.source.lower():
        score += 14
    if candidate.source.startswith("YouTube /"):
        score += 12
    if any(
        site in candidate.source.lower()
        for site in [
            "trainingpeaks",
            "strength running",
            "science of running",
            "morning shakeout",
            "runner",
            "marathon",
        ]
    ):
        score += 5
    if candidate.source.startswith("X @"):
        score += 4
    if candidate.created_utc:
        age_days = (dt.datetime.now(dt.UTC).timestamp() - candidate.created_utc) / 86400
        if age_days <= 14:
            score += 6
        elif age_days <= 45:
            score += 3
    if len(candidate.snippet) < 20:
        score -= 2
    if not any(term in title for term in TITLE_RELEVANCE_TERMS):
        score -= 12
    return max(score, 0)


def zh_title_summary(candidate: Candidate) -> str:
    title = clean_text(candidate.title)
    tags = candidate.topic_tags
    prefix = ""
    if "Reddit" in candidate.source:
        prefix = "跑者讨论："
    elif candidate.source.startswith("YouTube"):
        prefix = "视频素材："
    elif candidate.source:
        prefix = f"{candidate.source}："
    if contains_cjk(title):
        return f"{prefix}{title}"
    translated_theme = infer_theme(candidate)
    return f"{prefix}{translated_theme}｜{title}"


def infer_theme(candidate: Candidate) -> str:
    text = f"{candidate.title} {candidate.snippet}".lower()
    if "zone 2" in text or "aerobic base" in text:
        if "beginner" in text or "struggling" in text:
            return "新手为什么跑不进二区"
        return "二区训练和有氧基础"
    if "maf" in text or "low heart rate" in text:
        return "低心率训练的进步与挫折"
    if "threshold" in text or "tempo" in text or "lactate" in text:
        return "阈值跑和乳酸控制"
    if "marathon" in text and "half" in text:
        return "半马到全马训练安排"
    if "marathon" in text:
        return "马拉松训练策略"
    if "5k" in text or "10k" in text:
        return "5K/10K速度与耐力训练"
    if "vo2" in text or "interval" in text:
        return "间歇训练和最大摄氧量"
    if "recovery" in text:
        return "恢复与训练负荷管理"
    return "跑步训练干货"


def contains_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def zh_summary(candidate: Candidate) -> str:
    text = clean_text(candidate.snippet)
    theme = infer_theme(candidate)
    source_hint = "这条素材"
    if "Reddit" in candidate.source:
        source_hint = "这条跑者讨论"
    elif candidate.source.startswith("YouTube"):
        source_hint = "这个视频"
    elif candidate.source:
        source_hint = f"{candidate.source} 这篇内容"
    if not text:
        return f"{source_hint}围绕「{theme}」展开，适合进一步打开原文确认细节、提炼成小红书知识卡。"
    if contains_cjk(text):
        base = text
    else:
        base = english_snippet_to_chinese_style(text, theme)
    return f"{source_hint}的核心可以概括为：{base}"


def english_snippet_to_chinese_style(snippet: str, theme: str) -> str:
    lower = snippet.lower()
    points = []
    if "zone 2" in lower:
        points.append("二区不是一个神秘配速，而是用较低压力积累有氧适应")
    if "beginner" in lower or "starting" in lower:
        points.append("新手不一定一开始就能跑进二区，跑走交替或按体感慢下来很正常")
    if "aerobic" in lower or "mitochondria" in lower:
        points.append("有氧基础的价值在于线粒体、脂肪代谢和长期耐力的慢慢建立")
    if "heart rate" in lower:
        points.append("心率区间需要结合最大心率、体感和恢复状态一起判断")
    if "threshold" in lower or "lactate" in lower:
        points.append("阈值训练的重点不是硬顶，而是在可控压力下提高持续输出能力")
    if "marathon" in lower or "long run" in lower:
        points.append("长距离训练更看重能量管理、配速控制和后半程稳定性")
    if "recovery" in lower or "fatigue" in lower:
        points.append("恢复状态决定训练能不能被身体吸收")
    if not points:
        return f"它讨论的是「{theme}」，可作为一篇解释型或避坑型跑步干货的素材入口。原文摘要：{snippet[:180]}"
    return "；".join(dict.fromkeys(points)) + "。"


def xhs_angle(candidate: Candidate) -> str:
    text = f"{candidate.title} {candidate.snippet}".lower()
    if "beginner" in text and "zone 2" in text:
        return "新手跑不进二区，是训练失败还是有氧基础真实反馈？"
    if "zone 2" in text:
        return "二区训练到底该怎么跑，哪些人需要严格控制，哪些人不必焦虑？"
    if "maf" in text or "low heart rate" in text:
        return "低心率训练为什么进步慢，如何判断是在打基础还是方法错了？"
    if "threshold" in text or "lactate" in text:
        return "阈值跑怎么安排，为什么它决定比赛后半程能不能稳住？"
    if "5k" in text or "10k" in text:
        return "5K/10K不是只练速度，短距离也需要有氧底座。"
    if "marathon" in text:
        return "马拉松训练的关键不是单次猛练，而是跑量、长跑和恢复的结构。"
    if "recovery" in text or "injury" in text:
        return "训练有没有效果，先看身体能不能恢复和吸收。"
    return "可整理成跑步训练认知科普，先用痛点问题切入，再给可执行判断方法。"


def recommendation(candidate: Candidate) -> str:
    if candidate.score >= 30:
        return "优先阅读，可进入选题池"
    if candidate.score >= 22:
        return "值得备选，适合补充案例"
    if candidate.score >= 16:
        return "低优先级，先看标题摘要"
    return "暂缓"


def build_web_queries(keywords: list[str], budget: int) -> list[str]:
    queries: list[str] = []

    def add(query: str) -> None:
        if query not in queries and len(queries) < budget:
            queries.append(query)

    primary_keywords = [
        "zone 2 running training",
        "low heart rate running MAF",
        "marathon training aerobic base",
        "lactate threshold running",
        "5K 10K running training",
        "half marathon training threshold",
    ]

    for keyword in keywords[:4]:
        add(keyword)

    priority_sites = [
        "site:youtube.com/watch",
        "site:scienceofrunning.com running",
        "site:strengthrunning.com running",
        "site:themorningshakeout.com running",
        "site:trainingpeaks.com running",
        "site:marathonhandbook.com running",
        "site:runnersworld.com running",
        "site:letsrun.com/forum running",
        "site:philmaffetone.com MAF running",
        "site:reddit.com/r/AdvancedRunning",
    ]

    for keyword in primary_keywords:
        for account_query in X_ACCOUNT_QUERIES:
            add(f"{account_query} {keyword}")
            if len(queries) >= budget:
                break
        if len(queries) >= budget:
            break
        for site_query in priority_sites:
            add(f"{site_query} {keyword}")
            if len(queries) >= budget:
                break
        if len(queries) >= budget:
            break
    return queries


def build_youtube_queries(keywords: list[str], budget: int) -> list[str]:
    queries: list[str] = []

    def add(query: str) -> None:
        if query not in queries and len(queries) < budget:
            queries.append(query)

    priority_topics = [
        "zone 2 running",
        "low heart rate running",
        "MAF running",
        "marathon training",
        "half marathon training",
        "5K 10K training",
        "lactate threshold running",
        "VO2max intervals running",
        "easy run heart rate",
        "long run workout",
    ]

    for query in YOUTUBE_CREATOR_QUERIES:
        add(query)
    for keyword in keywords:
        add(keyword)
    for topic in priority_topics:
        add(topic)
    return queries


def enrich(candidates: list[Candidate]) -> list[Candidate]:
    dedup: dict[str, Candidate] = {}
    for candidate in candidates:
        key = canonical_url(candidate.url) or hashlib.sha1(candidate.url.encode()).hexdigest()
        if key in dedup:
            if len(candidate.snippet) > len(dedup[key].snippet):
                dedup[key].snippet = candidate.snippet
            dedup[key].query += f"; {candidate.query}"
            continue
        dedup[key] = candidate

    enriched = []
    for candidate in dedup.values():
        candidate.topic_tags = tag_topics(f"{candidate.title} {candidate.snippet} {candidate.url}")
        candidate.score = score_candidate(candidate)
        candidate.chinese_title = zh_title_summary(candidate)
        candidate.chinese_summary = zh_summary(candidate)
        candidate.xhs_angle = xhs_angle(candidate)
        candidate.recommendation = recommendation(candidate)
        enriched.append(candidate)
    return sorted(enriched, key=lambda c: (c.score, c.source, c.title), reverse=True)


def collect(args: argparse.Namespace) -> list[Candidate]:
    candidates: list[Candidate] = []
    keywords = args.keyword or DEFAULT_KEYWORDS
    for keyword in keywords:
        if args.include_reddit:
            candidates.extend(reddit_search(keyword, REDDIT_SUBREDDITS, args.per_source_limit))
        if args.include_youtube:
            candidates.extend(youtube_search(keyword, args.per_source_limit))
        time.sleep(args.sleep)
    if args.include_youtube:
        for query in build_youtube_queries(keywords, args.youtube_query_budget):
            candidates.extend(youtube_search(query, args.youtube_per_query_limit))
            time.sleep(args.sleep)
    if args.include_web:
        for query in build_web_queries(keywords, args.web_query_budget):
            candidates.extend(ddg_search(query, args.per_source_limit))
            time.sleep(args.sleep)
    enriched = enrich(candidates)
    if args.min_youtube_ratio and args.include_youtube:
        min_youtube_count = math.ceil(args.limit * args.min_youtube_ratio)
        youtube_candidates = [c for c in enriched if c.source.startswith("YouTube")]
        selected = youtube_candidates[:min_youtube_count]
        selected_urls = {canonical_url(c.url) or c.url for c in selected}
        for candidate in enriched:
            if len(selected) >= args.limit:
                break
            key = canonical_url(candidate.url) or candidate.url
            if key in selected_urls:
                continue
            selected.append(candidate)
            selected_urls.add(key)
        if len(youtube_candidates) < min_youtube_count:
            selected = enriched[: args.limit]
        return sorted(selected, key=lambda c: (c.score, c.source, c.title), reverse=True)[: args.limit]
    return enriched[: args.limit]


def write_reports(candidates: list[Candidate], output_dir: Path, date_label: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / f"{date_label}-running-materials"
    md_path = base.with_suffix(".md")
    csv_path = base.with_suffix(".csv")
    json_path = base.with_suffix(".json")

    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# 跑步素材候选日报｜{date_label}\n\n")
        f.write("## 使用说明\n\n")
        f.write("- 评分越高，越适合优先打开原文阅读。\n")
        f.write("- 中文摘要是基于标题、搜索摘要和可抓取正文片段的中文化整理；进入小红书制作前仍建议打开来源复核事实。\n")
        f.write("- YouTube 是优先信息源；如果选中视频，下一步应先下载字幕，再提炼核心观点并重组改写，不做逐句翻译。\n")
        f.write("- 选题角度按秋海跑步文章的表达习惯处理：先给问题，再给训练逻辑和可执行判断。\n\n")
        f.write("## 候选表格\n\n")
        headers = ["评分", "来源", "标签", "标题总结", "来源网址", "主要内容摘要", "小红书选题角度", "建议"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        for c in candidates:
            row = [
                str(c.score),
                c.source,
                "、".join(c.topic_tags),
                c.chinese_title,
                c.url,
                c.chinese_summary,
                c.xhs_angle,
                c.recommendation,
            ]
            f.write("| " + " | ".join(escape_md_cell(x) for x in row) + " |\n")

        f.write("\n## 下一步筛选建议\n\n")
        f.write("1. 先打开评分最高的 5-8 条，确认是否有明确事实、数据或跑者痛点。\n")
        f.write("2. 优先查看 YouTube 素材，尤其是 Floris Gierman、Nicklas Rossner、豹大王 run 及相近跑步训练频道。\n")
        f.write("3. 优先选择能改写成「误区 + 训练逻辑 + 可执行方法」的素材。\n")
        f.write("4. 如果来源是 Reddit/论坛，可作为痛点和案例；如果来源是专业网站/论文解读，可作为知识主干。\n")
        f.write("5. 选中素材后，先抓取原文/字幕并输出中文改写文章；确认后再进入 `qiuhai-xhs-images` 流程。\n")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "score",
                "source",
                "tags",
                "title_summary",
                "url",
                "summary",
                "xhs_angle",
                "recommendation",
                "query",
            ],
        )
        writer.writeheader()
        for c in candidates:
            writer.writerow(
                {
                    "score": c.score,
                    "source": c.source,
                    "tags": "、".join(c.topic_tags),
                    "title_summary": c.chinese_title,
                    "url": c.url,
                    "summary": c.chinese_summary,
                    "xhs_angle": c.xhs_angle,
                    "recommendation": c.recommendation,
                    "query": c.query,
                }
            )

    with json_path.open("w", encoding="utf-8") as f:
        json.dump([candidate_to_dict(c) for c in candidates], f, ensure_ascii=False, indent=2)

    return {"markdown": md_path, "csv": csv_path, "json": json_path}


def escape_md_cell(value: str) -> str:
    return clean_text(value).replace("|", "｜").replace("\n", " ")


def candidate_to_dict(candidate: Candidate) -> dict[str, object]:
    data = candidate.__dict__.copy()
    return data


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover running content candidates for Xiaohongshu.")
    parser.add_argument("--keyword", action="append", help="Custom keyword. Can be repeated.")
    parser.add_argument("--limit", type=int, default=30, help="Total candidates to keep.")
    parser.add_argument("--per-source-limit", type=int, default=4, help="Results per query/source.")
    parser.add_argument("--youtube-query-budget", type=int, default=24, help="Extra YouTube-focused queries per run.")
    parser.add_argument("--youtube-per-query-limit", type=int, default=2, help="Results per extra YouTube-focused query.")
    parser.add_argument("--web-query-budget", type=int, default=36, help="Maximum DuckDuckGo queries per run.")
    parser.add_argument("--min-youtube-ratio", type=float, default=0.0, help="Minimum ratio of final candidates that should come from YouTube when enough YouTube results are available.")
    parser.add_argument("--output-dir", default="running-materials", help="Report output directory.")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Date label for report.")
    parser.add_argument("--sleep", type=float, default=0.15, help="Delay between search groups.")
    parser.add_argument("--no-reddit", dest="include_reddit", action="store_false", help="Skip Reddit JSON search.")
    parser.add_argument("--no-youtube", dest="include_youtube", action="store_false", help="Skip direct YouTube search.")
    parser.add_argument("--no-web", dest="include_web", action="store_false", help="Skip DuckDuckGo web search.")
    parser.set_defaults(include_reddit=True, include_youtube=True, include_web=True)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    candidates = collect(args)
    paths = write_reports(candidates, Path(args.output_dir), args.date)
    print(f"Collected {len(candidates)} candidates.")
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
