"use client";

import type { Filters } from "@/lib/filters";

interface ControlsProps {
  filters: Filters;
  onChange: (patch: Partial<Filters>) => void;
  cities: string[];
  parties: string[];
  shownCount: number;
}

export default function Controls({
  filters,
  onChange,
  cities,
  parties,
  shownCount,
}: ControlsProps) {
  return (
    <div className="controls">
      <input
        type="text"
        placeholder="당선자 이름 또는 선거구 검색..."
        value={filters.query}
        onChange={(e) => onChange({ query: e.target.value })}
      />
      <select
        value={filters.city}
        onChange={(e) => onChange({ city: e.target.value })}
      >
        <option value="">전체 시·군</option>
        {cities.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <select
        value={filters.party}
        onChange={(e) => onChange({ party: e.target.value })}
      >
        <option value="">전체 정당</option>
        {parties.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>
      <select
        value={filters.type}
        onChange={(e) => onChange({ type: e.target.value })}
      >
        <option value="">전체 유형</option>
        <option value="지역구">지역구</option>
        <option value="비례">비례</option>
      </select>
      <select
        value={filters.news}
        onChange={(e) => onChange({ news: e.target.value })}
      >
        <option value="">전체</option>
        <option value="true">뉴스 있음</option>
        <option value="false">뉴스 없음</option>
      </select>
      <label className="check">
        <input
          type="checkbox"
          checked={filters.newOnly}
          onChange={(e) => onChange({ newOnly: e.target.checked })}
        />
        오늘 새 소식만
      </label>
      <span className="stats">{shownCount}명 표시 중</span>
    </div>
  );
}
