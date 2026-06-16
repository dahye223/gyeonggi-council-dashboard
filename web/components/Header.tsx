interface HeaderProps {
  updatedAt: string;
  total: number;
  withNews: number;
  totalNews: number;
}

export default function Header({
  updatedAt,
  total,
  withNews,
  totalNews,
}: HeaderProps) {
  return (
    <div className="header">
      <h1>🏛 경기도의회 당선자 뉴스 대시보드</h1>
      <div className="meta">
        제9회 전국동시지방선거(2026-06-03) 당선자 &nbsp;|&nbsp; 자동 업데이트:{" "}
        {updatedAt} &nbsp;|&nbsp; 총 {total}명 &nbsp;|&nbsp; 뉴스 있음 {withNews}
        명 / {totalNews}건
      </div>
    </div>
  );
}
