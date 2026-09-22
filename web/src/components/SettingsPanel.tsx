"use client";

import { X, Database, Zap } from "lucide-react";
import { useState } from "react";
import { buildIndex, getIndexStatus } from "@/lib/api";

interface Props {
  onClose: () => void;
  game: string;
  setGame: (v: string) => void;
  useStream: boolean;
  setUseStream: (v: boolean) => void;
  topK: number;
  setTopK: (v: number) => void;
  topN: number;
  setTopN: (v: number) => void;
}

const INSTITUTIONS = [
  "",
  "A01工银理财",
  "A03中银理财",
  "A05交银理财",
  "B01招银理财",
  "B03中信理财",
  "B05浦银理财",
  "B07民生理财",
  "B09广银理财",
];

export function SettingsPanel({
  onClose,
  game,
  setGame,
  useStream,
  setUseStream,
  topK,
  setTopK,
  topN,
  setTopN,
}: Props) {
  const [indexStatus, setIndexStatus] = useState<string>("");
  const [indexInfo, setIndexInfo] = useState<string>("");

  async function handleBuildIndex(force: boolean) {
    setIndexStatus("running");
    setIndexInfo("提交任务...");
    try {
      const job = await buildIndex({ force_rebuild: force });
      setIndexInfo(`Job ${job.job_id} 已创建`);

      // 轮询状态
      const interval = setInterval(async () => {
        try {
          const status = await getIndexStatus(job.job_id);
          setIndexInfo(
            `${status.status} | 文档: ${status.total_docs} | chunks: ${status.total_chunks}`
          );
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(interval);
            setIndexStatus(status.status);
          }
        } catch {
          clearInterval(interval);
          setIndexStatus("failed");
        }
      }, 1500);
    } catch (err) {
      setIndexStatus("failed");
      setIndexInfo((err as Error).message);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex justify-end z-50">
      <div className="w-96 bg-white h-full shadow-2xl overflow-y-auto animate-slide-up">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold">设置</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-6">
          {/* Institution Filter */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              机构过滤
            </label>
            <select
              value={game}
              onChange={(e) => setGame(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {INSTITUTIONS.map((g) => (
                <option key={g} value={g}>
                  {g || "全部"}
                </option>
              ))}
            </select>
          </div>

          {/* Retrieval params */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-700">检索参数</h3>
            <div>
              <label className="text-xs text-gray-500 flex justify-between">
                <span>Top K (召回)</span>
                <span>{topK}</span>
              </label>
              <input
                type="range"
                min={1}
                max={50}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 flex justify-between">
                <span>Top N (生成)</span>
                <span>{topN}</span>
              </label>
              <input
                type="range"
                min={1}
                max={20}
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          {/* Stream */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <span className="text-sm text-gray-700">流式响应</span>
            </div>
            <button
              onClick={() => setUseStream(!useStream)}
              className={`relative w-10 h-5 rounded-full ${
                useStream ? "bg-primary-600" : "bg-gray-300"
              }`}
            >
              <span
                className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition ${
                  useStream ? "left-5" : "left-0.5"
                }`}
              />
            </button>
          </div>

          {/* Index */}
          <div className="pt-4 border-t">
            <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <Database className="w-4 h-4" />
              索引管理
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => handleBuildIndex(false)}
                disabled={indexStatus === "running"}
                className="flex-1 px-3 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50"
              >
                增量构建
              </button>
              <button
                onClick={() => handleBuildIndex(true)}
                disabled={indexStatus === "running"}
                className="flex-1 px-3 py-2 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700 disabled:opacity-50"
              >
                强制重建
              </button>
            </div>
            {indexInfo && (
              <div className="mt-2 text-xs text-gray-500 break-all">
                {indexInfo}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}