"use client";

import { useMemo, useState } from "react";
import type { DashboardData } from "@/lib/types";
import { EMPTY_FILTERS, matchesFilters, type Filters } from "@/lib/filters";
import Header from "./Header";
import Controls from "./Controls";
import CandidateTable from "./CandidateTable";

export default function Dashboard({ data }: { data: DashboardData }) {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);

  const visible = useMemo(
    () => data.candidates.filter((c) => matchesFilters(c, filters)),
    [data.candidates, filters],
  );

  const onChange = (patch: Partial<Filters>) =>
    setFilters((prev) => ({ ...prev, ...patch }));

  return (
    <>
      <Header
        updatedAt={data.updatedAt}
        total={data.total}
        withNews={data.withNews}
        totalNews={data.totalNews}
      />
      <Controls
        filters={filters}
        onChange={onChange}
        cities={data.cities}
        parties={data.parties}
        shownCount={visible.length}
      />
      <CandidateTable candidates={visible} />
      <div className="footer">
        데이터: 중앙선거관리위원회 · 네이버 뉴스 · 경기도의회
      </div>
    </>
  );
}
