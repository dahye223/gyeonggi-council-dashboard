#!/usr/bin/env python3
"""경기도의회 당선자 뉴스 대시보드 생성 스크립트 (GitHub Actions용)

루트의 candidates.json(당선자 + 미리 수집된 뉴스)을 읽어 index.html을 생성한다.
뉴스 수집은 별도 단계(스케줄 작업)에서 수행되어 candidates.json에 반영된다.
"""
import json, os, html
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
update_time = datetime.now(KST).strftime('%Y년 %m월 %d일 %H:%M KST')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

with open(os.path.join(REPO_ROOT, 'candidates.json'), encoding='utf-8') as f:
    data = json.load(f)

members = data.get('당선자', [])
total = len(members)
with_news = sum(1 for m in members if m.get('뉴스'))
total_news = sum(len(m.get('뉴스', [])) for m in members)

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
    # candidates.json은 제목만 보관(본문 없음)하므로, 제목에 당선자 이름이
    # 실제로 포함된 기사를 우선 노출한다. '경기도의회 전체' 류 일반 기사는
    # 이름이 들어간 기사 뒤로 밀린다. 안정 정렬이라 그룹 내 기존(날짜) 순서는 유지.
    if name:
        news = sorted(news, key=lambda n: 0 if name in (n.get('제목') or '') else 1)
    has_news = bool(news)
    if has_news:
        items = ''
        for n in news[:3]:
            items += (f'<a href="{esc(n.get("링크",""))}" target="_blank" class="news-link">'
                      f'{esc(n.get("제목",""))}</a>'
                      f'<span class="news-date">{esc(n.get("날짜",""))}</span>')
        news_html = items
    else:
        news_html = '<span class="no-news">뉴스 없음</span>'
    type_tag = '비례' if mtype == '비례' else '지역구'
    rows += f'''<tr data-city="{esc(city)}" data-party="{esc(party)}" data-type="{esc(mtype)}" data-has-news="{'true' if has_news else 'false'}">
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
</style>
</head>
<body>
<div class="header">
  <h1>🏛 경기도의회 당선자 뉴스 대시보드</h1>
  <div class="meta">제9회 전국동시지방선거(2026-06-03) 당선자 &nbsp;|&nbsp; 자동 업데이트: {update_time} &nbsp;|&nbsp; 총 {total}명 &nbsp;|&nbsp; 뉴스 있음 {with_news}명 / {total_news}건</div>
</div>
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
  const rows = document.querySelectorAll('#tbody tr');
  let shown = 0;
  rows.forEach(r => {{
    const text = r.textContent.toLowerCase();
    const match = (!q || text.includes(q)) &&
      (!city || r.dataset.city === city) &&
      (!party || r.dataset.party === party) &&
      (!type || r.dataset.type === type) &&
      (!news || r.dataset.hasNews === news);
    r.classList.toggle('hidden', !match);
    if (match) shown++;
  }});
  document.getElementById('stats').textContent = shown + '명 표시 중';
}}
['search','cityFilter','partyFilter','typeFilter','newsFilter'].forEach(id => {{
  document.getElementById(id).addEventListener('input', filterTable);
}});
filterTable();
</script>
</body>
</html>'''

with open(os.path.join(REPO_ROOT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html_out)
print(f"index.html 저장 완료: 당선자 {total}명, 뉴스 {total_news}건")
