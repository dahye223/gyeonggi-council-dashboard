export const PARTY_COLORS: Record<string, string> = {
  더불어민주당: "#0052A5",
  국민의힘: "#E61E2B",
  개혁신당: "#FF7210",
  진보당: "#D6001C",
  조국혁신당: "#003C8F",
  무소속: "#888888",
};

export const DEFAULT_PARTY_COLOR = "#888888";

export function partyColor(party: string): string {
  return PARTY_COLORS[party] ?? DEFAULT_PARTY_COLOR;
}
