"""
analyze.py - Claude vision으로 썸네일 패턴 자동 분류

사용법:
  $env:ANTHROPIC_API_KEY = "sk-ant-..."
  python scripts/analyze.py "캔바 AI"
  python scripts/analyze.py "캔바 AI" --force   (이미 분석된 것도 재분석)
  python scripts/analyze.py "캔바 AI" --limit 10
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
THUMBS_DIR = ROOT / "thumbs"

PROMPT = """이 유튜브 썸네일을 분석해서 JSON으로만 응답해. 다른 텍스트 X.

분류 기준:
- copy_pattern: 카피 패턴. 다음 중 하나
  - "대비": 둘 비교 (포토샵 X vs 캔바 O 같은)
  - "충격": 극단적 결과 (삭제함, 다 무료 등)
  - "질문": 호기심 후크 (~다고? ~이 가능?)
  - "총정리": 입문/종합 (완벽정리, 모든것, 60분 특강)
  - "결과": 구체적 산출물 (10가지, 5장, 1초)
  - "정보": 단순 안내 (캔바 공식 같은 톤)
- person_position: 인물 위치. "좌"/"우"/"중앙"/"없음"
- main_visual: 주된 시각 요소. "로고"/"스크린샷"/"일러스트"/"인물"/"혼합"
- background_tone: 배경 분위기. "밝음"/"어두움"/"그라데이션"/"화려함"
- colors: 주요 컬러 3개 hex 코드 배열 (예: ["#1A1A2E","#FF6B35","#FFFFFF"])
- main_copy: 썸네일에서 읽히는 핵심 카피 (2~3줄까지)
- hook_words: 강조된 단어 1~3개 배열 (예: ["삭제함","무료","미친"])

응답 예시:
{"copy_pattern":"충격","person_position":"우","main_visual":"인물","background_tone":"어두움","colors":["#0A0A1E","#FF3D3D","#FFFFFF"],"main_copy":"캔바 10분 배우고 / 파워포인트 삭제함","hook_words":["삭제함"]}
"""


def analyze_with_claude(image_path: Path) -> dict | None:
    try:
        from anthropic import Anthropic
    except ImportError:
        print("  anthropic SDK 미설치 - pip install anthropic")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = Anthropic(api_key=api_key)
    img_b64 = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            },
                        },
                        {"type": "text", "text": PROMPT},
                    ],
                }
            ],
        )
        text = resp.content[0].text.strip()
        # JSON만 추출
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return json.loads(text)
    except Exception as e:
        print(f"    error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="키워드 slug (예: '캔바-ai') 또는 키워드 원문")
    parser.add_argument("--force", action="store_true", help="이미 분석된 것도 재분석")
    parser.add_argument("--limit", type=int, default=0, help="최대 분석 개수 (0=전체)")
    args = parser.parse_args()

    # slug 또는 원문 둘 다 허용
    slug = re.sub(r"\s+", "-", args.keyword.strip())
    slug = re.sub(r"[^\w가-힣\-]", "", slug).lower()

    data_path = DATA_DIR / f"{slug}.json"
    if not data_path.exists():
        print(f"  데이터 없음: {data_path}")
        print(f"  먼저 collect.py 실행: python scripts/collect.py \"{args.keyword}\"")
        sys.exit(1)

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    videos = payload["videos"]

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  ⚠️ ANTHROPIC_API_KEY 환경 변수 없음")
        print("  PowerShell: $env:ANTHROPIC_API_KEY = \"sk-ant-...\"")
        print("  분석 건너뜀. 갤러리는 작동 (라벨 없이)")
        sys.exit(0)

    targets = []
    for v in videos:
        if not args.force and v.get("analysis"):
            continue
        if not v.get("thumb"):
            continue
        targets.append(v)
        if args.limit and len(targets) >= args.limit:
            break

    print(f"  분석 대상: {len(targets)}개 / 전체 {len(videos)}개")
    print(f"  모델: claude-haiku-4-5")

    for i, v in enumerate(targets, 1):
        thumb_path = ROOT / v["thumb"]
        if not thumb_path.exists():
            continue
        print(f"  [{i}/{len(targets)}] {v['title'][:50]}")
        result = analyze_with_claude(thumb_path)
        if result:
            v["analysis"] = result
            print(f"    {result.get('copy_pattern')} / {result.get('main_visual')} / hook: {result.get('hook_words')}")
            # 중간 저장 (대량 처리 중 끊겨도 보존)
            if i % 5 == 0:
                data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(0.3)  # rate limit 여유

    data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  저장: {data_path}")


if __name__ == "__main__":
    main()
