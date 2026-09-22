"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Loader2, BookOpen, Sparkles, X } from "lucide-react";
import {
  createSession,
  getSession,
  query,
  streamQuery,
  RetrievedDoc,
  SessionMessage,
} from "@/lib/api";
import { Markdown } from "./Markdown";
import { ThinkingPanel } from "./ThinkingPanel";
import { AgentSteps, AgentStep, AgentStepKind } from "./AgentSteps";
import {
  nodeNameToKind,
  mapAgentTrace,
  mapAgentStep,
  mapAgentReflect,
  mapAgentToolCall,
  finalizeAgentSteps,
} from "@/lib/agentStepMappers";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  retrieved_docs?: RetrievedDoc[];
  streaming?: boolean;
  latency_ms?: number;
  // Phase 6.9: Agent Trace 时间线
  steps?: AgentStep[];
  // Phase 6.9: Self-RAG 判断结果（可选展示）
  selfRag?: { needRetrieval: boolean; confidence: number; reason: string };
}

interface Props {
  game: string;
  useStream: boolean;
  topK: number;
  topN: number;
  sessionId: string | null;
  onSessionCreated?: (sessionId: string) => void;
}

const EXAMPLE_QUERIES = [
  "招银理财 24GS5969 的业绩基准是多少？",
  "工银理财产品说明书怎么查？",
  "中银理财业绩比较基准调整公告",
  "浦银理财新设份额的费率是多少？",
];

