"use client";

import { useState } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { SettingsPanel } from "@/components/SettingsPanel";
import { Sidebar } from "@/components/Sidebar";
import { Settings, Menu } from "lucide-react";

export default function Home() {
  const [showSettings, setShowSettings] = useState(false);
  const [game, setGame] = useState<string>("");
  const [useStream, setUseStream] = useState(true);
  const [topK, setTopK] = useState(10);
  const [topN, setTopN] = useState(5);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-3 border-b bg-white/60 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                GameGuide AI
              </h1>
              <p className="text-xs text-gray-500">
                基于 RAG 的游戏攻略问答 · Phase 1 MVP
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 hover:bg-gray-100 rounded-lg"
            title="设置"
          >
            <Settings className="w-5 h-5 text-gray-600" />
          </button>
        </header>

        {/* Chat */}
        <ChatWindow
          game={game}
          useStream={useStream}
          topK={topK}
          topN={topN}
        />
      </main>

      {/* Settings Drawer */}
      {showSettings && (
        <SettingsPanel
          onClose={() => setShowSettings(false)}
          game={game}
          setGame={setGame}
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