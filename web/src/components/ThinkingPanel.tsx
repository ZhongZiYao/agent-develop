"use client";

import { useState } from "react";
import { Brain, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  thinking: string;
  isStreaming?: boolean;
  className?: string;
}

/**
 * 思考过程面板 — 默认折叠，点击展开
 *
 * 业界做法（ChatGPT o1 / Claude Extended Thinking / Gemini Thinking）：
 * - 默认折叠 + 灰色背景
 * - Brain 图标标识
 * - ChevronDown 旋转展开
 * - 流式时显示 loading spinner
 */
export function ThinkingPanel({ thinking, isStreaming = false, className }: Props) {
  const [open, setOpen] = useState(false);

  if (!thinking && !isStreaming) return null;

  return (
    <div
      className={cn(
        "mt-2 rounded-lg border border-amber-200 bg-amber-50/50 overflow-hidden",
        className
      )}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left text-xs text-amber-700 hover:bg-amber-100/50 transition"
      >
        {isStreaming && thinking ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" />
        ) : (
          <Brain className="w-3.5 h-3.5 flex-shrink-0" />
        )}
        <span className="font-medium flex-1">
          {isStreaming && !thinking
            ? "思考中..."
            : open
            ? "隐藏思考过程"
            : "显示思考过程"}
        </span>
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-3 py-2 border-t border-amber-200 bg-amber-50 text-xs text-gray-700 leading-relaxed max-h-64 overflow-y-auto whitespace-pre-wrap font-mono">
          {thinking || (
            <span className="text-amber-600 italic">
              {isStreaming ? "正在推理..." : "（空）"}
            </span>
          )}
        </div>
      )}
    </div>
  );
}