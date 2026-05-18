# thumbnail-lab

행글라이터 영상 기획용 - 키워드별 유튜브 인기 썸네일 자동 수집 + AI 패턴 분류 갤러리

## 핵심

영상 만들 때마다 인기 썸네일 일일이 검색하는 작업 자동화. 키워드 던지면:
1. `collect.py` - yt-dlp로 톱 N개 자동 수집 (썸네일 + 메타)
2. `analyze.py` - Claude vision으로 패턴 자동 분류
3. `index.html` - 갤러리에서 검색·필터·★ 즐겨찾기

## 폴더 구조

```
thumbnail-lab/
├─ index.html          # 갤러리 UI (Tailwind CDN, fetch로 data 로드)
├─ thumbs/<키워드>/    # 썸네일 jpg (Vercel public)
├─ data/<키워드>.json  # 메타 + AI 분석 결과
├─ data/keywords.json  # 키워드 인덱스
├─ scripts/
│  ├─ collect.py       # yt-dlp 수집
│  ├─ analyze.py       # Claude API 패턴 분류
│  └─ requirements.txt
└─ README.md
```

## 사용법

```bash
# 수집
python scripts/collect.py "캔바 AI" --count 30
python scripts/collect.py "챗GPT 이미지" --count 30

# 검색 결과에 안 잡힌 특정 영상 직접 추가 (큐레이션)
python scripts/collect.py "캔바 AI" --add-id WRjR9cw7KyU --add-id VnMAgSd0BUg

# AI 패턴 분류 (ANTHROPIC_API_KEY 필요)
python scripts/analyze.py "캔바 AI"

# 로컬 확인
python -m http.server 8080
# → http://localhost:8080
```

## AI 분류 라벨

- **카피 패턴**: 대비 / 충격 / 질문 / 총정리 / 결과 / 정보
- **인물 위치**: 좌 / 우 / 중앙 / 없음
- **메인 시각**: 로고 / 스크린샷 / 일러스트 / 인물 / 혼합
- **배경 톤**: 밝음 / 어두움 / 그라데이션
- **컬러**: 주요 3색 hex

## 배포

- GitHub repo → Vercel 연결 (정적 사이트, 빌드 없음)
- `mintmaum07@gmail.com` 커밋 이메일 일치 필수
- 자동 수집은 로컬에서 `collect.py` 실행 → git push → Vercel 자동 배포

## 주의

- `thumbs/` 폴더는 git에 push (Vercel이 서빙)
- API 키 없으면 analyze.py는 빈 라벨로 fallback. 갤러리는 작동
- 첫 수집은 캔바 AI 키워드부터 (검증 완료)
