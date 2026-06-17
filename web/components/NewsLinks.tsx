import { Fragment } from "react";
import type { NewsItem } from "@/lib/types";

const MAX_NEWS = 3;

export default function NewsLinks({ news }: { news: NewsItem[] }) {
  if (news.length === 0) {
    return <span className="no-news">뉴스 없음</span>;
  }

  return (
    <>
      {news.slice(0, MAX_NEWS).map((n, i) => (
        <Fragment key={`${n.link}-${i}`}>
          <a
            href={n.link}
            target="_blank"
            rel="noopener noreferrer"
            className="news-link"
          >
            {n.isNew && <span className="new-tag">NEW</span>}
            {n.title}
          </a>
          <span className="news-date">{n.date}</span>
        </Fragment>
      ))}
    </>
  );
}
