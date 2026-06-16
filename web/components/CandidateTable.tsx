import type { Candidate } from "@/lib/types";
import CandidateRow from "./CandidateRow";

export default function CandidateTable({
  candidates,
}: {
  candidates: Candidate[];
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>시·군</th>
            <th>선거구</th>
            <th>당선자</th>
            <th>정당</th>
            <th>득표율</th>
            <th>관련 뉴스</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c, i) => (
            <CandidateRow key={`${c.name}-${c.district}-${i}`} candidate={c} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
