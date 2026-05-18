"""
weekly_insights.py - 전체 데이터에서 통합 인사이트 마크다운 자동 생성

사용법:
  python scripts/weekly_insights.py
  python scripts/weekly_insights.py --out D:\Sites\youtube-reports\research\2026-05-18-thumbnail-lab-insights.md
"""

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def fmt_num(n: int) -> str:
    if n >= 10000:
        return f"{n/10000:.1f}".rstrip("0").rstrip(".") + "만"
    if n >= 1000:
        return f"{n/1000:.1f}".rstrip("0").rstrip(".") + "천"
    return f"{n:,}"


def load_all():
    """모든 키워드 데이터를 한 번에 로드"""
    all_videos = []
    by_keyword = {}
    for p in sorted(DATA_DIR.glob("*.json")):
        if p.name == "keywords.json":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        kw = d.get("keyword", p.stem)
        by_keyword[kw] = d
        for v in d["videos"]:
            v["_keyword"] = kw
            all_videos.append(v)
    return all_videos, by_keyword


def pattern_stats(videos):
    """copy_pattern별 평균 조회수 + 카운트"""
    by_pattern = {}
    for v in videos:
        p = (v.get("analysis") or {}).get("copy_pattern")
        if not p:
            continue
        by_pattern.setdefault(p, []).append(v)
    rows = []
    for p, vs in by_pattern.items():
        avg = sum(v["views"] for v in vs) // len(vs)
        median_views = sorted(v["views"] for v in vs)[len(vs)//2]
        rows.append({"pattern": p, "count": len(vs), "avg_views": avg, "median_views": median_views})
    rows.sort(key=lambda r: -r["avg_views"])
    return rows


def hook_frequency(videos, top_n=15):
    """후크 단어 빈도"""
    counter = Counter()
    for v in videos:
        words = (v.get("analysis") or {}).get("hook_words") or []
        for w in words:
            counter[w.strip()] += 1
    return counter.most_common(top_n)


def visual_stats(videos):
    """인물 위치 + 시각 요소 빈도"""
    pos = Counter()
    visual = Counter()
    tone = Counter()
    for v in videos:
        a = v.get("analysis") or {}
        if a.get("person_position"):
            pos[a["person_position"]] += 1
        if a.get("main_visual"):
            visual[a["main_visual"]] += 1
        if a.get("background_tone"):
            tone[a["background_tone"]] += 1
    return pos, visual, tone


def script_analyzed(videos):
    """script_analysis 있는 영상 리스트"""
    return [v for v in videos if v.get("script_analysis")]


def top_videos_by_keyword(by_keyword, n=5):
    """키워드별 톱 N (조회수순)"""
    result = {}
    for kw, d in by_keyword.items():
        sorted_v = sorted(d["videos"], key=lambda v: -v["views"])[:n]
        result[kw] = sorted_v
    return result


def render_markdown(all_videos, by_keyword):
    lines = []
    import time
    today = time.strftime("%Y-%m-%d")

    lines.append("---")
    lines.append("title: 썸네일 랩 주간 인사이트 - " + today)
    lines.append(f"date: {today}")
    lines.append("category: research")
    lines.append("tags: [thumbnail-lab, weekly-insights, AI영상기획]")
    lines.append("---")
    lines.append("")
    lines.append(f"# 썸네일 랩 주간 인사이트 ({today})")
    lines.append("")
    lines.append(f"전체 영상: **{len(all_videos)}개** / 분석 완료(썸네일): **{sum(1 for v in all_videos if v.get('analysis'))}개** / 스크립트 분석: **{len(script_analyzed(all_videos))}개**")
    lines.append("")
    lines.append("> 사이트: https://thumbnail-lab-smoky.vercel.app")
    lines.append("")

    # 1. 패턴별 효과 순위
    lines.append("## 1. 어떤 카피 패턴이 가장 많이 봤나? (평균 조회수)")
    lines.append("")
    lines.append("| 패턴 | 분석된 영상 | 평균 조회수 | 중간값 |")
    lines.append("|------|------------|------------|--------|")
    for r in pattern_stats(all_videos):
        lines.append(f"| **{r['pattern']}** | {r['count']}개 | {fmt_num(r['avg_views'])} | {fmt_num(r['median_views'])} |")
    lines.append("")
    lines.append("> 평균 조회수가 가장 높은 패턴 = 같은 주제에서 가장 잘 통하는 카피 방식")
    lines.append("")

    # 2. 후크 단어 톱
    lines.append("## 2. 자주 박힌 후크 단어 톱 15")
    lines.append("")
    for w, c in hook_frequency(all_videos, 15):
        lines.append(f"- **{w}** ({c}회)")
    lines.append("")

    # 3. 시각 패턴
    pos, visual, tone = visual_stats(all_videos)
    lines.append("## 3. 시각 패턴 분포")
    lines.append("")
    lines.append("### 인물 위치")
    for k, c in pos.most_common():
        lines.append(f"- {k}: {c}개")
    lines.append("")
    lines.append("### 메인 시각 요소")
    for k, c in visual.most_common():
        lines.append(f"- {k}: {c}개")
    lines.append("")
    lines.append("### 배경 톤")
    for k, c in tone.most_common():
        lines.append(f"- {k}: {c}개")
    lines.append("")

    # 4. 키워드별 톱 5
    lines.append("## 4. 키워드별 톱 5 (조회수순)")
    lines.append("")
    for kw, vids in top_videos_by_keyword(by_keyword, 5).items():
        lines.append(f"### {kw}")
        lines.append("")
        for v in vids:
            a = v.get("analysis") or {}
            pattern = a.get("copy_pattern", "-")
            lines.append(f"- [{fmt_num(v['views'])}회 / {pattern}] **{v['title']}** ({v['channel']}) → {v['url']}")
        lines.append("")

    # 5. 스크립트 분석된 영상의 공통 인사이트
    sa_videos = script_analyzed(all_videos)
    if sa_videos:
        lines.append("## 5. 스크립트까지 분석한 인기 영상 (왜 끝까지 보게 되나)")
        lines.append("")
        for v in sa_videos:
            s = v["script_analysis"]
            lines.append(f"### [{fmt_num(v['views'])}회] {v['title']}")
            lines.append(f"채널: {v['channel']} / {v['url']}")
            lines.append("")
            if s.get("intro_hook"):
                lines.append(f"**🎣 인트로 후크**: {s['intro_hook']}")
                lines.append("")
            if s.get("structure"):
                lines.append("**🏗️ 구조**")
                for st in s["structure"]:
                    lines.append(f"- {st}")
                lines.append("")
            if s.get("hook_techniques"):
                lines.append(f"**🎯 핵심 후크 단어**: {' · '.join(s['hook_techniques'])}")
                lines.append("")
            if s.get("cta"):
                lines.append(f"**📢 CTA**: {s['cta']}")
                lines.append("")
            if s.get("why_popular"):
                lines.append(f"**🔥 왜 인기를 끌었나**: {s['why_popular']}")
                lines.append("")
            if s.get("benchmark_for_hangglwriter"):
                lines.append(f"> **💡 행글라이터 벤치마킹**: {s['benchmark_for_hangglwriter']}")
                lines.append("")
            lines.append("---")
            lines.append("")

    # 6. 다음 영상 기획 액션 아이템 (수동 작성 필요)
    lines.append("## 6. 다음 영상 기획 액션 (검증된 공식 기반)")
    lines.append("")
    lines.append("> 위 패턴/후크/구조 분석을 토대로, 다음 영상 기획에 즉시 적용할 포인트")
    lines.append("> (이 섹션은 Claude가 직접 작성합니다)")
    lines.append("")
    lines.append("- [ ] 액션 1: ")
    lines.append("- [ ] 액션 2: ")
    lines.append("- [ ] 액션 3: ")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="", help="출력 마크다운 경로 (기본: 콘솔 출력)")
    args = parser.parse_args()

    all_videos, by_keyword = load_all()
    md = render_markdown(all_videos, by_keyword)

    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"saved: {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
