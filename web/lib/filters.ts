import type { Candidate } from "./types";

export interface Filters {
  query: string;
  city: string;
  party: string;
  type: string;
  news: string;
}

export const EMPTY_FILTERS: Filters = {
  query: "",
  city: "",
  party: "",
  type: "",
  news: "",
};

function candidateText(c: Candidate): string {
  return [
    c.name,
    c.district,
    c.city,
    c.party,
    c.rate,
    ...c.news.flatMap((n) => [n.title, n.date]),
  ]
    .join(" ")
    .toLowerCase();
}

export function matchesFilters(c: Candidate, f: Filters): boolean {
  const q = f.query.trim().toLowerCase();
  const hasNews = c.news.length > 0;
  return (
    (!q || candidateText(c).includes(q)) &&
    (!f.city || c.city === f.city) &&
    (!f.party || c.party === f.party) &&
    (!f.type || c.type === f.type) &&
    (!f.news || String(hasNews) === f.news)
  );
}
