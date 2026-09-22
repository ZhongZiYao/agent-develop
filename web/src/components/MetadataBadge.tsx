"use client";

/**
 * MetadataBadge — 银行理财文档元数据标签
 *
 * 把后端 Chroma metadata 字段（institution / report_type / effective_date /
 * product_code / product_name）渲染成彩色标签。
 *
 * 设计要点：
 * - 颜色按字段分桶：机构/类型/日期/编号/产品 → 不同颜色便于扫读
 * - 缺失字段不渲染（避免空 badge）
 * - 体积小（text-[10px]），可内联在参考资料卡片标题下
 */

import { Landmark, FileText, Calendar, Hash, Tag } from "lucide-react";

interface Props {
  metadata?: Record<string, unknown> | null;
  className?: string;
}

interface BadgeItem {
  icon: React.ReactNode;
  label: string;
  tone: "blue" | "amber" | "green" | "slate" | "indigo";
}

const TONE_CLASSES: Record<BadgeItem["tone"], string> = {
  blue: "bg-blue-50 text-blue-700 border-blue-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  green: "bg-green-50 text-green-700 border-green-200",
  slate: "bg-slate-50 text-slate-700 border-slate-200",
  indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
};

function buildBadges(metadata?: Record<string, unknown> | null): BadgeItem[] {
  if (!metadata) return [];
  const items: BadgeItem[] = [];

  // 1. 机构（最高优先级）
  const institution = strOrEmpty(metadata.institution);
  if (institution) {
    items.push({
      icon: <Landmark className="w-2.5 h-2.5" />,
      label: institution,
      tone: "indigo",
    });
  }

  // 2. 报告类型
  const reportType = strOrEmpty(metadata.report_type);
  if (reportType) {
    items.push({
      icon: <FileText className="w-2.5 h-2.5" />,
      label: reportType,
      tone: "blue",
    });
  }

  // 3. 生效日期
  const effectiveDate = strOrEmpty(metadata.effective_date);
  if (effectiveDate) {
    items.push({
      icon: <Calendar className="w-2.5 h-2.5" />,
      label: effectiveDate,
      tone: "amber",
    });
  }

  // 4. 产品编号（理财登记系统编码）
  const productCode = strOrEmpty(metadata.product_code);
  if (productCode) {
    items.push({
      icon: <Hash className="w-2.5 h-2.5" />,
      label: productCode,
      tone: "slate",
    });
  }

  // 5. 产品名（如果与 title 不同才显示）
  const productName = strOrEmpty(metadata.product_name);
  const title = strOrEmpty(metadata.title);
  if (productName && productName !== title) {
    items.push({
      icon: <Tag className="w-2.5 h-2.5" />,
      label: productName,
      tone: "green",
    });
  }

  return items;
}

function strOrEmpty(v: unknown): string {
  if (typeof v !== "string") return "";
  return v.trim();
}

export function MetadataBadge({ metadata, className = "" }: Props) {
  const badges = buildBadges(metadata);
  if (badges.length === 0) return null;

  return (
    <div className={`flex flex-wrap items-center gap-1 mt-1 ${className}`}>
      {badges.map((b, idx) => (
        <span
          key={idx}
          className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] rounded border ${TONE_CLASSES[b.tone]}`}
        >
          {b.icon}
          <span className="leading-none">{b.label}</span>
        </span>
      ))}
    </div>
  );
}
