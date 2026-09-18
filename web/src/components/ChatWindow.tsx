"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Loader2, BookOpen, Sparkles } from "lucide-react";
import { query, streamQuery, RetrievedDoc } from "@/lib/api";
import { Markdown } from "./Markdown";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  retrieved_docs?: RetrievedDoc[];
  streaming?: boolean;
  latency_ms?: number;
}

interface Props {
  game: string;
  useStream: boolean;
  topK: number;
  topN: number;
}

const EXAMPLE_QUERIES = [
  "妖刀姬 S13 怎么连招？",
  "E-4048 错误码怎么解决？",
  "红蝶怎么玩？",
  "素问在副本里站什么位置？",
];

export function ChatWindow({ game, useStream, topK, topN }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function handleSubmit(queryText: string) {
    if (!queryText.trim() || loading) return;

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
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setLoading(true);

    try {
      if (useStream) {
        await handleStream(queryText, assistantId);
      } else {
        await handleSync(queryText, assistantId);
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `❌ 出错了：${(err as Error).message}`, streaming: false }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleSync(queryText: string, assistantId: string) {
    const result = await query({
      query: queryText,
      game: game || undefined,
      top_k: topK,
      top_n: topN,
    });
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantId
          ? {
              ...m,
              content: result.answer,
              retrieved_docs: result.retrieved_docs,
              latency_ms: result.latency_ms,
              streaming: false,
            }
          : m
      )
    );
  }

  async function handleStream(queryText: string, assistantId: string) {
    let fullAnswer = "";
    let retrievedDocs: RetrievedDoc[] = [];

    for await (const event of streamQuery({
      query: queryText,
      game: game || undefined,
      top_k: topK,
      top_n: topN,
    })) {
      if (event.event === "generation") {
        fullAnswer += (event.data.delta as string) || "";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: fullAnswer } : m
          )
        );
      } else if (event.event === "done") {
        retrievedDocs = (event.data.retrieved_docs as RetrievedDoc[]) || [];
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: fullAnswer,
                  retrieved_docs: retrievedDocs,
                  streaming: false,
                }
              : m
          )
        );
      } else if (event.event === "error") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `❌ ${event.data.error}`, streaming: false }
              : m
          )
        );
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
            placeholder="问点什么吧…比如「妖刀姬 S13 怎么连招？」"
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-50"
          />
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
        开始对话吧
      </h2>
      <p className="text-gray-500 max-w-md">
        GameGuide AI 基于 RAG 检索游戏攻略文档，回答准确、附带引用来源。
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
          G
        </div>
      )}
      <div className={`flex flex-col max-w-2xl ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-primary-600 text-white"
              : "bg-white border border-gray-200 text-gray-900"
          }`}
        >
          <div className={`prose prose-sm max-w-none ${message.streaming ? "streaming-cursor" : ""}`}>
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