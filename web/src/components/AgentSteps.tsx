"use client";

import { useState } from "react";
import {
  GitBranch,
  Search,
  MessageSquare,
  Brain,
  Wrench,
  Eye,
  Repeat,
  RotateCcw,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { Markdown } from "./Markdown";

export type AgentStepKind =
  | "router"
  | "self_rag"
  | "llm_only"
  | "retrieve"
  | "think"
  | "tool_call"
  | "observe"
  | "reflect"
  | "replan"
  | "done";

export type AgentStepStatus = "running" | "completed" | "failed";

export interface AgentStep {
  id: string;
  kind: AgentStepKind;
  node: string;
  title: string;
  detail: string;
  status: AgentStepStatus;
  iteration?: number;
  ts: number;
  thoughtPreview?: string;
  action?: { tool: string; args: Record<string, unknown> };
  observationPreview?: string;
  score?: number;
  needReplan?: boolean;
  payload?: Record<string, unknown>;
}

interface Props {
  steps: AgentStep[];
  isStreaming?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

// kind 的图标 + 文案 + 颜色映射
const KIND_META: Record<
  AgentStepKind,
  { icon: typeof GitBranch; label: string; color: string; bg: string; border: string }
> = {
  router: {
    icon: GitBranch,
    label: "路由决策",
    color: "text-slate-700",
    bg: "bg-slate-50",
    border: "border-slate-200",
  },
  self_rag: {
    icon: Search,
    label: "Self-RAG 判断",
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  llm_only: {
    icon: MessageSquare,
    label: "直接回答",
    color: "text-slate-700",
    bg: "bg-slate-50",
    border: "border-slate-200",
  },
  retrieve: {
    icon: Search,
    label: "检索文档",
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  think: {
    icon: Brain,
    label: "思考",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  tool_call: {
    icon: Wrench,
    label: "调用工具",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  observe: {
    icon: Eye,
    label: "观察结果",
    color: "text-slate-700",
    bg: "bg-slate-50",
    border: "border-slate-200",
  },
  reflect: {
    icon: Repeat,
    label: "反思评分",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  replan: {
    icon: RotateCcw,
    label: "重新规划",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  done: {
    icon: CheckCircle,
    label: "完成",
    color: "text-green-700",
    bg: "bg-green-50",
    border: "border-green-200",
  },
};

export function AgentSteps({
  steps,
  isStreaming = false,
  defaultExpanded = true,
  className = "",
}: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (!steps || steps.length === 0) {
    return null;
  }

  const runningCount = steps.filter((s) => s.status === "running").length;
  const completedCount = steps.filter((s) => s.status === "completed").length;

  return (
    <div className={`rounded-lg border border-gray-200 bg-white ${className}`}>
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="w-full px-3 py-2 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-2 text-sm text-gray-700">
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
          )}
          <span className="font-medium">Agent 执行步骤</span>
          <span className="text-xs text-gray-500">({steps.length})</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {runningCount > 0 && (
            <span className="text-amber-600">运行中 {runningCount}</span>
          )}
          {completedCount > 0 && (
            <span className="text-green-600">已完成 {completedCount}</span>
          )}
        </div>
      </button>

      {/* 时间线 */}
      {expanded && (
        <ol className="px-3 pb-3 space-y-2">
          {steps.map((step, idx) => {
            const meta = KIND_META[step.kind] || KIND_META.router;
            const Icon = meta.icon;
            const isLast = idx === steps.length - 1;
            return (
              <li key={step.id} className="flex gap-2.5 relative">
                {/* 图标列 */}
                <div className="flex flex-col items-center pt-0.5">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center border ${meta.bg} ${meta.border}`}
                  >
                    <Icon className={`w-3 h-3 ${meta.color}`} />
                  </div>
                  {!isLast && (
                    <div className="w-px flex-1 bg-gray-200 mt-1 min-h-[12px]" />
                  )}
                </div>

                {/* 内容列 */}
                <div className="flex-1 min-w-0 pb-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium ${meta.color}`}>
                      {meta.label}
                    </span>
                    {step.iteration !== undefined && (
                      <span className="text-[10px] text-gray-400">
                        #{step.iteration}
                      </span>
                    )}
                    <div className="ml-auto">
                      {step.status === "running" ? (
                        <Loader2 className="w-3 h-3 animate-spin text-amber-500" />
                      ) : step.status === "completed" ? (
                        <CheckCircle className="w-3 h-3 text-green-500" />
                      ) : (
                        <span className="text-[10px] text-red-500">失败</span>
                      )}
                    </div>
                  </div>

                  {step.title && (
                    <div className="text-xs text-gray-700 mt-0.5">
                      {step.title}
                    </div>
                  )}

                  {/* 详情：可折叠的 thought / observation */}
                  {(step.thoughtPreview || step.observationPreview || step.detail) && (
                    <details className="mt-1">
                      <summary className="text-[10px] text-gray-500 cursor-pointer hover:text-primary-600 select-none">
                        展开详情
                      </summary>
                      <div className="mt-1 space-y-1">
                        {step.thoughtPreview && (
                          <div className="text-[11px] text-gray-600 bg-amber-50/50 border border-amber-100 rounded px-2 py-1">
                            <div className="text-[9px] font-semibold text-amber-700 mb-0.5">
                              💭 思考
                            </div>
                            <Markdown text={step.thoughtPreview} />
                          </div>
                        )}
                        {step.action && (
                          <div className="text-[11px] text-gray-600 bg-slate-50 border border-slate-200 rounded px-2 py-1">
                            <div className="text-[9px] font-semibold text-slate-700 mb-0.5">
                              🛠 工具
                            </div>
                            <div>
                              <span className="font-mono">{step.action.tool}</span>
                              <span className="text-gray-500">
                                ({JSON.stringify(step.action.args)})
                              </span>
                            </div>
                          </div>
                        )}
                        {step.observationPreview && (
                          <div className="text-[11px] text-gray-600 bg-slate-50 border border-slate-200 rounded px-2 py-1">
                            <div className="text-[9px] font-semibold text-slate-700 mb-0.5">
                              👁 结果
                            </div>
                            <div className="line-clamp-4">{step.observationPreview}</div>
                          </div>
                        )}
                        {step.score !== undefined && (
                          <div className="text-[11px] text-gray-600">
                            评分：<span className="font-mono font-semibold">
                              {step.score.toFixed(1)}/5
                            </span>
                            {step.needReplan && (
                              <span className="ml-2 text-amber-600">→ 触发重新规划</span>
                            )}
                          </div>
                        )}
                        {step.detail && !step.thoughtPreview && (
                          <div className="text-[11px] text-gray-500">{step.detail}</div>
                        )}
                      </div>
                    </details>
                  )}
                </div>
              </li>
            );
          })}

          {/* 流式 placeholder */}
          {isStreaming && (
            <li className="flex items-center gap-2 pl-8 text-xs text-gray-400">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>Agent 执行中...</span>
            </li>
          )}
        </ol>
      )}
    </div>
  );
}