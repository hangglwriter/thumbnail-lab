"""
collect.py - 키워드로 유튜브 인기 썸네일 자동 수집

사용법:
  python scripts/collect.py "캔바 AI" --count 30
  python scripts/collect.py "캔바 AI" --count 30 --extra "Canva AI 2.0"
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THUMBS_DIR = ROOT / "thumbs"
DATA_DIR = ROOT / "data"
THUMBS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


def slug(keyword: str) -> str:
    s = re.sub(r"\s+", "-", keyword.strip())
    s = re.sub(r"[^\w가-힣\-]", "", s)
    return s.lower()


def yt_search(query: str, count: int) -> list[dict]:
    print(f"  searching: {query} (top {count})")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        ["yt-dlp", f"ytsearch{count}:{query}", "--dump-json", "--no-warnings"],
        capture_output=True, text=True, encoding="utf-8", env=env, errors="replace",
    )
    rows = []
    for line in proc.stdout.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(d)
    return rows


def yt_search_shorts(query: str, count: int) -> list[dict]:
    """YouTube 검색의 sp=EgIYAQ%3D%3D 필터 = Type: Shorts 전용.
    ytsearch가 일반 영상 위주로 잡는 한계 회피용."""
    print(f"  shorts search: {query} (top {count})")
    q = query.replace(" ", "+")
    sp_url = f"https://www.youtube.com/results?search_query={q}&sp=EgIYAQ%3D%3D"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        ["yt-dlp", sp_url, "--playlist-end", str(count), "--dump-json", "--no-warnings"],
        capture_output=True, text=True, encoding="utf-8", env=env, errors="replace",
    )
    rows = []
    for line in proc.stdout.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(d)
    return rows


def yt_channel_shorts(channel_url: str, count: int) -> list[dict]:
    """채널의 /shorts 페이지에서 영상 풀 정보 수집.
    channel_url: 'https://www.youtube.com/@핸들' 또는 그대로 '/shorts' 포함도 OK."""
    if not channel_url.rstrip("/").endswith("/shorts"):
        channel_url = channel_url.rstrip("/") + "/shorts"
    print(f"  channel shorts: {channel_url} (top {count})")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        ["yt-dlp", channel_url, "--playlist-end", str(count), "--dump-json", "--no-warnings"],
        capture_output=True, text=True, encoding="utf-8", env=env, errors="replace",
    )
    rows = []
    for line in proc.stdout.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(d)
    return rows


def normalize(d: dict) -> dict:
    duration = d.get("duration") or 0
    return {
        "id": d.get("id", ""),
        "title": d.get("title", ""),
        "channel": d.get("channel", ""),
        "channel_id": d.get("channel_id", ""),
        "views": d.get("view_count") or 0,
        "duration": duration,
        "format": "shorts" if duration <= 70 else "long",
        "upload_date": d.get("upload_date", ""),
        "thumbnail_url": d.get("thumbnail", ""),
        "url": f"https://youtu.be/{d.get('id','')}",
    }


def download_thumb(video_id: str, out_path: Path) -> bool:
    if out_path.exists() and out_path.stat().st_size > 5000:
        return True
    urls = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]
    for url in urls:
        try:
            urllib.request.urlretrieve(url, out_path)
            if out_path.stat().st_size > 5000:
                return True
        except Exception:
            continue
    return False


def update_keywords_index(keyword: str, count: int, category: str = "general"):
    idx_path = DATA_DIR / "keywords.json"
    idx = {"keywords": []}
    if idx_path.exists():
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = {k["slug"]: k for k in idx.get("keywords", [])}
    existing = entries.get(slug(keyword), {})
    entries[slug(keyword)] = {
        "slug": slug(keyword),
        "keyword": keyword,
        "category": category or existing.get("category", "general"),
        "count": count,
        "updated": time.strftime("%Y-%m-%d %H:%M"),
    }
    idx["keywords"] = sorted(entries.values(), key=lambda k: (k.get("category", "general"), k["keyword"]))
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="주 검색어 (예: '캔바 AI')")
    parser.add_argument("--extra", action="append", default=[], help="추가 검색어 (병합)")
    parser.add_argument("--count", type=int, default=30, help="각 쿼리당 검색 개수")
    parser.add_argument("--top", type=int, default=30, help="저장할 최종 개수 (조회수순)")
    parser.add_argument("--filter", default="", help="제목에 포함돼야 하는 키워드(콤마 구분)")
    parser.add_argument("--add-id", action="append", default=[], help="검색 결과에 없는 영상 ID 직접 추가 (큐레이션용)")
    parser.add_argument("--exclude-channel", default="", help="제외할 채널명 키워드 (콤마 구분, 부분 매칭). 공식/광고/뉴스 제외용")
    parser.add_argument("--min-views", type=int, default=0, help="최소 조회수 (이하 제외)")
    parser.add_argument("--shorts-only", action="store_true", help="duration<=70초 (쇼츠)만 저장")
    parser.add_argument("--shorts-search", action="store_true", help="YouTube 쇼츠 전용 검색 URL 사용 (sp=EgIYAQ). --shorts-only 자동 적용")
    parser.add_argument("--channel", default="", help="채널 URL (예: https://www.youtube.com/@bookvore). 쇼츠만 자동 수집")
    parser.add_argument("--category", default="general", help="키워드 카테고리 (general/ai/shorts/books 등)")
    args = parser.parse_args()

    keyword = args.keyword
    key_slug = slug(keyword)
    out_thumbs_dir = THUMBS_DIR / key_slug
    out_thumbs_dir.mkdir(exist_ok=True)
    out_json = DATA_DIR / f"{key_slug}.json"

    queries = [keyword] + args.extra
    all_rows: dict[str, dict] = {}
    if args.channel:
        # 채널 모드: 쿼리 무시, 채널 쇼츠 페이지만 수집
        args.shorts_only = True
        for d in yt_channel_shorts(args.channel, args.count):
            r = normalize(d)
            if not r["id"]:
                continue
            if r["id"] not in all_rows:
                all_rows[r["id"]] = r
    else:
        search_fn = yt_search_shorts if args.shorts_search else yt_search
        if args.shorts_search:
            args.shorts_only = True  # 쇼츠 검색이면 자동으로 쇼츠 필터
        for q in queries:
            for d in search_fn(q, args.count):
                r = normalize(d)
                if not r["id"]:
                    continue
                if r["id"] not in all_rows:
                    all_rows[r["id"]] = r

    if args.filter:
        terms = [t.strip().lower() for t in args.filter.split(",") if t.strip()]
        all_rows = {
            vid: r for vid, r in all_rows.items()
            if any(t in r["title"].lower() for t in terms)
        }

    if args.exclude_channel:
        excl = [t.strip().lower() for t in args.exclude_channel.split(",") if t.strip()]
        before = len(all_rows)
        all_rows = {
            vid: r for vid, r in all_rows.items()
            if not any(t in r["channel"].lower() for t in excl)
        }
        print(f"  exclude-channel: {before - len(all_rows)}개 제외")

    if args.min_views > 0:
        before = len(all_rows)
        all_rows = {vid: r for vid, r in all_rows.items() if r["views"] >= args.min_views}
        print(f"  min-views {args.min_views:,}: {before - len(all_rows)}개 제외")

    if args.shorts_only:
        before = len(all_rows)
        all_rows = {vid: r for vid, r in all_rows.items() if r["format"] == "shorts"}
        print(f"  shorts-only: {before - len(all_rows)}개 제외 (롱폼 빼고 쇼츠만)")

    rows = sorted(all_rows.values(), key=lambda r: -r["views"])[: args.top]

    # 큐레이션: --add-id로 들어온 영상은 필터·top 제한 무시하고 무조건 포함
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    existing_ids = {r["id"] for r in rows}
    for vid in getattr(args, "add_id", []) or []:
        if vid in existing_ids:
            continue
        print(f"  fetching by ID: {vid}")
        proc = subprocess.run(
            ["yt-dlp", f"https://youtu.be/{vid}", "--dump-json", "--no-warnings"],
            capture_output=True, text=True, encoding="utf-8", env=env, errors="replace",
        )
        out = proc.stdout.strip().split("\n")[0] if proc.stdout else ""
        try:
            r = normalize(json.loads(out))
            rows.append(r)
            existing_ids.add(r["id"])
            print(f"    OK [{r['channel'][:20]}] {r['title'][:50]}")
        except Exception as e:
            print(f"    FAIL: {e}")

    rows.sort(key=lambda r: -r["views"])

    print(f"\n  {len(rows)}개 후보 → 썸네일 다운로드")
    for i, r in enumerate(rows, 1):
        thumb_path = out_thumbs_dir / f"{r['id']}.jpg"
        if download_thumb(r["id"], thumb_path):
            r["thumb"] = f"thumbs/{key_slug}/{r['id']}.jpg"
        else:
            r["thumb"] = ""
            print(f"    [{i}] FAIL {r['id']}")
        if i % 10 == 0:
            print(f"    [{i}/{len(rows)}] done")

    # 기존 분석 라벨 유지 (있으면)
    existing = {}
    if out_json.exists():
        try:
            old = json.loads(out_json.read_text(encoding="utf-8"))
            existing = {v["id"]: v.get("analysis", {}) for v in old.get("videos", [])}
        except Exception:
            pass
    for r in rows:
        if r["id"] in existing and existing[r["id"]]:
            r["analysis"] = existing[r["id"]]

    payload = {
        "keyword": keyword,
        "slug": key_slug,
        "queries": queries,
        "updated": time.strftime("%Y-%m-%d %H:%M"),
        "count": len(rows),
        "videos": rows,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    update_keywords_index(keyword, len(rows), args.category)

    print(f"\n  저장: {out_json}")
    print(f"  썸네일: {out_thumbs_dir} ({len(list(out_thumbs_dir.glob('*.jpg')))}개)")
    print(f"  done.")


if __name__ == "__main__":
    main()
