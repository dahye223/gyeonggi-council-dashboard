#!/usr/bin/env python3
"""경기도의회 당선자 뉴스 수집 스크립트 (GitHub Actions용)

네이버 검색 API(뉴스)를 이용해 candidates.json의 당선자별 '뉴스' 항목을
매일 갱신한다. 표준 라이브러리만 사용하므로 별도 pip 설치가 필요 없다.

필요 환경변수 (GitHub Actions Secret 으로 주입):
  - NAVER_CLIENT_ID
  - NAVER_CLIENT_SECRET
자격증명이 없으면 수집을 건너뛰고(종료코드 0) 기존 데이터를 유지한다.
이렇게 해야 키를 등록하기 전이라도 워크플로(생성·배포)는 깨지지 않는다.

수집 로직(기존 대시보드 로직과 동일한 기준):
  1) 당선자 이름으로 뉴스 검색(최신순)
  2) 제목 또는 본문에 이름이 실제로 포함된 기사만 채택(무관 기사 제거)
  3) 제목에 이름이 든 기사 + 의회/정치 맥락 기사를 우선해 상위 3건만 저장
     (동일 우선순위 안에서는 최신순)
"""
import json
import os
import sys
import time
import html
import re
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import timezone, timedelta

KST = timezone(timedelta(hours=9))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(REPO_ROOT, 'candidates.json')

API_URL = 'https://openapi.naver.com/v1/search/news.json'
DISPLAY = 20          # 후보별로 가져올 검색 결과 수(채택 전 풀)
KEEP = 3              # 후보별로 저장할 최종 기사 수(기존 데이터와 동일)
SLEEP_SEC = 0.1       # 호출 간 간격(API 예의상)

CLIENT_ID = os.environ.get('NAVER_CLIENT_ID', '').strip()
CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', '').strip()

TAG_RE = re.compile(r'<[^>]+>')


def clean(text: str) -> str:
    """네이버가 돌려주는 제목의 <b> 태그와 HTML 엔티티를 제거한다."""
    return html.unescape(TAG_RE.sub('', text or '')).strip()


def to_date(pub_date: str) -> str:
    """RFC822 형식(pubDate)을 KST 기준 YYYY-MM-DD로 변환한다."""
    try:
        dt = parsedate_to_datetime(pub_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(KST).strftime('%Y-%m-%d')
    except (TypeError, ValueError):
        return ''


def search_news(query: str):
    """네이버 뉴스 검색 API를 호출해 items 리스트를 반환한다."""
    params = urllib.parse.urlencode({
        'query': query,
        'display': DISPLAY,
        'sort': 'date',   # 최신순
    })
    req = urllib.request.Request(f'{API_URL}?{params}')
    req.add_header('X-Naver-Client-Id', CLIENT_ID)
    req.add_header('X-Naver-Client-Secret', CLIENT_SECRET)
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    return payload.get('items', [])


def collect_for(member: dict):
    """한 당선자에 대해 뉴스 3건을 수집한다. 실패 시 None 반환(기존 유지)."""
    name = (member.get('이름') or '').strip()
    if not name:
        return None

    try:
        items = search_news(name)
    except Exception as e:  # 네트워크/쿼터 오류 등 — 해당 후보만 건너뜀
        print(f'  ! {name}: 검색 실패 ({e}) - 기존 뉴스 유지')
        return None

    # 동명이인/무관 기사를 줄이기 위한 맥락 키워드
    context = [c for c in [
        '경기도의회', '도의원', '도의회', '의원', '경기도',
        member.get('시군', ''), member.get('정당', ''),
    ] if c]

    seen_links = set()
    scored = []
    for it in items:
        title = clean(it.get('title', ''))
        desc = clean(it.get('description', ''))
        link = (it.get('originallink') or it.get('link') or '').strip()
        if not link or not title or link in seen_links:
            continue
        blob = f'{title} {desc}'
        if name not in blob:           # 이름이 실제로 안 나오면 무관 기사로 보고 제외
            continue
        has_context = any(k in blob for k in context)
        if not has_context:            # 의회/정치 맥락이 전혀 없으면 동명이인 가능성 → 제외
            continue
        seen_links.add(link)
        score = (2 if name in title else 0) + (1 if has_context else 0)
        scored.append({
            'score': score,
            'date': to_date(it.get('pubDate', '')),
            'item': {'제목': title, '링크': link, '날짜': to_date(it.get('pubDate', ''))},
        })

    if not scored:
        return []

    # 우선순위: 점수 높은 순(제목 이름 포함 + 맥락) → 최신순
    # 날짜는 YYYY-MM-DD 문자열이라 내림차순 정렬이 곧 최신순이다.
    scored.sort(key=lambda x: (x['score'], x['date']), reverse=True)
    return [s['item'] for s in scored[:KEEP]]


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print('NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정 - 수집 건너뜀(기존 데이터 유지)')
        return 0

    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)

    members = data.get('당선자', [])
    print(f'당선자 {len(members)}명 뉴스 수집 시작...')

    updated, kept, failed = 0, 0, 0
    for i, m in enumerate(members, 1):
        result = collect_for(m)
        if result is None:        # 검색 실패 — 기존 뉴스 보존
            failed += 1
        else:
            m['뉴스'] = result
            updated += 1
            kept += len(result)
        if i % 25 == 0:
            print(f'  ...{i}/{len(members)} 진행')
        time.sleep(SLEEP_SEC)

    # 업데이트 일시 갱신
    from datetime import datetime
    data['업데이트일시'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M KST')

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'수집 완료: 갱신 {updated}명 / 실패(기존유지) {failed}명 / 뉴스 {kept}건')
    return 0


if __name__ == '__main__':
    sys.exit(main())
