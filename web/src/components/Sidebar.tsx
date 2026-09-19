"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Database,
  Cpu,
  Plus,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  checkHealth,
  listSessions,
  createSession,
  deleteSession,
  renameSession,
  type SessionListItem,
  type HealthResponse,
} from "@/lib/api";

interface Props {
  open: boolean;
  onToggle: () => void;
  currentSessionId: string | null;
  onSelectSession: (sessionId: string | null) => void;
  refreshKey?: number; // 触发刷新
}

export function Sidebar({
  open,
  onToggle,
  currentSessionId,
  onSelectSession,
  refreshKey = 0,
}: Props) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  async function loadSessions() {
    try {
      const list = await listSessions();
      setSessions(list);
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    if (!open) return;
    checkHealth().then(setHealth).catch(() => setHealth(null));
  }, [open]);

  useEffect(() => {
    loadSessions();
  }, [refreshKey]);

  async function handleNewSession() {
    try {
      const session = await createSession();
      await loadSessions();
      onSelectSession(session.id);
    } catch {
      // ignore
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("确认删除这个对话吗？")) return;
    await deleteSession(id);
    if (currentSessionId === id) {
      onSelectSession(null);
    }
    await loadSessions();
  }

  async function handleSaveRename(id: string) {
    if (!editingTitle.trim()) return;
    await renameSession(id, editingTitle.trim());
    setEditingId(null);
    await loadSessions();
  }

  function startEdit(session: SessionListItem, e: React.MouseEvent) {
    e.stopPropagation();
    setEditingId(session.id);
    setEditingTitle(session.title);
  }

  function cancelEdit(e: React.MouseEvent) {
    e.stopPropagation();
    setEditingId(null);
  }

  if (!open) return null;

  return (
    <aside className="w-72 border-r bg-white/60 backdrop-blur-sm flex flex-col">
      {/* 系统状态 */}
      <div className="p-4 border-b">
        <h2 className="font-semibold text-gray-900 mb-3">系统状态</h2>
        <StatusCard
          icon={<Database className="w-3.5 h-3.5" />}
          label="向量库"
          status={health?.components.vector_store}
          detail={health ? `${health.vector_count} 条` : "未连接"}
        />
        <StatusCard
          icon={<Cpu className="w-3.5 h-3.5" />}
          label="LLM API"
          status={health?.components.llm_api}
          detail="MiniMax"
        />
        <StatusCard
          icon={<Activity className="w-3.5 h-3.5" />}
          label="Ollama"
          status={health?.components.ollama}
          detail="bge-m3"
        />
      </div>

      {/* Session 列表 */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="flex items-center justify-between mb-2 px-1">
          <h3 className="text-xs font-semibold text-gray-500 uppercase">
            会话 ({sessions.length})
          </h3>
          <button
            onClick={handleNewSession}
            className="p-1 rounded hover:bg-primary-50 text-primary-600"
            title="新建会话"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* 新对话按钮（大） */}
        <button
          onClick={handleNewSession}
          className="w-full mb-3 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center justify-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          新对话
        </button>

        {/* 列表 */}
        <div className="space-y-1">
          {sessions.length === 0 ? (
            <div className="text-center text-xs text-gray-400 py-6">
              还没有会话，点击"新对话"开始
            </div>
          ) : (
            sessions.map((s) => (
              <SessionItem
                key={s.id}
                session={s}
                active={s.id === currentSessionId}
                editing={editingId === s.id}
                editTitle={editingTitle}
                setEditTitle={setEditingTitle}
                onSelect={() => onSelectSession(s.id)}
                onDelete={(e) => handleDelete(s.id, e)}
                onEdit={(e) => startEdit(s, e)}
                onSave={(e) => {
                  e.stopPropagation();
                  handleSaveRename(s.id);
                }}
                onCancel={cancelEdit}
              />
            ))
          )}
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
    <div className="px-2.5 py-1.5 mb-1 bg-white border border-gray-100 rounded-md text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-gray-700">
          {icon}
          <span>{label}</span>
        </div>
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            isOk ? "bg-green-500" : status ? "bg-red-500" : "bg-gray-300"
          )}
        />
      </div>
      <div className="text-gray-400 text-[10px] mt-0.5">{detail}</div>
    </div>
  );
}

function SessionItem({
  session,
  active,
  editing,
  editTitle,
  setEditTitle,
  onSelect,
  onDelete,
  onEdit,
  onSave,
  onCancel,
}: {
  session: SessionListItem;
  active: boolean;
  editing: boolean;
  editTitle: string;
  setEditTitle: (v: string) => void;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onEdit: (e: React.MouseEvent) => void;
  onSave: (e: React.MouseEvent) => void;
  onCancel: (e: React.MouseEvent) => void;
}) {
  return (
    <div
      onClick={editing ? undefined : onSelect}
      className={cn(
        "group relative px-2.5 py-2 rounded-lg cursor-pointer text-sm transition",
        active
          ? "bg-primary-50 border border-primary-200"
          : "hover:bg-gray-50 border border-transparent"
      )}
    >
      <div className="flex items-start gap-2">
        <MessageSquare
          className={cn(
            "w-3.5 h-3.5 mt-0.5 flex-shrink-0",
            active ? "text-primary-600" : "text-gray-400"
          )}
        />
        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") onSave(e as any);
                  if (e.key === "Escape") onCancel(e as any);
                }}
                className="flex-1 px-1 py-0.5 text-xs border rounded"
                autoFocus
              />
              <button onClick={onSave} className="p-0.5 text-green-600">
                <Check className="w-3 h-3" />
              </button>
              <button onClick={onCancel} className="p-0.5 text-gray-400">
                <X className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <>
              <div
                className={cn(
                  "truncate",
                  active ? "font-medium text-gray-900" : "text-gray-700"
                )}
              >
                {session.title || "新对话"}
              </div>
              <div className="text-[10px] text-gray-400 mt-0.5">
                {session.message_count} 条消息
              </div>
            </>
          )}
        </div>
      </div>

      {!editing && (
        <div className="absolute right-1.5 top-1.5 opacity-0 group-hover:opacity-100 flex gap-0.5">
          <button
            onClick={onEdit}
            className="p-1 hover:bg-white rounded text-gray-500"
            title="重命名"
          >
            <Edit2 className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 hover:bg-white rounded text-red-500"
            title="删除"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
}