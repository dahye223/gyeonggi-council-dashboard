import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "경기도의회 당선자 뉴스 대시보드",
  description:
    "제9회 전국동시지방선거(2026-06-03) 경기도의회 당선자 뉴스 대시보드",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
