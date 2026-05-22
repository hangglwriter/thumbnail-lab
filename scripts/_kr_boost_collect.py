"""한국 친화 키워드 추가 수집 + 기존 6개 24시간 후 재수집."""
import subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
os.environ["PYTHONIOENCODING"] = "utf-8"

# 한국 친화 신규 키워드 4개 + 기존 6개 재수집
NEW_KR = [
    ("제미나이 옴니", "20"),
    ("제미나이 3.5 플래시", "20"),
    ("구글 플로우", "20"),
    ("AI 글래스 한국", "15"),
]
RECOLLECT = [
    ("Google I/O 2026", "30"),
    ("구글 IO 2026", "30"),
    ("구글 IO 2026 한국", "25"),
    ("Gemini Omni", "30"),
    ("Gemini Spark", "20"),
    ("Gemini 3.5 Flash", "30"),
]

for kw, count in NEW_KR + RECOLLECT:
    print(f"\n=== {kw} (top {count}) ===", flush=True)
    proc = subprocess.run(
        [sys.executable, "scripts/collect.py", kw, "--count", count, "--top", count,
         "--category", "google-io"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    print(proc.stdout[-400:] if proc.stdout else "(no stdout)", flush=True)
    if proc.returncode != 0:
        print("STDERR:", proc.stderr[-300:], flush=True)
print("\n=== 총 10개 키워드 완료 ===", flush=True)
