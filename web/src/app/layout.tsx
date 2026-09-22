import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinGuide AI",
  description: "银行理财产品智能问答助手 · 招银/工银/中银/浦银/民生 等 22 家机构",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}