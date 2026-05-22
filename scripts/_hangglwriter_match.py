"""행글라이터 결 매칭 점수화.

가중치:
- 비개발자 채널 가점, 개발자 채널 감점
- "직접 해봄/사용법/비교/필터/정리" 가점
- 무료/한국/접근성 가점
- 자극 파괴형 감점
- 롤폼 7~15분 가점, 쇼츠 감점
- 1인 크리에이터 시나리오 가점 (영상/콘텐츠/디자인/마케팅)
- 친근 톤(꿀팁/이렇게/직접) 가점
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYWORDS = ["google-io-2026", "구글-io-2026", "구글-io-2026-한국",
            "gemini-omni", "gemini-spark", "gemini-35-flash"]

# 가중치 사전 (대소문자 구분 안 함)
DEV_CHANNELS = [
    "코딩", "조코딩", "코드팩토리", "안될공학", "software engineer", "코딩알려드림",
    "antigravity", "rustybrick", "wpdev", "dev", "engineer",
]
TUTORIAL_HOOKS = [  # +2 each
    "직접", "해봤", "써봤", "사용법", "활용법", "활용", "방법", "테스트", "체험",
    "정리", "총정리", "한눈에", "10분", "7분", "5분", "12분", "15분",
    "튜토리얼", "tutorial", "guide", "how to", "how-to", "testei",
    "비교", "vs", "필터", "차이", "고른",
]
FREE_KR_HOOKS = [  # +1 each (max 2)
    "무료", "공짜", "0원", "free", "한국", "korea",
]
ATTRACTIVE_HOOKS = [  # +1 each (max 2)
    "꿀팁", "이렇게", "이런", "쉽게", "그냥", "솔직", "실전",
    "make", "build", "create",
]
USECASE_HOOKS = [  # +1 each (1인 크리에이터 시나리오)
    "영상", "콘텐츠", "디자인", "마케팅", "글쓰기", "쇼츠", "유튜브", "블로그",
    "video", "design", "content", "shorts", "marketing", "blog",
]
SHOCK_HOOKS = [  # -1 each
    "destroyed", "insane", "scary", "충격", "미쳤", "통수", "어이없", "killed", "scared",
    "blow your mind", "wild", "사라", "끝났",
]
CURATION_HOOKS = [  # +1 (큐레이션/필터 톤)
    "4가지", "5가지", "6가지", "7가지", "8가지", "10가지", "개만", "딱",
    "ways", "things", "tips",
]


def score_video(v: dict) -> tuple[int, dict]:
    title = v.get("title", "").lower()
    channel = v.get("channel", "").lower()
    duration = v.get("duration", 0) or 0
    fmt = v.get("format", "long")
    views = v.get("views", 0) or 0

    score = 0
    reasons = {}

    # 1) 개발자 채널 감점
    if any(d in channel for d in DEV_CHANNELS):
        score -= 3
        reasons["dev_channel"] = -3

    # 2) 튜토리얼/직접 해봄 (max +4)
    tut_hits = sum(1 for h in TUTORIAL_HOOKS if h in title)
    if tut_hits:
        bonus = min(tut_hits * 2, 4)
        score += bonus
        reasons["tutorial"] = bonus

    # 3) 무료/한국 (max +2)
    free_hits = sum(1 for h in FREE_KR_HOOKS if h in title)
    if free_hits:
        bonus = min(free_hits, 2)
        score += bonus
        reasons["free_kr"] = bonus

    # 4) 친근/실용 톤 (max +2)
    attr_hits = sum(1 for h in ATTRACTIVE_HOOKS if h in title)
    if attr_hits:
        bonus = min(attr_hits, 2)
        score += bonus
        reasons["friendly"] = bonus

    # 5) 1인 크리에이터 시나리오 (+1 each, max +2)
    use_hits = sum(1 for h in USECASE_HOOKS if h in title)
    if use_hits:
        bonus = min(use_hits, 2)
        score += bonus
        reasons["usecase"] = bonus

    # 6) 자극 파괴형 감점 (max -3)
    shock_hits = sum(1 for h in SHOCK_HOOKS if h in title)
    if shock_hits:
        penalty = -min(shock_hits, 3)
        score += penalty
        reasons["shock"] = penalty

    # 7) 큐레이션 N가지 (+1)
    if any(h in title for h in CURATION_HOOKS):
        score += 1
        reasons["curation"] = 1

    # 8) 롤폼 7~15분 가점 (+1)
    if 420 <= duration <= 900:
        score += 1
        reasons["good_length"] = 1
    elif 900 < duration <= 1500:  # 15~25분 약가점
        score += 0
    elif duration < 70 and fmt == "shorts":
        score -= 1
        reasons["shorts"] = -1
    elif duration > 3000:  # 50분+ 키노트
        score -= 1
        reasons["too_long"] = -1

    # 9) 한국어 영상 가점 (+1) — 행글라이터는 한국어 채널
    if any("가" <= ch <= "힣" for ch in v.get("title", "")):
        score += 1
        reasons["korean"] = 1

    # 10) 공식 채널 (Google, Android 본가) 감점 — 행글라이터 결 아님
    if channel in ("google", "android", "googledevelopers"):
        score -= 2
        reasons["official"] = -2

    # 11) 뉴스/방송 채널 감점
    if any(n in channel for n in ["news", "뉴스", "mbc", "sbs", "kbs", "jtbc", "ytn", "tv", "zdnet", "verge", "cnet"]):
        score -= 2
        reasons["news"] = -2

    return score, reasons


# 모든 영상 통합 (id 기준 dedupe + 키워드 추적)
all_videos = {}  # id -> {video, keywords:[]}
for slug in KEYWORDS:
    p = ROOT / "data" / f"{slug}.json"
    if not p.exists():
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    for v in d.get("videos", []):
        vid = v["id"]
        if vid not in all_videos:
            all_videos[vid] = {"video": v, "keywords": []}
        all_videos[vid]["keywords"].append(slug)

print(f"전체 고유 영상: {len(all_videos)}")

# 점수 계산
scored = []
for vid, entry in all_videos.items():
    s, reasons = score_video(entry["video"])
    scored.append({
        "id": vid,
        "score": s,
        "reasons": reasons,
        "video": entry["video"],
        "keywords": entry["keywords"],
    })

scored.sort(key=lambda x: (-x["score"], -x["video"].get("views", 0)))

# Top 행글라이터 결 매칭
print()
print("=" * 100)
print("[행글라이터 결 매칭 TOP 15] (score 높을수록 결 일치)")
print("=" * 100)
for r in scored[:15]:
    v = r["video"]
    title = v.get("title", "")[:65]
    print(f"  +{r['score']:>2}  {v.get('views',0):>9,}  {v.get('upload_date','')}  [{v.get('channel','')[:18]:<18}] {title}")
    print(f"        reasons={r['reasons']}  url={v.get('url','')}")
print()

# 결 안 맞는 영상 (낮은 점수)
print("=" * 100)
print("[결 안 맞는 영상 BOTTOM 8] (관성 회피용 — 행글라이터가 피해야 할 톤)")
print("=" * 100)
for r in scored[-8:]:
    v = r["video"]
    title = v.get("title", "")[:65]
    print(f"  {r['score']:>3}  {v.get('views',0):>9,}  [{v.get('channel','')[:18]:<18}] {title}")
    print(f"        reasons={r['reasons']}")

# 한국어 영상만 따로
print()
print("=" * 100)
print("[한국어 영상 결 매칭 TOP 10]")
print("=" * 100)
kr_scored = [r for r in scored if any("가" <= c <= "힣" for c in r["video"].get("title", ""))]
for r in kr_scored[:10]:
    v = r["video"]
    title = v.get("title", "")[:65]
    print(f"  +{r['score']:>2}  {v.get('views',0):>9,}  {v.get('upload_date','')}  [{v.get('channel','')[:18]:<18}] {title}")
    print(f"        url={v.get('url','')}")

# 저장
out = ROOT / "data" / "_baseline" / "hangglwriter_match_2026-05-22.json"
out.write_text(json.dumps({
    "generated": "2026-05-22",
    "total": len(scored),
    "top_15": scored[:15],
    "kr_top_10": kr_scored[:10],
    "bottom_8": scored[-8:],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n저장: {out}")
