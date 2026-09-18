"use client";

import { useEffect, useState } from "react";
import { checkHealth, type HealthResponse } from "@/lib/api";
import { Activity, Database, Cpu } from "lucide-react";

interface Props {
  open: boolean;
  onToggle: () => void;
}

export function Sidebar({ open, onToggle }: Props) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    if (!open) return;
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [open]);

  if (!open) return null;

  return (
    <aside className="w-72 border-r bg-white/60 backdrop-blur-sm flex flex-col">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-gray-900">系统状态</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <StatusCard
          icon={<Database className="w-4 h-4" />}
          label="向量库"
          status={health?.components.vector_store}
          detail={health ? `${health.vector_count} 条记录` : "未连接"}
        />
        <StatusCard
          icon={<Cpu className="w-4 h-4" />}
          label="LLM API"
          status={health?.components.llm_api}
          detail="MiniMax"
        />
        <StatusCard
          icon={<Activity className="w-4 h-4" />}
          label="Ollama"
          status={health?.components.ollama}
          detail="bge-m3"
        />

        <div className="pt-4 border-t mt-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            关于
          </h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            这是 GameGuide AI 的 Phase 1 MVP。 基于 LangChain + LangGraph + Ollama 构建。
          </p>
        </div>
      </div>
    </aside>
  );
}

function StatusCard({
  icon,
  label,
  status,
  detail,
}: {
  icon: React.ReactNode;
  label: string;
  status?: string;
  detail: string;
}) {
  const isOk = status === "ok" || status === "configured";
  return (
    <div className="px-3 py-2 bg-white border border-gray-100 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-700">
          {icon}
          <span className="text-sm">{label}</span>
        </div>
        <span
          className={`w-2 h-2 rounded-full ${
            isOk ? "bg-green-500" : status ? "bg-red-500" : "bg-gray-300"
          }`}
        />
      </div>
      <div className="text-xs text-gray-400 mt-1">{detail}</div>
    </div>
  );
}