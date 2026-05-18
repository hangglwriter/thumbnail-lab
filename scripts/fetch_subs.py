"""
fetch_subs.py - 조회수 30만+ 영상의 한국어 자막 일괄 다운로드

사용법:
  python scripts/fetch_subs.py 클로드-ai --min-views 300000
  python scripts/fetch_subs.py 챗gpt --min-views 300000

자막 위치: subs/{slug}/{video_id}.ko.srt
"""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SUBS_DIR = ROOT / "subs"
SUBS_DIR.mkdir(exist_ok=True)


def slug(keyword: str) -> str:
    s = re.sub(r"\s+", "-", keyword.strip())
    s = re.sub(r"[^\w가-힣\-]", "", s)
    return s.lower()


def fetch_sub(video_id: str, out_dir: Path) -> str | None:
    """yt-dlp로 한국어 자막 다운 (수동 우선, 없으면 자동 자막). 결과 파일 경로."""
    out_path = out_dir / f"{video_id}.ko.srt"
    if out_path.exists() and out_path.stat().st_size > 100:
        return str(out_path)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    url = f"https://youtu.be/{video_id}"

    # 한국어 수동 자막 우선 시도
    for flag in ["--write-sub", "--write-auto-sub"]:
        cmd = [
            "yt-dlp", url,
            flag, "--sub-lang", "ko",
            "--skip-download",
            "--convert-subs", "srt",
            "-o", str(out_dir / f"{video_id}.%(ext)s"),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, errors="replace")
        # 결과 파일 찾기
        candidates = list(out_dir.glob(f"{video_id}*.srt"))
        for c in candidates:
            if c.stat().st_size > 100:
                # 표준 이름으로 rename
                if c != out_path:
                    c.rename(out_path)
                return str(out_path)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="키워드 slug (예: '클로드-ai', '챗gpt')")
    parser.add_argument("--min-views", type=int, default=300000, help="최소 조회수")
    parser.add_argument("--top", type=int, default=0, help="조회수순 상위 N개 (0=전체)")
    args = parser.parse_args()

    key_slug = slug(args.slug)
    data_path = DATA_DIR / f"{key_slug}.json"
    if not data_path.exists():
        print(f"  데이터 없음: {data_path}")
        return

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    videos = sorted(payload["videos"], key=lambda v: -v["views"])

    out_dir = SUBS_DIR / key_slug
    out_dir.mkdir(exist_ok=True)

    targets = [v for v in videos if v["views"] >= args.min_views]
    if args.top:
        targets = targets[: args.top]

    print(f"  대상: {len(targets)}개 (조회수 {args.min_views:,}+ / 키워드 '{payload['keyword']}')")
    ok, fail = 0, 0
    for i, v in enumerate(targets, 1):
        print(f"  [{i}/{len(targets)}] {v['title'][:50]}")
        result = fetch_sub(v["id"], out_dir)
        if result:
            sub_path = Path(result).relative_to(ROOT).as_posix()
            # 메타에 저장
            for vid in payload["videos"]:
                if vid["id"] == v["id"]:
                    vid["sub"] = sub_path
                    break
            ok += 1
            print(f"      OK -> {sub_path}")
        else:
            fail += 1
            print(f"      FAIL (한국어 자막 없음)")

    data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  완료: 성공 {ok} / 실패 {fail}")


if __name__ == "__main__":
    main()
