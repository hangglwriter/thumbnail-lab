# -*- coding: utf-8 -*-
"""구글 옴니 기존영상 변형 주제 영상(조회 2천+) 썸네일 랩에 추가"""
import json, subprocess, urllib.request, os

BASE = r"D:\Sites\thumbnail-lab"
SLUG = "구글-옴니-영상변형"
KEYWORD = "구글 옴니 영상 변형"
CATEGORY = "google-io"

# 옴니 변형/편집 주제 + 조회 2천 이상 (2026-05-31 수집)
IDS = [
    "guv2-EoGUXw",  # Google 공식
    "CH7FsJ6LsSM",  # Tech Rush
    "o7v0sV5HA0g",  # Shijo p Abraham
    "pprZgm5PmT0",  # United Top Tech
    "EtG4dZfGBgo",  # AI 아스트라
    "KhfHkm6IEfc",  # 코드팩토리
    "TW4XucwPRX4",  # 닥또리
    "FCpOspogV_I",  # 애니한 콘텐츠랩
    "Q4o4zLqeNrE",  # 456tv
    "uM7dPURPvrQ",  # 브랜드마이트
    "nBUt8yN5ChU",  # ai_jinhyeong
    "Lcdj757wKRI",  # 오픈레이어
]

thumbdir = os.path.join(BASE, "thumbs", SLUG)
os.makedirs(thumbdir, exist_ok=True)


def dl(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
        f.write(r.read())


videos = []
for vid in IDS:
    out = subprocess.run(
        ["yt-dlp", f"https://youtu.be/{vid}", "--dump-json", "--no-warnings"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0 or not out.stdout.strip():
        print(f"  ! skip {vid}: {out.stderr[:120]}")
        continue
    d = json.loads(out.stdout)
    dur = d.get("duration") or 0
    fmt = "shorts" if 0 < dur <= 70 else "long"

    thumb_rel = f"thumbs/{SLUG}/{vid}.jpg"
    thumb_path = os.path.join(thumbdir, f"{vid}.jpg")
    turl = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
    try:
        dl(turl, thumb_path)
    except Exception:
        turl = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        try:
            dl(turl, thumb_path)
        except Exception as e:
            print(f"  ! thumb fail {vid}: {e}")
            turl = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"

    videos.append({
        "id": vid,
        "title": d.get("title", ""),
        "channel": d.get("channel") or d.get("uploader", ""),
        "channel_id": d.get("channel_id", ""),
        "views": d.get("view_count", 0),
        "duration": dur,
        "format": fmt,
        "upload_date": d.get("upload_date", ""),
        "thumbnail_url": turl,
        "url": f"https://youtu.be/{vid}",
        "thumb": thumb_rel,
    })
    print(f"  + {d.get('view_count',0):>9,}  {d.get('title','')[:50]}")

videos.sort(key=lambda v: v.get("views", 0), reverse=True)

from datetime import datetime
now = datetime.now().strftime("%Y-%m-%d %H:%M")
payload = {
    "keyword": KEYWORD,
    "slug": SLUG,
    "queries": ["구글 옴니 영상 변형", "Gemini Omni video editing"],
    "updated": now,
    "count": len(videos),
    "videos": videos,
}
with open(os.path.join(BASE, "data", f"{SLUG}.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

# keywords.json 등록
kwpath = os.path.join(BASE, "data", "keywords.json")
with open(kwpath, encoding="utf-8") as f:
    kw = json.load(f)
existing = next((k for k in kw["keywords"] if k["slug"] == SLUG), None)
if existing:
    existing.update({"keyword": KEYWORD, "category": CATEGORY, "count": len(videos), "updated": now})
else:
    kw["keywords"].append({"slug": SLUG, "keyword": KEYWORD, "category": CATEGORY, "count": len(videos), "updated": now})
with open(kwpath, "w", encoding="utf-8") as f:
    json.dump(kw, f, ensure_ascii=False, indent=2)

print(f"\n완료: {len(videos)}개 영상 -> data/{SLUG}.json + keywords.json 등록")
