# 썸네일 랩 (Thumbnail Lab)

키워드 던지면 유튜브 인기 썸네일 자동 수집 + AI 패턴 분류 → 갤러리.

영상 만들 때마다 반복하던 "인기 썸네일 찾기·메모"를 시스템화한 1인 크리에이터용 영감 사이트.

## 빠른 시작

```bash
pip install -r scripts/requirements.txt

# 1. 수집
python scripts/collect.py "캔바 AI" --count 30

# 2. AI 패턴 분류 (선택)
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # PowerShell
python scripts/analyze.py "캔바 AI"

# 3. 로컬에서 보기
python -m http.server 8080
# → http://localhost:8080
```

## 배포

Vercel에 GitHub repo 연결만 하면 끝 (정적 사이트, 빌드 없음).

## 기능

- 키워드별 톱 N개 인기 영상 자동 수집 (yt-dlp)
- 썸네일 + 제목 + 채널 + 조회수 + 길이 + 업로드일 메타
- Claude vision으로 카피·인물·시각·컬러 패턴 자동 분류
- 검색 + 필터 (조회수순/최신순/쇼츠/롱폼/패턴)
- ★ 즐겨찾기 (localStorage)
- 다크 모드 기본

## 라이선스

개인 용도. 썸네일 원본은 각 채널 저작권.
