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

interface NewsState {
  updated_candidates?: number;
  new_articles?: number;
  last_new_links?: string[];
}

function resolveFirst(candidates: string[]): string | null {
  return candidates.find((p) => fs.existsSync(p)) ?? null;
}

// candidates.json is maintained at the repo root by the existing Python pipeline.
// Depending on the build context (local dev, Vercel root=web, or a copy inside
// web/), it may sit one level up or alongside the app — resolve the first match.
function resolveDataPath(): string {
  const found = resolveFirst([
    path.join(process.cwd(), "candidates.json"),
    path.join(process.cwd(), "..", "candidates.json"),
  ]);
  if (!found) {
    throw new Error("candidates.json not found near the working directory");
  }
  return found;
}

// news_state.json is written by scripts/generate.py and records which article
// links were newly added in the most recent update. The Next.js app reuses it
// so the "신규(NEW)" highlighting matches the static (index.html) site exactly.
function loadNewsState(): NewsState {
  const found = resolveFirst([
    path.join(process.cwd(), "scripts", "news_state.json"),
    path.join(process.cwd(), "..", "scripts", "news_state.json"),
  ]);
  if (!found) return {};
  try {
    return JSON.parse(fs.readFileSync(found, "utf-8")) as NewsState;
  } catch {
    return {};
  }
}

function mapNews(
  news: RawNews[] | undefined,
  newLinks: Set<string>,
): NewsItem[] {
  return (news ?? []).map((n) => ({
    title: n.제목 ?? "",
    link: n.링크 ?? "",
    date: n.날짜 ?? "",
    isNew: newLinks.has(n.링크 ?? ""),
  }));
}

// Sort priority (stable, preserving original date order within a group):
//  1) headline mentions the candidate by name (relevance) — generic
//     "경기도의회 전체" coverage drops below name-specific articles
//  2) newly added (NEW) articles surface to the top so fresh news stands out
function prioritizeNews(news: NewsItem[], name: string): NewsItem[] {
  const mentionsName = (n: NewsItem) => Boolean(name) && n.title.includes(name);
  return [...news].sort((a, b) => {
    const nameDelta = Number(mentionsName(b)) - Number(mentionsName(a));
    if (nameDelta !== 0) return nameDelta;
    return Number(b.isNew) - Number(a.isNew);
  });
}

function mapCandidate(c: RawCandidate, newLinks: Set<string>): Candidate {
  const type: CandidateType = c.유형 === "비례" ? "비례" : "지역구";
  const name = c.이름 ?? "";
  const news = prioritizeNews(mapNews(c.뉴스, newLinks), name);
  return {
    name,
    district: c.선거구 ?? "",
    city: c.시군 ?? "",
    party: c.정당 ?? "",
    rate: c.득표율 ?? "",
    type,
    dong: c.행정동 ?? "",
    news,
    isNew: news.some((n) => n.isNew),
  };
}

export function getDashboardData(): DashboardData {
  const raw = JSON.parse(fs.readFileSync(resolveDataPath(), "utf-8")) as RawData;
  const state = loadNewsState();
  const newLinks = new Set(state.last_new_links ?? []);

  const candidates = (raw.당선자 ?? []).map((c) => mapCandidate(c, newLinks));

  const withNews = candidates.filter((c) => c.news.length > 0).length;
  const totalNews = candidates.reduce((sum, c) => sum + c.news.length, 0);

  const cities = [...new Set(candidates.map((c) => c.city))].sort((a, b) =>
    a.localeCompare(b, "ko"),
  );
  const parties = [...new Set(candidates.map((c) => c.party))].sort((a, b) =>
    a.localeCompare(b, "ko"),
  );

  const updatedCandidates =
    state.updated_candidates ?? candidates.filter((c) => c.isNew).length;
  const newArticles =
    state.new_articles ??
    candidates.reduce((s, c) => s + c.news.filter((n) => n.isNew).length, 0);

  return {
    updatedAt: raw.업데이트일시 ?? "",
    basis: raw.기준 ?? "",
    total: candidates.length,
    withNews,
    totalNews,
    candidates,
    cities,
    parties,
    updatedCandidates,
    newArticles,
  };
}
