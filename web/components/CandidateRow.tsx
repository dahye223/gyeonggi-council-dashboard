import type { Candidate } from "@/lib/types";
import PartyBadge from "./PartyBadge";
import NewsLinks from "./NewsLinks";

export default function CandidateRow({ candidate }: { candidate: Candidate }) {
  return (
    <tr>
      <td>{candidate.city}</td>
      <td>
        {candidate.district}
        <span className="type-tag">{candidate.type}</span>
      </td>
      <td className="name-cell">{candidate.name}</td>
      <td>
        <PartyBadge party={candidate.party} />
      </td>
      <td className="rate-cell">{candidate.rate}</td>
      <td className="news-cell">
        <NewsLinks news={candidate.news} />
      </td>
    </tr>
  );
}
