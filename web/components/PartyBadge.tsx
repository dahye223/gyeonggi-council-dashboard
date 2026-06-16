import { partyColor } from "@/lib/constants";

export default function PartyBadge({ party }: { party: string }) {
  return (
    <span className="badge" style={{ background: partyColor(party) }}>
      {party}
    </span>
  );
}
