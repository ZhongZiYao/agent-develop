/** AgentStep 映射辅助函数（从 ChatWindow.tsx 抽出）
 *
 * 这些是纯函数，方便测试和复用。
 * 后端 SSE 事件 → 前端 AgentStep 数据结构的转换。
 */

import { AgentStep, AgentStepKind } from "@/components/AgentSteps";

/** 后端节点名 → 前端 step kind */
export function nodeNameToKind(node: string): AgentStepKind {
  switch (node) {
    case "router":
      return "router";
    case "self_rag_judge":
      return "self_rag";
    case "llm_only_answer":
      return "llm_only";
    case "retrieve":
    case "retrieval":
      return "retrieve";
    case "agentic_rag":
      return "think";
    case "evaluator":
      return "reflect";
    case "replan":
      return "replan";
    default:
      return "router";
  }
}

/** appendAgentTrace 数据转换 */
export function mapAgentTrace(data: Record<string, unknown>): AgentStep {
  const node = (data.node as string) || "unknown";
  const status =
    (data.status as "running" | "completed" | "failed") || "started";
  const ts = (data.ts as number) || Date.now();
  return {
    id: `trace-${ts}-${Math.random().toString(36).slice(2, 6)}`,
    kind: nodeNameToKind(node),
    node,
    title: "",
    detail: "",
    status,
    ts,
    payload: data.payload as Record<string, unknown> | undefined,
  };
}

/** appendAgentStep：同 iteration 时 in-place 更新（避免 step 数量爆炸） */
export function mapAgentStep(
  data: Record<string, unknown>,
  existingSteps: AgentStep[],
): AgentStep[] {
  const iteration = data.iteration as number | undefined;
  const ts = (data.ts as number) || Date.now();

  if (iteration !== undefined) {
    const existingIdx = existingSteps.findIndex(
      (s) =>
        s.iteration === iteration && s.kind === "think" && s.status !== "completed",
    );
    if (existingIdx >= 0) {
      const updated = [...existingSteps];
      updated[existingIdx] = {
        ...updated[existingIdx],
        thoughtPreview:
          (data.thought_preview as string) ||
          updated[existingIdx].thoughtPreview,
        action: (data.action as any) || updated[existingIdx].action,
        observationPreview:
          (data.observation_preview as string) ||
          updated[existingIdx].observationPreview,
        status: "completed",
        ts,
      };
      return updated;
    }
  }

  // 否则 append 新 step
  return [
    ...existingSteps,
    {
      id: `step-${ts}-${Math.random().toString(36).slice(2, 6)}`,
      kind: "think" as AgentStepKind,
      node: "agentic_rag",
      title: "",
      detail: "",
      status: "completed",
      iteration,
      ts,
      thoughtPreview: data.thought_preview as string | undefined,
      action: data.action as any,
      observationPreview: data.observation_preview as string | undefined,
    },
  ];
}

/** appendAgentReflect 数据转换 */
export function mapAgentReflect(data: Record<string, unknown>): AgentStep {
  const ts = (data.ts as number) || Date.now();
  return {
    id: `reflect-${ts}`,
    kind: "reflect",
    node: "evaluator",
    title: `评分 ${data.score}/5${data.need_replan ? " → 触发重新规划" : ""}`,
    detail: (data.reason as string) || "",
    status: "completed",
    ts,
    score: data.score as number,
    needReplan: data.need_replan as boolean,
  };
}

/** appendAgentToolCall 数据转换 */
export function mapAgentToolCall(data: Record<string, unknown>): AgentStep {
  const ts = (data.ts as number) || Date.now();
  return {
    id: `tool-${ts}-${Math.random().toString(36).slice(2, 6)}`,
    kind: "tool_call",
    node: "agentic_rag",
    title: `调用 ${data.tool}`,
    detail: "",
    status: "completed",
    iteration: data.iteration as number | undefined,
    ts,
    action: {
      tool: data.tool as string,
      args: (data.args as Record<string, unknown>) || {},
    },
    observationPreview: data.output_preview as string | undefined,
  };
}

/** finalizeAgentSteps：把所有 running 标为 completed */
export function finalizeAgentSteps(steps: AgentStep[]): AgentStep[] {
  return steps.map((s) =>
    s.status === "running" ? { ...s, status: "completed" as const } : s,
  );
}
