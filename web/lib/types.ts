export type CandidateType = "지역구" | "비례";

export interface NewsItem {
  title: string;
  link: string;
  date: string;
}

export interface Candidate {
  name: string;
  district: string;
  city: string;
  party: string;
  rate: string;
  type: CandidateType;
  dong: string;
  news: NewsItem[];
}

export interface DashboardData {
  updatedAt: string;
  basis: string;
  total: number;
  withNews: number;
  totalNews: number;
  candidates: Candidate[];
  cities: string[];
  parties: string[];
}
