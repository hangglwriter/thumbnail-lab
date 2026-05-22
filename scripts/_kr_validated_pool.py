"""한국 검증 풀 추출 — 13개 키워드 통합, 한국어 1만+, 결+5 이상."""
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEV_CHANNELS = ["코딩", "조코딩", "코드팩토리", "안될공학", "software engineer", "코딩알려드림",
    "antigravity", "rustybrick", "wpdev", "engineer"]
TUTORIAL_HOOKS = ["직접", "해봤", "써봤", "사용법", "활용법", "활용", "방법", "테스트", "체험",
    "정리", "총정리", "한눈에", "10분", "7분", "5분", "12분", "15분",
    "튜토리얼", "tutorial", "guide", "how to", "how-to", "testei",
    "비교", "vs", "필터", "차이", "고른"]
FREE_KR_HOOKS = ["무료", "공짜", "0원", "free", "한국", "korea"]
ATTRACTIVE_HOOKS = ["꿀팁", "이렇게", "이런", "쉽게", "그냥", "솔직", "실전",
    "make", "build", "create"]
USECASE_HOOKS = ["영상", "콘텐츠", "디자인", "마케팅", "글쓰기", "쇼츠", "유튜브", "블로그",
    "video", "design", "content", "shorts", "marketing", "blog"]
SHOCK_HOOKS = ["destroyed", "insane", "scary", "충격", "미쳤", "통수", "killed", "scared",
    "blow your mind", "wild"]
CURATION_HOOKS = ["4가지", "5가지", "6가지", "7가지", "8가지", "10가지", "개만", "딱",
    "ways", "things", "tips"]


def score_video(v):
    title = v.get("title", "").lower()
    channel = v.get("channel", "").lower()
    duration = v.get("duration", 0) or 0
    fmt = v.get("format", "long")
    s = 0; r = {}
    if any(d in channel for d in DEV_CHANNELS): s -= 3; r["dev_channel"] = -3
    th = sum(1 for h in TUTORIAL_HOOKS if h in title)
    if th: b = min(th * 2, 4); s += b; r["tutorial"] = b
    fh = sum(1 for h in FREE_KR_HOOKS if h in title)
    if fh: b = min(fh, 2); s += b; r["free_kr"] = b
    ah = sum(1 for h in ATTRACTIVE_HOOKS if h in title)
    if ah: b = min(ah, 2); s += b; r["friendly"] = b
    uh = sum(1 for h in USECASE_HOOKS if h in title)
    if uh: b = min(uh, 2); s += b; r["usecase"] = b
    sh = sum(1 for h in SHOCK_HOOKS if h in title)
    if sh: p = -min(sh, 3); s += p; r["shock"] = p
    if any(h in title for h in CURATION_HOOKS): s += 1; r["curation"] = 1
    if 420 <= duration <= 900: s += 1; r["good_length"] = 1
    elif duration < 70 and fmt == "shorts": s -= 1; r["shorts"] = -1
    elif duration > 3000: s -= 1; r["too_long"] = -1
    if any("가" <= ch <= "힣" for ch in v.get("title", "")): s += 1; r["korean"] = 1
    if channel in ("google", "android", "googledevelopers"): s -= 2; r["official"] = -2
    if any(n in channel for n in ["news", "뉴스", "mbc", "sbs", "kbs", "jtbc", "ytn", "tv", "zdnet", "verge", "cnet"]):
        s -= 2; r["news"] = -2
    return s, r


# 13개 키워드
KEYWORDS = ['google-io-2026', '구글-io-2026', '구글-io-2026-한국', 'gemini-omni',
    'gemini-spark', 'gemini-35-flash', '캔바-ai', '챗gpt', '이미지-ai',
    '영상-ai', '메타-ai-한국', '메타-ai', 'ai-꿀팁', '나노바나나', '제미나이',
    '클로드-ai', '메타-ai-무료']

kr_high = {}
for s in KEYWORDS:
    p = ROOT / "data" / f"{s}.json"
    if not p.exists(): continue
    d = json.loads(p.read_text(encoding="utf-8"))
    for v in d.get("videos", []):
        if not any("가" <= ch <= "힣" for ch in v.get("title", "")): continue
        if v.get("views", 0) < 10000: continue
        sc, r = score_video(v)
        if v["id"] not in kr_high:
            kr_high[v["id"]] = {"score": sc, "reasons": r, "video": v, "kws": [s]}
        else:
            kr_high[v["id"]]["kws"].append(s)

# Flow/VEO 카테고리 추출
flow_videos = [r for r in kr_high.values() if any(t in r["video"].get("title","").lower() for t in ["flow", "플로우", "플로 ", "veo"])]
flow_videos.sort(key=lambda x: -x["video"].get("views", 0))

# 결+5 이상 + 톤별 분류
tier_videos = sorted([r for r in kr_high.values() if r["score"] >= 5], key=lambda x: -x["video"].get("views", 0))

print(f"한국 1만+ 영상: {len(kr_high)}건")
print(f"결+5 이상: {len(tier_videos)}건")
print(f"Flow/VEO 관련 한국 1만+: {len(flow_videos)}건")
print()
print("=== Flow/VEO 카테고리 한국 검증 영상 (1만+) ===")
for r in flow_videos:
    v = r["video"]
    print(f"  결+{r['score']}  {v['views']:>9,}  {v.get('upload_date','')}  [{v.get('channel','')[:18]:<18}] {v.get('title','')[:65]}")

# 저장
out = ROOT / "data" / "_baseline" / "kr_validated_pool_2026-05-23.json"
out.write_text(json.dumps({
    "generated": "2026-05-23",
    "kr_1man_plus": len(kr_high),
    "tier_top": [r for r in tier_videos[:50]],
    "flow_category": flow_videos,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n저장: {out}")
