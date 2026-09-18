import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GameGuide AI",
  description: "基于 RAG 的游戏攻略问答助手",
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