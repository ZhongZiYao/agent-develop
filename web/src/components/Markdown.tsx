"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { CodeBlock } from "./CodeBlock";
import { Citation, type SourceDoc } from "./Citation";
import { cn } from "@/lib/utils";

import "highlight.js/styles/github-dark.css";

interface Props {
  text: string;
  sources?: SourceDoc[];
  className?: string;
}

/**
 * 统一 Markdown 渲染组件
 *
 * 特性（业界 80% 默认）：
 * - GFM：表格、删除线、任务列表、链接自动识别
 * - 代码高亮：highlight.js（自动检测语言）
 * - 代码 Copy 按钮：hover 出现
 * - 引用 [1] -> 蓝色上标 + tooltip + 点击跳转
 * - 表格响应式：横向滚动
 * - 链接：新窗口打开 + 安全
 */
export function Markdown({ text, sources = [], className }: Props) {
  // 自定义组件映射
  const components: Components = {
    // 代码块（pre）
    pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,

    // 链接
    a: ({ node, ...props }) => (
      <a
        {...props}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary-600 hover:underline"
      />
    ),

    // 表格（响应式）
    table: ({ children }) => (
      <div className="overflow-x-auto my-3 rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
    th: ({ children }) => (
      <th className="px-3 py-2 text-left font-semibold text-gray-700 border-b">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-3 py-2 border-b border-gray-100">{children}</td>
    ),

    // 标题层级
    h1: ({ children }) => (
      <h1 className="text-xl font-bold mt-4 mb-2 text-gray-900">{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-lg font-bold mt-4 mb-2 text-gray-900">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-base font-semibold mt-3 mb-1.5 text-gray-800">{children}</h3>
    ),

    // 列表
    ul: ({ children }) => (
      <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>
    ),
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,

    // 引用
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-primary-500 bg-primary-50 pl-3 py-1 my-2 text-gray-700 italic">
        {children}
      </blockquote>
    ),

    // 行内代码
    code: ({ children, className: cls }) => {
      // 如果是代码块（className 包含 language-xxx），交给 <pre> 处理
      const isBlock = cls?.includes("language-");
      if (isBlock) {
        return <code className={cls}>{children}</code>;
      }
      // 行内代码
      return (
        <code className="px-1.5 py-0.5 rounded bg-gray-100 text-pink-600 text-[0.9em] font-mono">
          {children}
        </code>
      );
    },

    // 段落
    p: ({ children }) => (
      <p className="my-2 leading-relaxed text-gray-800">{children}</p>
    ),

    // 强调
    strong: ({ children }) => (
      <strong className="font-semibold text-gray-900">{children}</strong>
    ),
    em: ({ children }) => <em className="italic">{children}</em>,

    // 分割线
    hr: () => <hr className="my-4 border-gray-200" />,
  };

  return (
    <div className={cn("markdown-body", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {text}
      </ReactMarkdown>

      {/* 渲染 [1] [2] 等引用上标（手动方式） */}
      {sources.length > 0 && <CitationInjector text={text} sources={sources} />}
    </div>
  );
}

/**
 * 引用注入器 — 把字符串中的 [1][2] 转成 <Citation> 组件
 *
 * 简化方案：在 Markdown 渲染后再追加一个独立的"引用列表"
 * 真正的"行内替换 [N]" 需要 AST 操作，复杂度高；这里取折中
 *
 * 实际渲染效果：Markdown 答案下面会有一行 [1][2][3] 引用上标链接
 */
function CitationInjector({ text, sources }: { text: string; sources: SourceDoc[] }) {
  // 从文本中提取所有 [N]
  const citationMatches = Array.from(text.matchAll(/\[(\d+)\]/g));
  const uniqueIndices = Array.from(
    new Set(citationMatches.map((m) => Number(m[1])))
  )
    .filter((n) => n >= 1 && n <= sources.length)
    .sort((a, b) => a - b);

  if (uniqueIndices.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-1">
      <span className="text-xs text-gray-500 mr-2">引用：</span>
      {uniqueIndices.map((idx) => (
        <Citation key={idx} index={idx} source={sources[idx - 1]} />
      ))}
    </div>
  );
}