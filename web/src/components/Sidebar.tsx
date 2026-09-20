"use client";

import { useEffect, useMemo, useState } from "react";
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
  Search,
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

function relativeTime(iso: string | null): string {
  if (!iso) return "";
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diff = Math.max(0, now - then);
  const m = Math.floor(diff / 60000);
  if (m < 1) return "刚刚";
  if (m < 60) return `${m} 分钟前`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} 小时前`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d} 天前`;
  return new Date(then).toLocaleDateString("zh-CN");
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
  const [searchQuery, setSearchQuery] = useState("");

  async function loadSessions() {
    try {
      const list = await listSessions(searchQuery || undefined);
      setSessions(list);
    } catch {
      // ignore
    }
  }

  // 搜索防抖
  useEffect(() => {
    const t = setTimeout(() => loadSessions(), 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, refreshKey]);

  useEffect(() => {
    if (!open) return;
    checkHealth().then(setHealth).catch(() => setHealth(null));
  }, [open]);

  async function handleNewSession() {
    try {
      const session = await createSession();
      setSearchQuery("");
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

  // 按更新时间分组
  const grouped = useMemo(() => {
    const now = Date.now();
    const today: SessionListItem[] = [];
    const week: SessionListItem[] = [];
    const older: SessionListItem[] = [];
    sessions.forEach((s) => {
      const diff = now - new Date(s.updated_at || 0).getTime();
      if (diff < 24 * 3600 * 1000) today.push(s);
      else if (diff < 7 * 24 * 3600 * 1000) week.push(s);
      else older.push(s);
    });
    return { today, week, older };
  }, [sessions]);

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
          label="LLM"
          status={health?.components.llm_api}
          detail={health?.components.llm_api || "未配置"}
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

        {/* 搜索框 */}
        <div className="relative mb-3">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索会话..."
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-3 h-3" />
            </button>
          )}
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
        {sessions.length === 0 ? (
          <div className="text-center text-xs text-gray-400 py-6">
            {searchQuery ? "未找到匹配的会话" : "还没有会话，点击\"新对话\"开始"}
          </div>
        ) : (
          <div className="space-y-3">
            {/* 今天 */}
            {grouped.today.length > 0 && (
              <SessionGroup
                label="今天"
                sessions={grouped.today}
                currentSessionId={currentSessionId}
                editingId={editingId}
                editingTitle={editingTitle}
                setEditingTitle={setEditingTitle}
                onSelectSession={onSelectSession}
                onDelete={handleDelete}
                onEdit={startEdit}
                onSave={handleSaveRename}
                onCancel={cancelEdit}
              />
            )}
            {/* 本周 */}
            {grouped.week.length > 0 && (
              <SessionGroup
                label="本周"
                sessions={grouped.week}
                currentSessionId={currentSessionId}
                editingId={editingId}
                editingTitle={editingTitle}
                setEditingTitle={setEditingTitle}
                onSelectSession={onSelectSession}
                onDelete={handleDelete}
                onEdit={startEdit}
                onSave={handleSaveRename}
                onCancel={cancelEdit}
              />
            )}
            {/* 更早 */}
            {grouped.older.length > 0 && (
              <SessionGroup
                label="更早"
                sessions={grouped.older}
                currentSessionId={currentSessionId}
                editingId={editingId}
                editingTitle={editingTitle}
                setEditingTitle={setEditingTitle}
                onSelectSession={onSelectSession}
                onDelete={handleDelete}
                onEdit={startEdit}
                onSave={handleSaveRename}
                onCancel={cancelEdit}
              />
            )}
          </div>
        )}
      </div>
    </aside>
  );
}

function SessionGroup({
  label,
  sessions,
  ...itemProps
}: {
  label: string;
  sessions: SessionListItem[];
  currentSessionId: string | null;
  editingId: string | null;
  editingTitle: string;
  setEditingTitle: (v: string) => void;
  onSelectSession: (id: string | null) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onEdit: (s: SessionListItem, e: React.MouseEvent) => void;
  onSave: (e: React.MouseEvent) => void;
  onCancel: (e: React.MouseEvent) => void;
}) {
  return (
    <div className="space-y-1">
      <h4 className="text-[10px] font-semibold text-gray-400 uppercase px-1">
        {label}
      </h4>
      {sessions.map((s) => (
        <SessionItem
          key={s.id}
          session={s}
          active={s.id === itemProps.currentSessionId}
          editing={editingId === s.id}
          editTitle={itemProps.editingTitle}
          setEditTitle={itemProps.setEditingTitle}
          onSelect={() => itemProps.onSelectSession(s.id)}
          onDelete={(e) => itemProps.onDelete(s.id, e)}
          onEdit={(e) => itemProps.onEdit(s, e)}
          onSave={(e) => {
            e.stopPropagation();
            itemProps.onSave(s.id);
          }}
          onCancel={itemProps.onCancel}
        />
      ))}
    </div>
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
  const isOk =
    status === "ok" ||
    status === "configured" ||
    status?.startsWith("ollama:") ||
    status?.endsWith(":configured");
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
                title={session.title || "新对话"}
              >
                {session.title || "新对话"}
              </div>
              <div className="text-[10px] text-gray-400 mt-0.5 flex items-center gap-1">
                <span>{session.message_count} 条</span>
                <span>·</span>
                <span>{relativeTime(session.updated_at)}</span>
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