export function ChatWindow({ game, useStream, topK, topN, sessionId, onSessionCreated }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");

  // 多会话状态管理：Map<sessionId, {messages, loading, abortController, loaded}>
  // loaded 标志表示是否已经从服务器加载过历史（避免重复加载）
  const sessionsRef = useRef<Map<string, {
    messages: Message[];
    loading: boolean;
    abortController: AbortController | null;
    loaded: boolean;  // 是否已从服务器加载历史
  }>>(new Map());

  // 强制重新渲染
  const [, forceUpdate] = useState({});

  // 获取当前会话的状态
  const getCurrentSession = () => {
    if (!sessionId) return { messages: [], loading: false, abortController: null, loaded: true };

    if (!sessionsRef.current.has(sessionId)) {
      sessionsRef.current.set(sessionId, {
        messages: [],
        loading: false,
        abortController: null,
        loaded: false,
      });
    }
    return sessionsRef.current.get(sessionId)!;
  };

  const currentSession = getCurrentSession();
  const messages = currentSession.messages;
  const loading = currentSession.loading;

  // session 切换时加载历史（首次访问时才加载）
  useEffect(() => {
    if (!sessionId) return;

    const current = sessionsRef.current.get(sessionId);

    // 如果已经加载过历史，不重复加载
    if (current?.loaded) {
      return;
    }

    // 标记为正在加载（避免重复请求）
    if (current) {
      current.loaded = true;
    }

    // 从服务器加载历史
    getSession(sessionId)
      .then((d) => {
        const sessionState = sessionsRef.current.get(sessionId) || {
          messages: [],
          loading: false,
          abortController: null,
          loaded: true,
        };
        sessionState.messages = (d.messages || []).map((m: SessionMessage) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          thinking: m.thinking || undefined,
          retrieved_docs: m.retrieved_docs || undefined,
        }));
        sessionState.loaded = true;
        sessionsRef.current.set(sessionId, sessionState);
        forceUpdate({});
      })
      .catch(() => {
        const sessionState = sessionsRef.current.get(sessionId) || {
          messages: [],
          loading: false,
          abortController: null,
          loaded: true,
        };
        sessionState.loaded = true;
        sessionsRef.current.set(sessionId, sessionState);
        forceUpdate({});
      });
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function handleSubmit(queryText: string) {
    if (!queryText.trim() || loading) return;

    let activeSessionId = sessionId;
    try {
      if (!activeSessionId) {
        const created = await createSession();
        activeSessionId = created.id;
        onSessionCreated?.(created.id);
      }

      // 确保会话存在（新建会话时设置 loaded=true，因为消息已在内存）
      if (!sessionsRef.current.has(activeSessionId)) {
        sessionsRef.current.set(activeSessionId, {
          messages: [],
          loading: false,
          abortController: null,
          loaded: true,  // 新会话无需再加载历史
        });
      }

      const session = sessionsRef.current.get(activeSessionId)!;

      const userMsg: Message = {
        id: `u-${Date.now()}`,
        role: "user",
        content: queryText,
      };
      const assistantId = `a-${Date.now()}`;
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        streaming: useStream,
        retrieved_docs: [],
        steps: [],  // Phase 6.9: Agent Trace 时间线
      };

      // 更新当前会话的 messages 和 loading
      session.messages = [...session.messages, userMsg, assistantMsg];
      session.loading = true;
      forceUpdate({});
      setInput("");

      if (useStream) {
        await handleStream(queryText, assistantId, activeSessionId);
      } else {
        await handleSync(queryText, assistantId, activeSessionId);
      }
      onSessionCreated?.(activeSessionId);
    } catch (err) {
      if (!activeSessionId) return;
      const session = sessionsRef.current.get(activeSessionId);
      if (!session) return;

      const latestAssistant = [...session.messages].reverse().find((m) => m.role === "assistant");
      if (!latestAssistant) return;

      session.messages = session.messages.map((m) =>
        m.id === latestAssistant.id
          ? { ...m, content: `❌ 出错了：${(err as Error).message}`, streaming: false }
          : m
      );
      forceUpdate({});
    } finally {
      if (activeSessionId) {
        const session = sessionsRef.current.get(activeSessionId);
        if (session) {
          session.loading = false;
          forceUpdate({});
        }
      }
    }
  }

  async function handleSync(
    queryText: string,
    assistantId: string,
    activeSessionId: string
  ) {
    const result = await query({
      query: queryText,
      game: game || undefined,
      top_k: topK,
      top_n: topN,
      session_id: activeSessionId,
    });

    const session = sessionsRef.current.get(activeSessionId);
    if (!session) return;

    session.messages = session.messages.map((m) =>
      m.id === assistantId
        ? {
            ...m,
            content: result.answer,
            thinking: result.thinking || undefined,
            retrieved_docs: result.retrieved_docs,
            latency_ms: result.latency_ms,
            streaming: false,
          }
        : m
    );
    forceUpdate({});
  }

  async function handleStream(
    queryText: string,
    assistantId: string,
    activeSessionId: string
  ) {
    let fullAnswer = "";
    let retrievedDocs: RetrievedDoc[] = [];
    let fullThinking = "";

    const session = sessionsRef.current.get(activeSessionId);
    if (!session) return;

    // 为当前会话创建独立的 AbortController
    const controller = new AbortController();
    session.abortController = controller;

    try {
      for await (const event of streamQuery({
        query: queryText,
        game: game || undefined,
        top_k: topK,
        top_n: topN,
        session_id: activeSessionId,
        signal: controller.signal,
      })) {
        const currentSession = sessionsRef.current.get(activeSessionId);
        if (!currentSession) break;

        if (event.event === "thinking") {
          fullThinking += (event.data.delta as string) || "";
          currentSession.messages = currentSession.messages.map((m) =>
            m.id === assistantId ? { ...m, thinking: fullThinking } : m
          );
          forceUpdate({});
        } else if (event.event === "generation") {
          fullAnswer += (event.data.delta as string) || "";
          currentSession.messages = currentSession.messages.map((m) =>
            m.id === assistantId ? { ...m, content: fullAnswer } : m
          );
          forceUpdate({});
        } else if (event.event === "done") {
          retrievedDocs = (event.data.retrieved_docs as RetrievedDoc[]) || [];
          // 把后端返回的 trace_events 合并到 steps（如有）
          const backendTraces = (event.data.trace_events as any[]) || [];
          currentSession.messages = currentSession.messages.map((m) => {
            if (m.id !== assistantId) return m;
            const existingSteps = m.steps || [];
            // 如果后端 trace_events 没合并到前端 steps（说明事件流被忽略），补一下
            if (existingSteps.length === 0 && backendTraces.length > 0) {
              return {
                ...m,
                content: fullAnswer,
                thinking: fullThinking,
                retrieved_docs: retrievedDocs,
                streaming: false,
                steps: backendTraces.map((t: any, idx: number) => ({
                  id: `trace-${idx}`,
                  kind: "router" as AgentStepKind,
                  node: t.node || "unknown",
                  title: "",
                  detail: "",
                  status: "completed" as const,
                  ts: t.ts || Date.now(),
                  payload: t,
                })),
              };
            }
            return {
              ...m,
              content: fullAnswer,
              thinking: fullThinking,
              retrieved_docs: retrievedDocs,
              streaming: false,
            };
          });
          forceUpdate({});
        } else if (event.event === "error") {
          currentSession.messages = currentSession.messages.map((m) =>
            m.id === assistantId
              ? { ...m, content: `❌ ${event.data.error}`, streaming: false }
              : m
          );
          forceUpdate({});
        } else if (event.event === "agent_trace") {
          // Phase 6.9: 节点进入/退出
          appendAgentTrace(currentSession, assistantId, event.data, forceUpdate);
        } else if (event.event === "agent_step") {
          // Phase 6.9: ReAct 单步
          appendAgentStep(currentSession, assistantId, event.data, forceUpdate);
        } else if (event.event === "agent_reflect") {
          // Phase 6.9: Reflexion 评分
          appendAgentReflect(currentSession, assistantId, event.data, forceUpdate);
        } else if (event.event === "agent_tool_call") {
          // Phase 6.9: 工具调用
          appendAgentToolCall(currentSession, assistantId, event.data, forceUpdate);
        } else if (event.event === "agent_done") {
          // Phase 6.9: 所有节点完成 → 把所有 running 标 completed
          finalizeAgentSteps(currentSession, assistantId, forceUpdate);
        }
      }
    } catch (err: any) {
      const currentSession = sessionsRef.current.get(activeSessionId);
      if (!currentSession) return;

      // 如果是 abort，显示已取消
      if (err.name === "AbortError") {
        currentSession.messages = currentSession.messages.map((m) =>
          m.id === assistantId
            ? { ...m, content: fullAnswer || "已取消", streaming: false }
            : m
        );
        forceUpdate({});
      } else {
        throw err; // 重新抛出其他错误
      }
    } finally {
      const currentSession = sessionsRef.current.get(activeSessionId);
      if (currentSession && currentSession.abortController === controller) {
        currentSession.abortController = null;
      }
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}
      </div>

      {/* Examples */}
      {messages.length === 0 && (
        <div className="px-6 pb-2">
          <div className="max-w-3xl mx-auto flex flex-wrap gap-2">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => handleSubmit(q)}
                className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full hover:border-primary-500 hover:text-primary-600 transition"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t bg-white/80 backdrop-blur-sm px-6 py-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(input);
          }}
          className="max-w-3xl mx-auto flex gap-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="问点理财相关的问题吧…比如「招银理财 24GS5969 的业绩基准是多少？」"
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-50"
          />
          {loading && currentSession.abortController && (
            <button
              type="button"
              onClick={() => {
                if (sessionId) {
                  const session = sessionsRef.current.get(sessionId);
                  if (session?.abortController) {
                    session.abortController.abort();
                    session.abortController = null;
                    session.loading = false;
                    forceUpdate({});
                  }
                }
              }}
              className="px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 flex items-center gap-2"
              title="取消当前咨询的请求"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-6">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mb-4 shadow-lg">
        <Sparkles className="w-8 h-8 text-white" />
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        开始咨询吧
      </h2>
      <p className="text-gray-500 max-w-md">
        FinGuide AI 基于 RAG 检索银行理财公告与产品说明书，覆盖 22 家机构、附带引用来源与风险提示。
      </p>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex-shrink-0 flex items-center justify-center text-white text-sm font-semibold">
          F
        </div>
      )}
      <div className={`flex flex-col max-w-2xl ${isUser ? "items-end" : "items-start"}`}>
        {/* Thinking Panel（仅 assistant 显示） */}
        {!isUser && (message.thinking || message.streaming) && (
          <ThinkingPanel
            thinking={message.thinking || ""}
            isStreaming={message.streaming && !message.thinking}
            className="mb-1"
          />
        )}

        {/* Phase 6.9: Agent Steps 时间线（仅 assistant 显示） */}
        {!isUser && message.steps && message.steps.length > 0 && (
          <AgentSteps
            steps={message.steps}
            isStreaming={message.streaming}
            className="mb-1"
          />
        )}

        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-primary-600 text-white"
              : "bg-white border border-gray-200 text-gray-900"
          }`}
        >
          <div className={`prose prose-sm max-w-none ${message.streaming && !message.thinking ? "streaming-cursor" : ""}`}>
            {message.content ? (
              <Markdown
                text={message.content}
                sources={message.retrieved_docs?.map((d) => ({
                  id: d.id,
                  title: d.title,
                  source: d.source,
                  score: d.score,
                }))}
              />
            ) : (
              message.streaming && (
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )
            )}
          </div>
        </div>

        {/* Retrieved Docs */}
        {!isUser && message.retrieved_docs && message.retrieved_docs.length > 0 && (
          <details className="mt-2 text-xs text-gray-500 max-w-2xl">
            <summary className="cursor-pointer hover:text-primary-600 flex items-center gap-1">
              <BookOpen className="w-3 h-3" />
              参考资料（{message.retrieved_docs.length}）
            </summary>
            <div className="mt-2 space-y-2">
              {message.retrieved_docs.map((doc, i) => (
                <div
                  key={doc.id}
                  id={`source-${i + 1}`}
                  className="px-3 py-2 bg-gray-50 rounded-lg border border-gray-100 transition-all"
                >
                  <div className="font-medium text-gray-700">
                    [{i + 1}] {doc.title}
                  </div>
                  <div className="text-gray-500 line-clamp-2">{doc.content}</div>
                  <div className="text-gray-400 text-[10px] mt-1">
                    score: {doc.score.toFixed(3)} · {doc.source.split("/").pop()}
                  </div>
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Latency */}
        {!isUser && message.latency_ms && (
          <div className="mt-1 text-[10px] text-gray-400">
            延迟 {message.latency_ms.toFixed(0)}ms
          </div>
        )}
      </div>
    </div>
  );
}

// ===== Phase 6.9: Agent Trace 事件映射（薄包装，调 lib/agentStepMappers 的纯函数） =====

function pushStep(
  session: { messages: Message[] },
  assistantId: string,
  step: AgentStep,
  forceUpdate: (s: any) => void,
) {
  session.messages = session.messages.map((m) =>
    m.id === assistantId
      ? { ...m, steps: [...(m.steps || []), step] }
      : m
  );
  forceUpdate({});
}

function appendAgentTrace(
  session: { messages: Message[] },
  assistantId: string,
  data: Record<string, unknown>,
  forceUpdate: (s: any) => void,
) {
  pushStep(session, assistantId, mapAgentTrace(data), forceUpdate);
}

function appendAgentStep(
  session: { messages: Message[] },
  assistantId: string,
  data: Record<string, unknown>,
  forceUpdate: (s: any) => void,
) {
  const idx = session.messages.findIndex((m) => m.id === assistantId);
  if (idx === -1) return;
  const msg = session.messages[idx];
  const nextSteps = mapAgentStep(data, msg.steps || []);
  session.messages = session.messages.map((m, i) =>
    i === idx ? { ...m, steps: nextSteps } : m,
  );
  forceUpdate({});
}

function appendAgentReflect(
  session: { messages: Message[] },
  assistantId: string,
  data: Record<string, unknown>,
  forceUpdate: (s: any) => void,
) {
  pushStep(session, assistantId, mapAgentReflect(data), forceUpdate);
}

function appendAgentToolCall(
  session: { messages: Message[] },
  assistantId: string,
  data: Record<string, unknown>,
  forceUpdate: (s: any) => void,
) {
  pushStep(session, assistantId, mapAgentToolCall(data), forceUpdate);
}

function _finalizeAgentSteps(
  session: { messages: Message[] },
  assistantId: string,
  forceUpdate: (s: any) => void,
) {
  session.messages = session.messages.map((m) => {
    if (m.id !== assistantId) return m;
    return { ...m, steps: finalizeAgentSteps(m.steps || []) };
  });
  forceUpdate({});
}

// 保留旧名兼容（handleStream 引用 finalizeAgentSteps）
const finalizeAgentStepsFn = _finalizeAgentSteps;