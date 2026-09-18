"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export interface SourceDoc {
  id: string;
  title: string;
  source: string;
  score?: number;
}

interface Props {
  index: number;
  source?: SourceDoc;
}

/**
 * 行内引用上标组件 — 把 [1] 渲染成蓝色可点击的小标签
 * hover 出 tooltip 显示完整标题和来源
 *
 * 业界做法（Perplexity / 文心 / 通义）：
 * - 蓝色背景 + 白色数字
 * - hover 出 tooltip 显示来源标题
 * - 点击跳到底部参考资料卡片
 */
export function Citation({ index, source }: Props) {
  const [open, setOpen] = useState(false);

  const handleClick = () => {
    // 滚动到参考资料区域
    const el = document.getElementById(`source-${index}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-2", "ring-primary-500");
      setTimeout(() => el.classList.remove("ring-2", "ring-primary-500"), 1500);
    }
  };

  return (
    <span className="relative inline-block align-baseline">
      <sup
        onClick={handleClick}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className={cn(
          "ml-0.5 px-1 rounded text-[10px] font-semibold cursor-pointer transition",
          "bg-primary-100 text-primary-700 hover:bg-primary-600 hover:text-white",
          "select-none"
        )}
        title={source?.title || `引用 ${index}`}
      >
        [{index}]
      </sup>

      {open && source && (
        <span
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50",
            "px-3 py-2 text-xs bg-gray-900 text-white rounded-lg shadow-2xl",
            "max-w-xs whitespace-normal text-left",
            "animate-fade-in"
          )}
        >
          <span className="font-semibold block mb-0.5">{source.title}</span>
          <span className="text-gray-300 text-[10px] line-clamp-2">
            {source.source}
          </span>
          {source.score !== undefined && (
            <span className="text-gray-400 text-[10px] block mt-1">
              相似度：{source.score.toFixed(3)}
            </span>
          )}
        </span>
      )}
    </span>
  );
}