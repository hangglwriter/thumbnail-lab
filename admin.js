/**
 * 썸네일 랩 - 관리 위젯 (추가/삭제)
 *
 * 삭제: 카드 호버 ❌ → GitHub API로 data/{slug}.json 수정 → 즉시 반영
 * 추가: URL 입력 → YouTube Data API로 정보 fetch → 카드 생성 (API 키 설정 후 활성)
 *
 * 토큰: localStorage("gh_token_thumbnail_lab"), YouTube API: localStorage("yt_api_key")
 */

(function () {
  const REPO = "hangglwriter/thumbnail-lab";
  const BRANCH = "master";
  const TOKEN_KEY = "gh_token_thumbnail_lab";
  const YT_KEY = "yt_api_key";

  // ── 스타일 ────────────────────────────────────────────────
  const css = `
    .admin-btn {
      background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
      color: #e5e7eb; padding: 6px 10px; border-radius: 8px;
      font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;
    }
    .admin-btn:hover { background: rgba(245,158,11,0.2); border-color: rgba(245,158,11,0.5); }
    .admin-btn.active { background: rgba(34,197,94,0.2); border-color: rgba(34,197,94,0.5); }
    .delete-btn {
      position: absolute; top: 6px; right: 6px;
      width: 26px; height: 26px; border-radius: 50%;
      background: rgba(0,0,0,0.7); color: #fca5a5; border: 1px solid rgba(252,165,165,0.3);
      font-size: 14px; cursor: pointer; z-index: 5;
      display: none; align-items: center; justify-content: center;
      transition: all 0.15s ease;
    }
    .delete-btn:hover { background: rgba(220,38,38,0.9); color: #fff; transform: scale(1.1); }
    .thumb-card:hover .delete-btn { display: flex; }

    /* 모달 */
    .admin-modal {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 10000;
      display: none; align-items: center; justify-content: center;
      backdrop-filter: blur(4px);
    }
    .admin-modal.open { display: flex; }
    .admin-modal-box {
      background: #111827; border: 1px solid #374151; border-radius: 12px;
      padding: 24px; width: 440px; max-width: calc(100vw - 32px);
      color: #e5e7eb; font-family: -apple-system, "Noto Sans KR", sans-serif;
    }
    .admin-modal-box h3 {
      font-size: 17px; font-weight: 700; margin: 0 0 16px;
      display: flex; align-items: center; gap: 8px;
    }
    .admin-modal-box label {
      display: block; font-size: 12px; color: #9ca3af; margin: 12px 0 6px;
    }
    .admin-modal-box input, .admin-modal-box select {
      width: 100%; background: #1f2937; border: 1px solid #374151;
      color: #e5e7eb; padding: 9px 12px; border-radius: 6px;
      font-size: 14px; box-sizing: border-box;
    }
    .admin-modal-box input:focus, .admin-modal-box select:focus {
      outline: none; border-color: #f59e0b;
    }
    .admin-modal-box .row { display: flex; gap: 10px; margin-top: 16px; }
    .admin-modal-box .row button {
      flex: 1; padding: 10px; border-radius: 6px; cursor: pointer;
      font-size: 14px; font-weight: 600; border: none;
    }
    .btn-primary { background: #f59e0b; color: #111827; }
    .btn-primary:hover { background: #fbbf24; }
    .btn-primary:disabled { background: #4b5563; color: #9ca3af; cursor: not-allowed; }
    .btn-cancel { background: #374151; color: #e5e7eb; }
    .btn-cancel:hover { background: #4b5563; }
    .admin-status {
      margin-top: 12px; padding: 8px 12px; border-radius: 6px;
      font-size: 12px; min-height: 18px;
    }
    .admin-status.ok { background: rgba(34,197,94,0.15); color: #86efac; }
    .admin-status.err { background: rgba(239,68,68,0.15); color: #fca5a5; }
    .admin-status.warn { background: rgba(234,179,8,0.15); color: #fcd34d; }
    .admin-help {
      font-size: 11px; color: #6b7280; margin-top: 6px; line-height: 1.5;
    }
    .admin-help a { color: #fbbf24; text-decoration: underline; }
    .new-kw-row { display: none; }
    .new-kw-row.open { display: block; }
  `;
  const styleEl = document.createElement("style");
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ── 토큰 관리 ──────────────────────────────────────────────
  const getToken = () => localStorage.getItem(TOKEN_KEY) || "";
  const setToken = (t) => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);
  const getYtKey = () => localStorage.getItem(YT_KEY) || "";
  const setYtKey = (k) => k ? localStorage.setItem(YT_KEY, k) : localStorage.removeItem(YT_KEY);

  function hasToken() { return !!getToken(); }

  async function promptToken() {
    const cur = getToken();
    const hint = cur ? cur.slice(0, 12) + "..." : "없음";
    const t = prompt(
      "GitHub Personal Access Token 입력.\n" +
        "- github.com/settings/tokens?type=beta 발급\n" +
        "- Repository access: Only select repositories → thumbnail-lab\n" +
        "- Repository permissions → Contents: Read and write\n" +
        "- 빈 값 입력 후 OK = 삭제\n\n" +
        `현재: ${hint}`,
      ""
    );
    if (t === null) return;
    const token = t.trim();
    setToken(token);
    if (!token) {
      alert("토큰 삭제됨");
      updateButtons();
      return;
    }
    const result = await diagnoseToken(token);
    alert(result.msg);
    updateButtons();
  }

  async function promptYtKey() {
    const cur = getYtKey();
    const hint = cur ? cur.slice(0, 12) + "..." : "없음 (oEmbed로만 작동)";
    const k = prompt(
      "YouTube Data API v3 key 입력 (선택사항).\n" +
        "- console.cloud.google.com → APIs & Services → Credentials\n" +
        "- YouTube Data API v3 enable\n" +
        "- 키 입력하면 URL 추가 시 조회수·길이·업로드일 자동 채움\n" +
        "- 비워두면 제목·채널·썸네일만 oEmbed로 채움\n\n" +
        `현재: ${hint}`,
      ""
    );
    if (k === null) return;
    setYtKey(k.trim());
    alert(k.trim() ? "YouTube API 키 저장됨" : "YouTube API 키 삭제됨");
  }

  async function diagnoseToken(token) {
    try {
      const meRes = await fetch("https://api.github.com/user", {
        headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" }
      });
      if (!meRes.ok) return { ok: false, msg: `토큰 무효 (${meRes.status})` };
      const me = await meRes.json();
      const repoRes = await fetch(`https://api.github.com/repos/${REPO}`, {
        headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" }
      });
      if (!repoRes.ok) return { ok: false, msg: `${me.login} 계정. thumbnail-lab repo 접근 불가 (${repoRes.status})` };
      return { ok: true, msg: `✅ ${me.login} - thumbnail-lab 접근 OK` };
    } catch (e) {
      return { ok: false, msg: `진단 실패: ${e.message}` };
    }
  }

  // ── GitHub API ─────────────────────────────────────────────
  function b64encode(s) {
    return btoa(unescape(encodeURIComponent(s)));
  }
  function b64decode(s) {
    return decodeURIComponent(escape(atob(s.replace(/\n/g, ""))));
  }

  async function ghGet(path) {
    const token = getToken();
    const url = `https://api.github.com/repos/${REPO}/contents/${path}?ref=${BRANCH}&t=${Date.now()}`;
    const headers = { Accept: "application/vnd.github+json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(url, { headers, cache: "no-store" });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`GET 실패: ${res.status}`);
    return res.json();
  }

  async function ghPut(path, content, sha, message) {
    const token = getToken();
    if (!token) throw new Error("토큰 없음. 🔑 버튼 눌러 입력");
    const url = `https://api.github.com/repos/${REPO}/contents/${path}`;
    const body = { message, content: b64encode(content), branch: BRANCH };
    if (sha) body.sha = sha;
    const res = await fetch(url, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`PUT 실패 ${res.status}: ${err.slice(0, 200)}`);
    }
    return res.json();
  }

  // ── 비디오 정보 fetch ────────────────────────────────────────
  function parseVideoId(url) {
    const m = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|shorts\/|embed\/))([A-Za-z0-9_-]{11})/);
    return m ? m[1] : null;
  }

  async function fetchOEmbed(videoUrl) {
    const oembedUrl = `https://www.youtube.com/oembed?url=${encodeURIComponent(videoUrl)}&format=json`;
    const res = await fetch(oembedUrl);
    if (!res.ok) throw new Error(`oEmbed 실패: ${res.status}`);
    return res.json();
  }

  async function fetchYtDataApi(videoId) {
    const key = getYtKey();
    if (!key) return null;
    const url = `https://www.googleapis.com/youtube/v3/videos?id=${videoId}&part=snippet,statistics,contentDetails&key=${key}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`YT API 실패: ${res.status}`);
    const j = await res.json();
    if (!j.items?.length) throw new Error("영상을 찾을 수 없음");
    const it = j.items[0];
    const dur = parseIsoDuration(it.contentDetails.duration);
    return {
      id: videoId,
      title: it.snippet.title,
      channel: it.snippet.channelTitle,
      channel_id: it.snippet.channelId,
      views: parseInt(it.statistics.viewCount) || 0,
      duration: dur,
      format: dur <= 70 ? "shorts" : "long",
      upload_date: it.snippet.publishedAt.slice(0, 10).replace(/-/g, ""),
      thumbnail_url: it.snippet.thumbnails.maxres?.url || it.snippet.thumbnails.high?.url || "",
      url: `https://youtu.be/${videoId}`
    };
  }

  function parseIsoDuration(iso) {
    const m = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!m) return 0;
    return (parseInt(m[1] || 0) * 3600) + (parseInt(m[2] || 0) * 60) + parseInt(m[3] || 0);
  }

  // ── 핵심: 삭제 ─────────────────────────────────────────────
  async function deleteVideo(slug, videoId) {
    if (!confirm(`이 영상 카드를 삭제할까?\n키워드: ${slug}\nID: ${videoId}\n\n(GitHub에서 영구 삭제. 복구는 git에서)`)) return;

    try {
      const path = `data/${encodeURIComponent(slug)}.json`;
      const file = await ghGet(path);
      if (!file) throw new Error(`data/${slug}.json 없음`);

      const data = JSON.parse(b64decode(file.content));
      const before = data.videos.length;
      data.videos = data.videos.filter(v => v.id !== videoId);
      if (data.videos.length === before) {
        alert(`해당 영상이 데이터에 없음 (id: ${videoId})`);
        return;
      }
      data.updated = new Date().toISOString().slice(0, 10);

      // 썸네일 파일은 같이 안 지움 (orphan 정리는 별도 스크립트)
      await ghPut(
        path,
        JSON.stringify(data, null, 2),
        file.sha,
        `delete: ${slug} - ${videoId}`
      );

      alert(`✅ 삭제 완료. 사이트 1~2분 후 자동 갱신`);
      // 로컬 즉시 반영
      if (window.thumblabState && window.thumblabState.activeKeyword === slug) {
        window.thumblabState.allVideos = data.videos;
        window.thumblabRender?.();
      }
    } catch (e) {
      alert(`❌ 삭제 실패: ${e.message}`);
    }
  }

  // ── 핵심: 추가 ─────────────────────────────────────────────
  async function addVideo(url, slugChoice, newKeywordName, newCategory) {
    const videoId = parseVideoId(url);
    if (!videoId) throw new Error("유효한 YouTube URL이 아님");

    // 1. 정보 fetch (YT API 우선, 없으면 oEmbed)
    let video;
    const ytKey = getYtKey();
    if (ytKey) {
      try {
        video = await fetchYtDataApi(videoId);
        setModalStatus("✓ YouTube API로 풀 정보 가져옴", "ok");
      } catch (e) {
        setModalStatus(`YT API 실패, oEmbed로 fallback: ${e.message}`, "warn");
        video = null;
      }
    }
    if (!video) {
      const oe = await fetchOEmbed(url);
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      video = {
        id: videoId,
        title: oe.title,
        channel: oe.author_name,
        channel_id: "",
        views: 0,
        duration: 0,
        format: "long",
        upload_date: today,
        thumbnail_url: oe.thumbnail_url,
        url: `https://youtu.be/${videoId}`,
        added_manually: true
      };
      setModalStatus("ℹ oEmbed - 조회수·길이 미수집. YT API 키 설정 또는 collect.py --add-id로 백필 권장", "warn");
    }

    // 2. 키워드 결정
    let slug;
    if (slugChoice === "__new__") {
      if (!newKeywordName) throw new Error("새 키워드 이름 입력 필요");
      slug = newKeywordName.trim().replace(/\s+/g, "-").toLowerCase();
      slug = slug.replace(/[^\w가-힣\-]/g, "");
      if (!slug) throw new Error("유효하지 않은 키워드 이름");
      // keywords.json 갱신
      await addToKeywordsIndex(slug, newKeywordName.trim(), 1, newCategory || "general");
    } else {
      slug = slugChoice;
    }

    // 3. 썸네일 다운로드 (GitHub repo로 직접 PUT은 binary 부담 → 그냥 thumbnail_url로 외부 링크 표시)
    // 카드 렌더링에서 v.thumb 대신 v.thumbnail_url도 fallback으로 처리
    video.thumb = `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`;

    // 4. data/{slug}.json 업데이트
    const path = `data/${encodeURIComponent(slug)}.json`;
    let file = await ghGet(path);
    let data;
    if (file) {
      data = JSON.parse(b64decode(file.content));
      if (data.videos.some(v => v.id === videoId)) {
        throw new Error("이미 추가된 영상");
      }
      data.videos.unshift(video);
    } else {
      // 새 키워드 파일 생성
      data = {
        keyword: newKeywordName || slug,
        slug: slug,
        updated: new Date().toISOString().slice(0, 10),
        videos: [video]
      };
    }
    data.updated = new Date().toISOString().slice(0, 10);

    await ghPut(
      path,
      JSON.stringify(data, null, 2),
      file?.sha,
      `add: ${slug} - ${video.title.slice(0, 40)}`
    );

    return { slug, videoId };
  }

  async function addToKeywordsIndex(slug, keyword, count, category) {
    const path = "data/keywords.json";
    const file = await ghGet(path);
    const today = new Date().toISOString().slice(0, 10);
    let data;
    if (file) {
      data = JSON.parse(b64decode(file.content));
      if (!data.keywords.some(k => k.slug === slug)) {
        data.keywords.push({ slug, keyword, category: category || "general", count, updated: today });
      }
    } else {
      data = { keywords: [{ slug, keyword, category: category || "general", count, updated: today }] };
    }
    await ghPut(path, JSON.stringify(data, null, 2), file?.sha, `add keyword: ${slug}`);
  }

  // ── 모달 UI ────────────────────────────────────────────────
  function createAddModal() {
    const modal = document.createElement("div");
    modal.className = "admin-modal";
    modal.id = "admin-add-modal";
    modal.innerHTML = `
      <div class="admin-modal-box" onclick="event.stopPropagation()">
        <h3>📥 영상 추가</h3>

        <label>YouTube URL</label>
        <input type="text" id="add-url" placeholder="https://youtu.be/... 또는 https://www.youtube.com/watch?v=...">

        <label>키워드 선택</label>
        <select id="add-keyword">
          <option value="">선택...</option>
          <option value="__new__">+ 새 키워드 만들기</option>
        </select>

        <div class="new-kw-row" id="new-kw-row">
          <label>새 키워드 이름</label>
          <input type="text" id="add-new-keyword" placeholder="예: 무료 영상 AI">
          <label>카테고리</label>
          <select id="add-category">
            <option value="ai">🤖 AI 도구</option>
            <option value="shorts">🎬 쇼츠 벤치마킹</option>
            <option value="books">📚 책·자기계발</option>
            <option value="general">📁 기타</option>
          </select>
          <div class="admin-help">공백은 - 로 변환, 특수문자 제거 → slug로 사용</div>
        </div>

        <div class="admin-status" id="add-status"></div>

        <div class="row">
          <button class="btn-cancel" onclick="document.getElementById('admin-add-modal').classList.remove('open')">취소</button>
          <button class="btn-primary" id="add-submit">추가</button>
        </div>

        <div class="admin-help" style="margin-top:14px; padding-top:12px; border-top:1px solid #1f2937">
          <strong>현재 상태:</strong> ${getYtKey() ? "✅ YouTube API 키 설정됨 - 풀 정보 자동" : "⚠ YouTube API 키 미설정 - oEmbed로 제목·채널·썸네일만 자동 (조회수·길이·날짜 0)"}
          <br><br>
          <strong>YT API 키 설정:</strong> 우상단 🎬 버튼
          <br>
          <strong>정확한 정보 백필:</strong> <code>python scripts/collect.py "키워드명" --add-id VIDEO_ID</code>
        </div>
      </div>
    `;
    modal.onclick = () => modal.classList.remove("open");
    document.body.appendChild(modal);

    document.getElementById("add-keyword").onchange = (e) => {
      document.getElementById("new-kw-row").classList.toggle("open", e.target.value === "__new__");
    };

    document.getElementById("add-submit").onclick = async () => {
      const url = document.getElementById("add-url").value.trim();
      const slug = document.getElementById("add-keyword").value;
      const newKw = document.getElementById("add-new-keyword").value.trim();
      const newCat = document.getElementById("add-category").value;
      if (!url) return setModalStatus("URL 입력 필요", "err");
      if (!slug) return setModalStatus("키워드 선택 필요", "err");
      if (slug === "__new__" && !newKw) return setModalStatus("새 키워드 이름 입력 필요", "err");

      const btn = document.getElementById("add-submit");
      btn.disabled = true;
      btn.textContent = "처리 중...";
      setModalStatus("oEmbed 정보 가져오는 중...", "warn");

      try {
        const result = await addVideo(url, slug, newKw, newCat);
        setModalStatus(`✅ 추가 완료 (${result.slug}) - 사이트 1~2분 후 자동 갱신`, "ok");
        // 키워드 인덱스 리로드 트리거
        setTimeout(() => {
          modal.classList.remove("open");
          window.location.reload();
        }, 1500);
      } catch (e) {
        setModalStatus(`❌ ${e.message}`, "err");
      } finally {
        btn.disabled = false;
        btn.textContent = "추가";
      }
    };
  }

  function setModalStatus(msg, type) {
    const el = document.getElementById("add-status");
    if (!el) return;
    el.textContent = msg;
    el.className = "admin-status " + (type || "");
  }

  function openAddModal() {
    if (!hasToken()) {
      alert("먼저 🔑 버튼으로 GitHub 토큰을 설정하세요.");
      return;
    }
    // 키워드 옵션 갱신
    const sel = document.getElementById("add-keyword");
    sel.innerHTML = '<option value="">선택...</option><option value="__new__">+ 새 키워드 만들기</option>';
    const keywords = window.thumblabState?.keywords || [];
    for (const k of keywords) {
      const opt = document.createElement("option");
      opt.value = k.slug;
      opt.textContent = `${k.keyword} (${k.count})`;
      if (k.slug === window.thumblabState.activeKeyword) opt.selected = true;
      sel.insertBefore(opt, sel.querySelector('option[value="__new__"]'));
    }
    document.getElementById("admin-add-modal").classList.add("open");
    document.getElementById("new-kw-row").classList.remove("open");
    document.getElementById("add-status").textContent = "";
    document.getElementById("add-status").className = "admin-status";
    document.getElementById("add-url").value = "";
    document.getElementById("add-url").focus();
  }

  // ── 헤더 버튼 주입 ────────────────────────────────────────
  function injectButtons() {
    const headerContainer = document.querySelector("header .max-w-7xl");
    if (!headerContainer) return;

    const btns = document.createElement("div");
    btns.className = "flex items-center gap-1.5";
    btns.id = "admin-btns";
    btns.innerHTML = `
      <button class="admin-btn" id="admin-token-btn" title="GitHub 토큰">🔑</button>
      <button class="admin-btn" id="admin-yt-btn" title="YouTube API 키">🎬</button>
      <button class="admin-btn" id="admin-add-btn" title="영상 추가">➕</button>
    `;
    headerContainer.appendChild(btns);

    document.getElementById("admin-token-btn").onclick = promptToken;
    document.getElementById("admin-yt-btn").onclick = promptYtKey;
    document.getElementById("admin-add-btn").onclick = openAddModal;

    updateButtons();
  }

  function updateButtons() {
    const tokenBtn = document.getElementById("admin-token-btn");
    if (tokenBtn) tokenBtn.classList.toggle("active", hasToken());
    const ytBtn = document.getElementById("admin-yt-btn");
    if (ytBtn) ytBtn.classList.toggle("active", !!getYtKey());
  }

  // ── 외부 노출 ──────────────────────────────────────────────
  window.thumblabAdmin = {
    hasToken,
    deleteVideo,
    openAddModal,
    promptToken
  };

  // ── 초기화 ────────────────────────────────────────────────
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      injectButtons();
      createAddModal();
    });
  } else {
    injectButtons();
    createAddModal();
  }
})();
