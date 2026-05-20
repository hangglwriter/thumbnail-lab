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
# 일반 수집 (롱폼 위주, 풀버전 포함)
python scripts/collect.py "캔바 AI" --count 30
python scripts/collect.py "챗GPT 이미지" --count 30

# 쇼츠 전용 수집 (★ 2026-05-20 추가)
# - ytsearch는 쇼츠 거의 못 잡음 → YouTube sp=Shorts URL 사용
# - --shorts-search 옵션 = sp=EgIYAQ%3D%3D 자동 적용 + --shorts-only
python scripts/collect.py "AI 꿀팁" --shorts-search --count 60 \
  --category shorts --min-views 5000
# 검증: AI 꿀팁 = 30건 한국 쇼츠 (691만 AI모아둠 1위)
# 주의: niche 키워드(글쓰기, 챗GPT 단독)는 sp 결과도 빈약. 더 일반/인기 키워드로

# 검색 결과에 안 잡힌 특정 영상 직접 추가 (큐레이션)
python scripts/collect.py "캔바 AI" --add-id WRjR9cw7KyU --add-id VnMAgSd0BUg

# AI 패턴 분류 (ANTHROPIC_API_KEY 필요)
python scripts/analyze.py "캔바 AI"

# 자막 다운 + 스크립트 분석 (30만+ 영상만)
python scripts/fetch_subs.py 캔바-ai --min-views 300000 --top 5
python scripts/extract_script.py subs/캔바-ai/VIDEO_ID.ko.srt
# → 텍스트 추출 후 Claude가 분석 → data/{slug}.json의 script_analysis 필드에 박기

# 주간 인사이트 마크다운 자동 생성
python scripts/weekly_insights.py --out "D:\Sites\youtube-reports\research\YYYY-MM-DD-thumbnail-lab-insights.md"

# 로컬 확인
python -m http.server 8080
# → http://localhost:8080
```

## 쇼츠 수집 돌파법 (2026-05-20 발견)

### 문제
- `yt-dlp ytsearch80:AI` → 풀버전 위주, 쇼츠 거의 없음
- `--shorts-only` 후처리 시 0~4건만 남음
- 한국 인기 쇼츠 채널 진입 불가

### 해결
YouTube 검색 URL의 `sp=EgIYAQ%3D%3D` 파라미터 = "Type: Shorts" 필터 (base64).
```
https://www.youtube.com/results?search_query=KEYWORD&sp=EgIYAQ%3D%3D
```
yt-dlp가 이 URL 직접 처리. `--playlist-end N --dump-json` 옵션으로 정상 작동.
`collect.py`의 `yt_search_shorts()` 함수에 구현됨.

### 검증 (2026-05-20)
- AI 꿀팁 → 30건 한국 쇼츠 (691만 AI모아둠, 296만 알린, 299만 AI김새벽)
- 책 추천 → 30건 한국 쇼츠 (437만 만두책방, 391만 쩜, 319만 밍찌)
- 기존 ytsearch + --shorts-only는 동일 키워드에서 0건이었음

### 한계
- niche 키워드(글쓰기·챗GPT 단독)는 sp 결과도 풀버전 섞여 0건
- 영어 인기 키워드(AI)는 글로벌 영상 잡힘 (Squid Game ASMR 등)
- 한국 쇼츠 수집은 일반 + 인기 한국어 키워드 (AI 꿀팁, 책 추천 등) 권장

### 패턴 인사이트 리포트
`D:/Sites/youtube-reports/research/2026-05-20-shorts-thumbnail-patterns.md`
- 쇼츠 vs 롱폼 차이 7가지
- AI/책 분야별 차별 패턴
- 행글라이터 쇼츠 적용 공식: [숫자+가지] + [충격 동사] + [본인 제스처/결과물]

## 다음 세션 할 일 (2026-05-19+)

### 우선순위 1: Method C v3 4명 페르소나 자동 연동
- 주간 리포트 R0 단계에서 가장 최근 `2026-MM-DD-thumbnail-lab-insights.md`를 입력값으로 4명이 평가
- youtube-workflow의 Method C 셋업 파일에 `--insights-file` 옵션 추가

### 우선순위 2: 카피 후보 자동 생성기
- `python scripts/copy_generator.py "영상 주제"` 한 줄로:
  - 검증된 후크(0.1%·100배·공짜·죽였습니다 등) + 구조(결과 시연→대비→약속) 결합
  - 제목 후보 5개 + 썸네일 카피 5개 자동 제안
- Claude API 사용 (없으면 Claude Code가 직접)

### 우선순위 3: 자막 분석 확장
- 남은 6개 영상 분석 (각 키워드 톱 2~3위)
- 캔바 데이터 보강: `--min-views 50000`으로 재수집 + 분석

### 우선순위 4: 정기 자동 갱신
- 매주 월요일 자동 collect → analyze → insights → push 크론 셋업

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
