#!/usr/bin/env python3
"""경기도의회 당선자 뉴스 대시보드 생성 스크립트 (GitHub Actions용)

루트의 candidates.json(당선자 + 미리 수집된 뉴스)을 읽어 index.html을 생성한다.
뉴스 수집은 별도 단계(스케줄 작업)에서 수행되어 candidates.json에 반영된다.
"""
import json, os, html, hashlib, sys
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
update_time = datetime.now(KST).strftime('%Y년 %m월 %d일 %H:%M KST')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

# candidates.json 원문(바이트)을 그대로 읽어 해시를 계산한다. 데이터가 바뀌지
# 않은 날에는 재생성을 건너뛰어, 의미 없는 커밋·배포(빌드)가 발생하지 않게 한다.
with open(os.path.join(REPO_ROOT, 'candidates.json'), 'rb') as f:
    raw_bytes = f.read()
data = json.loads(raw_bytes.decode('utf-8'))
data_hash = hashlib.sha256(raw_bytes).hexdigest()

members = data.get('당선자', [])
total = len(members)
with_news = sum(1 for m in members if m.get('뉴스'))
total_news = sum(len(m.get('뉴스', [])) for m in members)

# --- 신규 업데이트 감지: 직전 생성 시점과 비교 -------------------------------
# scripts/news_state.json에 당선자별로 '이미 본 뉴스 링크'를 저장해 두고,
# 이번 candidates.json과 비교해 새로 추가된 기사/당선자를 가려낸다.
# 최초 실행(상태 파일 없음)은 기준선이므로 아무것도 신규로 표시하지 않는다.
STATE_PATH = os.path.join(SCRIPT_DIR, 'news_state.json')
today = datetime.now(KST).strftime('%Y-%m-%d')

def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding='utf-8') as sf:
                return json.load(sf)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

prev_state = load_state()
prev_seen = prev_state.get('seen', {})
first_run = not prev_seen  # 상태 파일이 비어 있으면 최초 실행

# 데이터가 직전과 동일하면 아무것도 다시 쓰지 않고 종료한다(파일 미변경 → 커밋
# 없음 → Vercel 재배포 없음). 시각만 바뀐 무의미한 일일 빌드를 막는 핵심 장치.
if not first_run and prev_state.get('data_hash') == data_hash:
    print('candidates.json 변경 없음 - 재생성 건너뜀 (커밋/배포 없음)')
    sys.exit(0)

def cand_key(m):
    return f"{m.get('이름','')}|{m.get('선거구','')}"

def news_links(m):
    return [n.get('링크', '') for n in (m.get('뉴스', []) or []) if n.get('링크')]

# 당선자별 신규 링크 집합과 신규 여부를 미리 계산
new_seen = {}
new_link_sets = {}      # key -> set(새 링크)
new_candidates = set()  # 이전에 없던 당선자 key
for m in members:
    key = cand_key(m)
    cur_links = news_links(m)
    new_seen[key] = cur_links
    if first_run:
        new_link_sets[key] = set()
        continue
    prev_links = set(prev_seen.get(key, []))
    new_link_sets[key] = {l for l in cur_links if l not in prev_links}
    if key not in prev_seen and cur_links:
        new_candidates.add(key)

def is_new_candidate(m):
    key = cand_key(m)
    return bool(new_link_sets.get(key)) or key in new_candidates

updated_count = sum(1 for m in members if is_new_candidate(m))
new_article_count = sum(len(s) for s in new_link_sets.values())

PARTY_COLORS = {
    '더불어민주당': '#0052A5',
    '국민의힘': '#E61E2B',
    '개혁신당': '#FF7210',
    '진보당': '#D6001C',
    '조국혁신당': '#003C8F',
    '무소속': '#888888',
}

def esc(s):
    return html.escape(str(s or ''))

def party_badge(party):
    color = PARTY_COLORS.get(party, '#888888')
    return f'<span class="badge" style="background:{color}">{esc(party)}</span>'

