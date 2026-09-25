"use client";

import { useState } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { SettingsPanel } from "@/components/SettingsPanel";
import { Sidebar } from "@/components/Sidebar";
import { Settings, Menu, Landmark, FileText } from "lucide-react";

export default function Home() {
  const [showSettings, setShowSettings] = useState(false);
  const [institution, setInstitution] = useState<string>("");
  const [useStream, setUseStream] = useState(true);
  const [topK, setTopK] = useState(10);
  const [topN, setTopN] = useState(5);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  function handleNewChat() {
    setSessionId(null);
    setRefreshKey((k) => k + 1);
  }

  function handleSelectSession(id: string | null) {
    setSessionId(id);
  }

  function handleSessionActivity(id: string) {
    setSessionId(id);
    setRefreshKey((key) => key + 1);
    // 兼容旧的兜底刷新（chat-graph 同步路径不会推 SSE）
    window.setTimeout(() => setRefreshKey((key) => key + 1), 1500);
  }

  // Phase 8.7.2: 后端 SSE 流式推送新标题，立即刷新侧栏
  function handleSessionRenamed(_id: string, _title: string) {
    setRefreshKey((key) => key + 1);
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        refreshKey={refreshKey}
      />

      {/* Main */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-indigo-100 bg-gradient-to-r from-indigo-50/80 to-white/60 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-indigo-50 rounded-lg"
            >
              <Menu className="w-5 h-5 text-indigo-700" />
            </button>
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-primary-600 rounded-lg shadow-sm">
                <Landmark className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  FinGuide AI
                </h1>
                <p className="text-xs text-gray-500">
                  银行理财产品智能问答 · 招银/工银/中银/浦银/民生 等 22 家机构
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleNewChat}
              className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 shadow-sm flex items-center gap-1.5"
            >
              <FileText className="w-4 h-4" />
              新咨询
            </button>
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 hover:bg-indigo-50 rounded-lg"
              title="设置"
            >
              <Settings className="w-5 h-5 text-indigo-700" />
            </button>
          </div>
        </header>

        {/* Chat */}
        <ChatWindow
          game={institution}
          useStream={useStream}
          topK={topK}
          topN={topN}
          sessionId={sessionId}
          onSessionCreated={handleSessionActivity}
          onSessionRenamed={handleSessionRenamed}
        />
      </main>

      {/* Settings Drawer */}
      {showSettings && (
        <SettingsPanel
          onClose={() => setShowSettings(false)}
          game={institution}
          setGame={setInstitution}
          useStream={useStream}
          setUseStream={setUseStream}
          topK={topK}
          setTopK={setTopK}
          topN={topN}
          setTopN={setTopN}
        />
      )}
    </div>
  );
}