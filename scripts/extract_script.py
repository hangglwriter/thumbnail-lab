"""
extract_script.py - SRT 자막을 분석용 텍스트로 추출

사용법:
  python scripts/extract_script.py subs/클로드-ai/aITV54CLc_U.ko.srt

출력: 인트로 60초 + 중간 샘플 2곳 + 엔딩 60초 텍스트 (분석용)
"""

import re
import sys
from pathlib import Path


def parse_srt(text: str):
    """SRT → [(start_seconds, end_seconds, text)] 리스트"""
    blocks = re.split(r"\n\s*\n", text.strip())
    items = []
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        # 첫 줄: 인덱스 (숫자) / 둘째 줄: 시간코드 / 나머지: 텍스트
        time_line = None
        text_lines = []
        for line in lines:
            if re.match(r"^\d+$", line) and time_line is None:
                continue
            if "-->" in line:
                time_line = line
            else:
                text_lines.append(line)
        if not time_line or not text_lines:
            continue
        m = re.match(r"(\d{2}):(\d{2}):(\d{2})[,\.](\d+)\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d+)", time_line)
        if not m:
            continue
        sh, sm, ss, sms, eh, em, es, ems = m.groups()
        start = int(sh) * 3600 + int(sm) * 60 + int(ss) + int(sms) / 1000
        end = int(eh) * 3600 + int(em) * 60 + int(es) + int(ems) / 1000
        # 텍스트에서 HTML 태그·메타 제거
        joined = " ".join(text_lines)
        joined = re.sub(r"<[^>]+>", "", joined)
        joined = re.sub(r"\{[^}]+\}", "", joined)
        items.append((start, end, joined.strip()))
    return items


def fmt_time(s: float) -> str:
    m, sec = divmod(int(s), 60)
    return f"{m:02d}:{sec:02d}"


def collect(items, start: float, end: float) -> str:
    """주어진 시간대의 자막을 이어붙임"""
    parts = []
    for s, e, t in items:
        if e < start or s > end:
            continue
        parts.append(t)
    # 중복·반복 제거 (자동 자막의 흔한 노이즈)
    seen = set()
    cleaned = []
    for p in parts:
        key = p.strip()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(key)
    return " ".join(cleaned)


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/extract_script.py <srt_path>")
        sys.exit(1)

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8", errors="replace")
    items = parse_srt(text)
    if not items:
        print("자막 파싱 실패")
        sys.exit(1)

    duration = items[-1][1]
    print(f"# {path.name}")
    print(f"# 총 길이: {fmt_time(duration)} ({len(items)}개 큐)")
    print()

    print("## 인트로 (0-60초)")
    print(collect(items, 0, 60))
    print()

    # 중간 샘플 2곳
    if duration > 180:
        mid1 = duration * 0.3
        print(f"## 중간 1 ({fmt_time(mid1)}~{fmt_time(mid1+30)})")
        print(collect(items, mid1, mid1 + 30))
        print()
        mid2 = duration * 0.6
        print(f"## 중간 2 ({fmt_time(mid2)}~{fmt_time(mid2+30)})")
        print(collect(items, mid2, mid2 + 30))
        print()

    print(f"## 엔딩 (마지막 60초, {fmt_time(max(0, duration-60))}~{fmt_time(duration)})")
    print(collect(items, max(0, duration - 60), duration))


if __name__ == "__main__":
    main()