rows = ''
for m in members:
    name = m.get('이름', '')
    sgg = m.get('선거구', '')
    city = m.get('시군', '')
    party = m.get('정당', '')
    rate = m.get('득표율', '')
    mtype = m.get('유형', '')
    news = m.get('뉴스', []) or []
    new_links = new_link_sets.get(cand_key(m), set())
    cand_new = is_new_candidate(m)
    # 정렬 우선순위:
    #  1) 제목에 당선자 이름이 포함된 기사 (관련성) — '경기도의회 전체' 류는 뒤로
    #  2) 그 안에서 새로 추가된(NEW) 기사 — 신규 소식을 상위로 부각
    # 안정 정렬이라 동일 그룹 내 기존(날짜) 순서는 유지된다.
    if news:
        news = sorted(
            news,
            key=lambda n: (
                0 if name and name in (n.get('제목') or '') else 1,
                0 if n.get('링크', '') in new_links else 1,
            ),
        )
    has_news = bool(news)
    if has_news:
        items = ''
        for n in news[:3]:
            link = n.get('링크', '')
            badge = '<span class="new-tag">NEW</span>' if link in new_links else ''
            items += (f'<a href="{esc(link)}" target="_blank" class="news-link">'
                      f'{badge}{esc(n.get("제목",""))}</a>'
                      f'<span class="news-date">{esc(n.get("날짜",""))}</span>')
        news_html = items
    else:
        news_html = '<span class="no-news">뉴스 없음</span>'
    type_tag = '비례' if mtype == '비례' else '지역구'
    row_cls = 'is-new' if cand_new else ''
    rows += f'''<tr class="{row_cls}" data-city="{esc(city)}" data-party="{esc(party)}" data-type="{esc(mtype)}" data-has-news="{'true' if has_news else 'false'}" data-new="{'true' if cand_new else 'false'}">
      <td>{esc(city)}</td>
      <td>{esc(sgg)}<span class="type-tag">{type_tag}</span></td>
      <td class="name-cell">{esc(name)}</td>
      <td>{party_badge(party)}</td>
      <td class="rate-cell">{esc(rate)}</td>
      <td class="news-cell">{news_html}</td>
    </tr>'''

cities = sorted(set(m.get('시군', '') for m in members))
city_opts = '<option value="">전체 시·군</option>' + ''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in cities)
parties = sorted(set(m.get('정당', '') for m in members))
party_opts = '<option value="">전체 정당</option>' + ''.join(f'<option value="{esc(p)}">{esc(p)}</option>' for p in parties)

# 상단 요약 배너 (신규 업데이트가 있을 때만 노출)
if updated_count > 0:
    banner_html = (
        '<div class="banner" id="banner">'
        '<span class="banner-dot"></span>'
        f'<span><strong>오늘 새 소식</strong> &nbsp;업데이트된 당선자 '
        f'{updated_count}명 · 새 기사 {new_article_count}건</span>'
        "<button class=\"banner-x\" onclick=\"document.getElementById('banner').remove()\">&times;</button>"
        '</div>'
    )
else:
    banner_html = ''

