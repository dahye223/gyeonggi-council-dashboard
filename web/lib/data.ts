import "server-only";
import fs from "node:fs";
import path from "node:path";
import type { Candidate, CandidateType, DashboardData, NewsItem } from "./types";

interface RawNews {
  제목?: string;
  링크?: string;
  날짜?: string;
}

interface RawCandidate {
  이름?: string;
  선거구?: string;
  시군?: string;
  정당?: string;
  득표율?: string;
  유형?: string;
  행정동?: string;
  뉴스?: RawNews[];
}

interface RawData {
  업데이트일시?: string;
  기준?: string;
  당선자?: RawCandidate[];
}

// candidates.json is maintained at the repo root by the existing Python pipeline.
// Depending on the build context (local dev, Vercel root=web, or a copy inside
// web/), it may sit one level up or alongside the app — resolve the first match.
const DATA_CANDIDATES = [
  path.join(process.cwd(), "candidates.json"),
  path.join(process.cwd(), "..", "candidates.json"),
];

function resolveDataPath(): string {
  const found = DATA_CANDIDATES.find((p) => fs.existsSync(p));
  if (!found) {
    throw new Error(
      `candidates.json not found. Looked in: ${DATA_CANDIDATES.join(", ")}`,
    );
  }
  return found;
}

function mapNews(news: RawNews[] | undefined): NewsItem[] {
  return (news ?? []).map((n) => ({
    title: n.제목 ?? "",
    link: n.링크 ?? "",
    date: n.날짜 ?? "",
  }));
}

function mapCandidate(c: RawCandidate): Candidate {
  const type: CandidateType = c.유형 === "비례" ? "비례" : "지역구";
  return {
    name: c.이름 ?? "",
    district: c.선거구 ?? "",
    city: c.시군 ?? "",
    party: c.정당 ?? "",
    rate: c.득표율 ?? "",
    type,
    dong: c.행정동 ?? "",
    news: mapNews(c.뉴스),
  };
}

export function getDashboardData(): DashboardData {
  const raw = JSON.parse(fs.readFileSync(resolveDataPath(), "utf-8")) as RawData;
  const candidates = (raw.당선자 ?? []).map(mapCandidate);

  const withNews = candidates.filter((c) => c.news.length > 0).length;
  const totalNews = candidates.reduce((sum, c) => sum + c.news.length, 0);

  const cities = [...new Set(candidates.map((c) => c.city))].sort((a, b) =>
    a.localeCompare(b, "ko"),
  );
  const parties = [...new Set(candidates.map((c) => c.party))].sort((a, b) =>
    a.localeCompare(b, "ko"),
  );

  return {
    updatedAt: raw.업데이트일시 ?? "",
    basis: raw.기준 ?? "",
    total: candidates.length,
    withNews,
    totalNews,
    candidates,
    cities,
    parties,
  };
}
