"use client";

import { useState, type ReactNode } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  children?: ReactNode;
  className?: string;
}

/**
 * 代码块组件 — 带 Copy 按钮
 *
 * react-markdown 9.x 把 ```lang ... ``` 解析成 <pre><code class="language-lang">...</code></pre>
 * 我们在外层 <pre> 上加 Copy 按钮（点击复制内部 text）
 *
 * 业界做法（ChatGPT / Claude / Copilot）：
 * - 右上角 Copy 按钮，hover 显示
 * - 复制成功后短暂变成 ✓
 * - 代码块圆角 + 等宽字体
 */
export function CodeBlock({ children, className }: Props) {
  const [copied, setCopied] = useState(false);

  // 从 children 提取文本内容
  const extractText = (node: any): string => {
    if (typeof node === "string") return node;
    if (node?.props?.children) {
      if (Array.isArray(node.props.children)) {
        return node.props.children.map(extractText).join("");
      }
      return extractText(node.props.children);
    }
    return "";
  };

  const text = extractText(children);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // 兜底
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className="relative group my-3 rounded-lg overflow-hidden bg-gray-900">
      <button
        onClick={handleCopy}
        className={cn(
          "absolute top-2 right-2 p-1.5 rounded-md",
          "bg-gray-700 hover:bg-gray-600 text-white",
          "opacity-0 group-hover:opacity-100 transition",
          "flex items-center gap-1 text-xs"
        )}
        aria-label="复制代码"
      >
        {copied ? (
          <>
            <Check className="w-3 h-3" /> 已复制
          </>
        ) : (
          <>
            <Copy className="w-3 h-3" /> 复制
          </>
        )}
      </button>

      <pre className={cn("!my-0 p-4 text-sm overflow-x-auto text-gray-100", className)}>
        {children}
      </pre>
    </div>
  );
}