html_out = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>경기도의회 당선자 뉴스 대시보드</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", sans-serif; background: #f5f7fa; color: #1a1a2e; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 24px 32px; }}
.header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
.header .meta {{ font-size: 12px; opacity: 0.75; margin-top: 6px; }}
.controls {{ background: white; border-bottom: 1px solid #e8eaed; padding: 16px 32px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
.controls input {{ padding: 8px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; min-width: 200px; }}
.controls select {{ padding: 8px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; background: white; cursor: pointer; }}
.controls .stats {{ margin-left: auto; font-size: 12px; color: #6b7280; }}
table {{ width: 100%; border-collapse: collapse; background: white; }}
th {{ padding: 12px 14px; text-align: left; font-weight: 600; font-size: 12px; letter-spacing: 0.3px; white-space: nowrap; background: #f8fafc; border-bottom: 2px solid #e2e8f0; color: #475569; }}
td {{ padding: 11px 14px; border-bottom: 1px solid #f1f5f9; font-size: 13px; vertical-align: top; }}
tr:hover td {{ background: #f8faff; }}
.badge {{ display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600; color: white; white-space: nowrap; }}
.name-cell {{ font-weight: 700; }}
.rate-cell {{ color: #475569; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.type-tag {{ display: inline-block; margin-left: 6px; padding: 1px 7px; border-radius: 6px; font-size: 10px; font-weight: 600; background: #eef2ff; color: #4338ca; vertical-align: middle; }}
.news-cell {{ max-width: 460px; }}
.news-link {{ color: #1d4ed8; text-decoration: none; font-size: 12.5px; display: block; line-height: 1.45; margin-top: 4px; }}
.news-link:first-child {{ margin-top: 0; }}
.news-link:hover {{ text-decoration: underline; }}
.news-date {{ font-size: 11px; color: #94a3b8; display: block; margin-bottom: 6px; }}
.no-news {{ color: #cbd5e1; font-size: 12px; }}
.table-wrap {{ overflow-x: auto; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 20px 24px; }}
tr.hidden {{ display: none; }}
.footer {{ text-align: center; font-size: 11px; color: #9ca3af; padding: 8px 0 28px; }}
.new-tag {{ display: inline-block; margin-right: 6px; padding: 0 6px; border-radius: 6px; font-size: 10px; font-weight: 700; background: #ef4444; color: white; vertical-align: middle; letter-spacing: 0.3px; }}
tr.is-new td {{ background: #fff7ed; }}
tr.is-new:hover td {{ background: #ffedd5; }}
tr.is-new td:first-child {{ box-shadow: inset 3px 0 0 #f97316; }}
.banner {{ display: flex; align-items: center; gap: 10px; background: #fff7ed; border-bottom: 1px solid #fed7aa; color: #9a3412; padding: 11px 32px; font-size: 13px; }}
.banner-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #f97316; flex-shrink: 0; }}
.banner strong {{ font-weight: 700; }}
.banner-x {{ margin-left: auto; background: none; border: none; font-size: 18px; line-height: 1; color: #9a3412; cursor: pointer; padding: 0 4px; }}
.controls .check {{ display: flex; align-items: center; gap: 6px; font-size: 13px; color: #374151; cursor: pointer; user-select: none; }}
.controls .check input {{ min-width: auto; width: 15px; height: 15px; cursor: pointer; }}
</style>
</head>
<body>
<div class="header">
  <h1>🏛 경기도의회 당선자 뉴스 대시보드</h1>
  <div class="meta">제9회 전국동시지방선거(2026-06-03) 당선자 &nbsp;|&nbsp; 자동 업데이트: {update_time} &nbsp;|&nbsp; 총 {total}명 &nbsp;|&nbsp; 뉴스 있음 {with_news}명 / {total_news}건</div>
</div>
{banner_html}
<div class="controls">
  <input type="text" id="search" placeholder="당선자 이름 또는 선거구 검색...">
  <select id="cityFilter">{city_opts}</select>
  <select id="partyFilter">{party_opts}</select>
  <select id="typeFilter">
    <option value="">전체 유형</option>
    <option value="지역구">지역구</option>
    <option value="비례">비례</option>
  </select>
  <select id="newsFilter">
    <option value="">전체</option>
    <option value="true">뉴스 있음</option>
    <option value="false">뉴스 없음</option>
  </select>
  <label class="check"><input type="checkbox" id="newOnly"> 오늘 새 소식만</label>
  <span class="stats" id="stats">{total}명 표시 중</span>
</div>
<div class="table-wrap">
<table id="mainTable">
<thead><tr>
  <th>시·군</th><th>선거구</th><th>당선자</th><th>정당</th><th>득표율</th><th>관련 뉴스</th>
</tr></thead>
<tbody id="tbody">
{rows}
</tbody>
</table>
</div>
<div class="footer">데이터: 중앙선거관리위원회 · 네이버 뉴스 · 경기도의회</div>
<script>
function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  const city = document.getElementById('cityFilter').value;
  const party = document.getElementById('partyFilter').value;
  const type = document.getElementById('typeFilter').value;
  const news = document.getElementById('newsFilter').value;
  const newOnly = document.getElementById('newOnly').checked;
  const rows = document.querySelectorAll('#tbody tr');
  let shown = 0;
  rows.forEach(r => {{
    const text = r.textContent.toLowerCase();
    const match = (!q || text.includes(q)) &&
      (!city || r.dataset.city === city) &&
      (!party || r.dataset.party === party) &&
      (!type || r.dataset.type === type) &&
      (!news || r.dataset.hasNews === news) &&
      (!newOnly || r.dataset.new === 'true');
    r.classList.toggle('hidden', !match);
    if (match) shown++;
  }});
  document.getElementById('stats').textContent = shown + '명 표시 중';
}}
['search','cityFilter','partyFilter','typeFilter','newsFilter'].forEach(id => {{
  document.getElementById(id).addEventListener('input', filterTable);
}});
document.getElementById('newOnly').addEventListener('change', filterTable);
filterTable();
</script>
</body>
</html>'''

with open(os.path.join(REPO_ROOT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html_out)

# 다음 실행 때 비교할 수 있도록 현재 본 뉴스 링크 상태를 저장한다.
# last_new는 Next.js 앱이 동일한 '신규' 표시를 재현할 때 사용한다.
new_links_all = sorted({l for s in new_link_sets.values() for l in s})
state_out = {
    'last_run': today,
    'data_hash': data_hash,
    'updated_candidates': updated_count,
    'new_articles': new_article_count,
    'last_new_links': new_links_all,
    'seen': new_seen,
}
with open(STATE_PATH, 'w', encoding='utf-8') as f:
    json.dump(state_out, f, ensure_ascii=False, indent=2)

print(f"index.html 저장 완료: 당선자 {total}명, 뉴스 {total_news}건")
print(f"신규: 업데이트 당선자 {updated_count}명, 새 기사 {new_article_count}건 (first_run={first_run})")
