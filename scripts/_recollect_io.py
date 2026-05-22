"""구글 I/O 6개 키워드 재수집 (5/22 신규 영상 diff용)."""
import subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
os.environ["PYTHONIOENCODING"] = "utf-8"

KEYWORDS = [
    ("Google I/O 2026", "26"),
    ("구글 IO 2026", "26"),
    ("구글 IO 2026 한국", "18"),
    ("Gemini Omni", "27"),
    ("Gemini Spark", "20"),
    ("Gemini 3.5 Flash", "28"),
]

for kw, count in KEYWORDS:
    print(f"\n=== {kw} (top {count}) ===", flush=True)
    proc = subprocess.run(
        [sys.executable, "scripts/collect.py", kw, "--count", count, "--top", count,
         "--category", "google-io"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    print(proc.stdout[-600:] if proc.stdout else "(no stdout)", flush=True)
    if proc.returncode != 0:
        print("STDERR:", proc.stderr[-400:], flush=True)
print("\n=== 6개 키워드 재수집 완료 ===", flush=True)
