"""5/21 baseline과 비교해서 신규 영상 diff 추출."""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "data" / "_baseline" / "google_io_2026-05-21.json"
KEYWORDS = ["google-io-2026", "구글-io-2026", "구글-io-2026-한국",
            "gemini-omni", "gemini-spark", "gemini-35-flash"]

baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
baseline_ids = set()
for ids in baseline.values():
    baseline_ids.update(ids)

new_videos = {}  # vid -> {video, keywords:[]}
removed_videos = {}  # 떨어진 영상 (조회수/랭킹 변동 인사이트용)
all_current_ids = set()

for slug in KEYWORDS:
    p = ROOT / "data" / f"{slug}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    cur_ids = set()
    for v in d.get("videos", []):
        vid = v["id"]
        cur_ids.add(vid)
        all_current_ids.add(vid)
        if vid not in baseline_ids:
            if vid not in new_videos:
                new_videos[vid] = {"video": v, "keywords": []}
            new_videos[vid]["keywords"].append(slug)
    # baseline에 있었는데 이번에는 사라진 것
    base_set = set(baseline.get(slug, []))
    dropped = base_set - cur_ids
    for vid in dropped:
        removed_videos.setdefault(vid, []).append(slug)

def is_kr(v):
    title = v.get("title", "")
    return any("가" <= ch <= "힣" for ch in title)

new_list = list(new_videos.values())
new_list.sort(key=lambda e: -e["video"].get("views", 0))

print(f"baseline IDs: {len(baseline_ids)}")
print(f"current IDs : {len(all_current_ids)}")
print(f"신규 영상   : {len(new_videos)}")
print(f"빠진 영상   : {len(removed_videos)}")
print()
print("=== 신규 한국어 영상 ===")
kr_new = [e for e in new_list if is_kr(e["video"])]
for e in kr_new:
    v = e["video"]
    up = v.get("upload_date", "")
    print(f"  {v.get('views',0):>8,}  {up}  [{v.get('channel','')[:18]:<18}] {v.get('title','')[:60]}")
    print(f"           keywords={e['keywords']}  url={v.get('url','')}")
print()
print(f"=== 신규 영문 영상 ({len([e for e in new_list if not is_kr(e['video'])])}건) ===")
en_new = [e for e in new_list if not is_kr(e["video"])]
for e in en_new[:30]:
    v = e["video"]
    up = v.get("upload_date", "")
    print(f"  {v.get('views',0):>8,}  {up}  [{v.get('channel','')[:18]:<18}] {v.get('title','')[:60]}")

# diff 결과 저장
out = ROOT / "data" / "_baseline" / "google_io_diff_2026-05-22.json"
out.write_text(json.dumps({
    "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "baseline_count": len(baseline_ids),
    "current_count": len(all_current_ids),
    "new_count": len(new_videos),
    "removed_count": len(removed_videos),
    "new_kr": [e for e in new_list if is_kr(e["video"])],
    "new_en": [e for e in new_list if not is_kr(e["video"])],
    "removed_ids": removed_videos,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n저장: {out}")
